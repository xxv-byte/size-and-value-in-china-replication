# 运行指南（依赖关系与执行顺序）

本文件说明：每个 Notebook 依赖谁、需要什么工作目录、会不会重复跑全量数据、
以及**按什么顺序运行**才不会缺变量。所有结论都来自对 `%run` 语句与内联代码的实际检查。

---

## 0. 三条硬规则

1. **内核工作目录 = Notebook 所在目录**。Jupyter 默认如此；`%run config_0.ipynb` 这种相对路径
   只有在 `src_jup/` 或 `CH3_jup/` 目录下启动内核才成立。
2. **`%run` 是"执行并共享变量"**，不是 import。它会把上游 Notebook 的**所有代码单元**
   都跑一遍（包括读数据与画图）。
3. **C 线不是独立实现**。它通过两种方式借用 B 线的函数：
   `%run -i features_3.ipynb`（把流水线开关关掉，只取函数定义）与
   `load_source_function`（用 ast 从 Notebook JSON 里抽取单个函数源码）。

---

## 1. B 线（src_jup）的运行关系

| Notebook | `%run` 的上游数 | 自身是否读数据 | 能否单独运行 | 说明 |
|---|---|---|---|---|
| `config_0.ipynb` | 0 | 否 | 是 | 纯常量 + 路径发现 |
| `data_io_1.ipynb` | 1 | 否（只定义函数） | 是 | 定义 4 个 read_* |
| `clean_and_universe_2.ipynb` | 2 | 否 | 是 | 定义清洗、股票池、年度事件函数 |
| `features_3.ipynb` | 3 | **是**（末尾有演示流水线） | 是 | 演示段由 `run_features_pipeline` 控制 |
| `monthly_4.ipynb` | 4 | **是**（跑一遍全流程） | 是 | 产出 `monthly_final` |
| `portfolio_5.ipynb` | 5 | **是，且 3 遍** | 是 | 3 个分组函数各自带一段内联流水线 |
| `time_series_regression_6.ipynb` | 5 | **是** | 是 | **不直接** %run features_3，靠 monthly 间接带入 |
| `cross_section_regression_7.ipynb` | 7 | **是** | 是 | 产出 `E_R / E_F`（单次截面，≠ Fama–MacBeth） |
| `fama_macbeth_8.ipynb` | 7 | **是** | 是 | 末尾调用 `fama_macbeth(R, B)` |

### 1.1 %run 累积链

```
config_0 → data_io_1 → clean_and_universe_2 → features_3 → monthly_4 → portfolio_5
        → time_series_regression_6 → { cross_section_regression_7 , fama_macbeth_8 }
```

每个下游 Notebook 的第一个单元都把**左起全部上游**再跑一遍。因此：

- **运行"最后一个"就等于跑完整条链**，但也会把数据读取与特征计算重复 N 遍。
- 这是原始工程的设计，仓库**没有**改成缓存或抽取公共模块——那会改变执行语义，
  也就无法保证结果与历史运行一致。

### 1.2 依赖的是"全局变量"，不是函数返回值

`time_series_regression_6` / `cross_section_regression_7` / `fama_macbeth_8` 末尾的内联段
会自己重新算一遍 `df → monthly → monthly_final → F → R → B`，然后在各自命名空间里留下
`R、B、E_R、E_F、lambda_bar、t_stat` 等变量。**它们依赖同一个内核里前面留下的变量**，
所以不能用"只跑某一个 cell"的方式跳过上游。

### 1.3 变量名冲突（真实存在，未修改）

`fama_macbeth` 的返回值里第一个是"每期溢价矩阵"，调用处写成
`F, Alpha, lambda_bar, t_stat = fama_macbeth(R, B)`，于是 **`F` 从"因子收益矩阵"被覆盖成
"溢价矩阵"**。如果下游还要用因子收益，请在调用前另存
（`scripts/run_sample_pipeline.py` 就是这么做的）。这是原始代码的行为，仓库保留未改。

---

## 2. C 线（CH3_jup）的运行关系

### 2.1 总入口

```
CH_3_factors.ipynb            ← ★ 主入口，按顺序 %run 下面四步
├── 00_paper_targets.ipynb              论文 Table 1–10 / A1–A5 原值（不参与计算）
├── 01_data_and_factors.ipynb           for 循环 %run reproduction_pipeline/00 → 10
├── ../src_jup/CH3_核心解释实验.ipynb    主线实证（因子溢价 / 异象解释 / alpha）
└── ../src_jup/CH3_补充定价检验.ipynb    EP 赛马 / GRS / CH-4
```

### 2.2 11 步数据管道

| 步 | 文件 | 需要什么 | 产出 |
|---|---|---|---|
| 00 | `00_ch3_config.ipynb` | 定位 root；`os.chdir` 到 `src_jup` 后 `%run -i features_3.ipynb` | CH3 字段名、`start_date='1999-01-01'` |
| 01 | `01_read_local_data.ipynb` | 日表 + 月表 + CF/BS/FAS | `df, monthly, cf_df, bs_df, fas_df` |
| 02 | `02_clean_local_tables.ipynb` | 上一步的表 | 清洗后的日表与月表（A 股前缀 00/30/60） |
| 03 | `03_formation_snapshot_and_universe.ipynb` | 清洗后的日表 | 月末快照 `snap` + 流动性/交易资格过滤 |
| 04 | `04_value_signals_and_am.ipynb` | snap + 月表 | EP/BM/ROE 月表优先、日表回退；AM 事件 |
| 05 | `05_construct_characteristics.ipynb` | 日表 + 三张财报表 | 15 个日频特征 + 月度快照 |
| 06 | `06_monthly_panel.ipynb` | snap + monthly | `monthly_all` → `monthly_final`（剔除最小 30%） |
| 07 | `07_factor_returns.ipynb` | monthly_final | `f_ch3 / f_ff3 / f_ch4 / f_ff5` |
| 08 | `08_anomaly_returns.ipynb` | monthly_final | `anomaly_uncon / anomaly_neutral` |
| 09 | `09_daily_reversal.ipynb` | 日表 + monthly_final | 日频反转多空 |
| 10 | `10_data_limitations.ipynb` | — | 口径限制登记表 |

### 2.3 B↔C 的耦合点（不能随便挪文件）

| 耦合 | 位置 | 如果挪动会怎样 |
|---|---|---|
| `%run -i features_3.ipynb` | `00_ch3_config.ipynb` | 找不到文件 → C 线全部特征函数缺失 |
| `load_source_function` 读 `time_series_regression_6.ipynb` | `CH3_核心解释实验.ipynb` | ast 抽取失败 → 时间序列回归不可用 |
| `Path.cwd()` 向上找 `data/raw` | 多个 C 线 Notebook | 找不到根目录 → 读不到数据 |
| `project_root/jupter_notebook_version/src_jup` | 同上 | 目录名被改 → 路径失效 |

> **因此本仓库保留了原目录名 `jupter_notebook_version`（含原拼写）**，只改了路径发现方式。

### 2.4 必须先跑完主线才能运行的专题

| 文件 | 前置 | 说明 |
|---|---|---|
| `03_extended_analysis.ipynb` | 主线（01 管道 + 核心解释） | 缺输入时只输出"覆盖缺口"，不伪造结果 |
| `04_behavior_checks.ipynb` | 主线 | 用小型人工面板做行为校验，不读大表 |
| `05_author_data_validation.ipynb` | 无（自带快照） | 作者公开因子的校准参照 |
| `06_reproduction_report.ipynb` | 主线 | 汇总覆盖率与差异 |
| `07_bayesian_comparison.ipynb` | 主线（需要 `f_ch3, f_ff3`） | 解析贝叶斯比较 |
| `08_additional_conclusions.ipynb` | 主线 | 补充结论 |

> 原学习文档提到的 `CH3_jup/02_tables_and_tests.ipynb` **在本仓库中不存在**；
> 对应的补充检验已合并进 `src_jup/CH3_补充定价检验.ipynb`。

---

## 3. 推荐执行顺序

### 3.1 Full Mode（真实数据）

```
# 0) 先检查数据
python scripts/check_data_layout.py --deep

# 1) 打开 Jupyter，进入 jupter_notebook_version/CH3_jup 目录
jupyter lab

# 2) 主入口，全部运行： CH_3_factors.ipynb
# 3) 主线跑完后，按需运行专题：
#    03_extended_analysis / 04_behavior_checks / 06_reproduction_report
#    07_bayesian_comparison / 08_additional_conclusions
```

> 若只想看通用因子工作流（B 线），进入 `src_jup` 目录并运行
> `fama_macbeth_8.ipynb`（它会自动 %run 上游 7 个）。

### 3.2 单步调试顺序（B 线）

1. `config_0.ipynb`
2. `data_io_1.ipynb`
3. `clean_and_universe_2.ipynb`
4. `features_3.ipynb`
5. `monthly_4.ipynb`（产出 `monthly_final`）
6. `portfolio_5.ipynb`（产出 `F`、`F_ch3`）
7. `time_series_regression_6.ipynb`（产出 `R、B`）
8. `cross_section_regression_7.ipynb` 或 `fama_macbeth_8.ipynb`

### 3.3 Sample Mode（合成数据，无需 RESSET）

```
python scripts/check_data_layout.py --data-dir data/sample
python scripts/run_sample_pipeline.py
python -m unittest discover -s tests -v
```

`run_sample_pipeline.py` 会按 1.1 的顺序执行 9 个 Notebook 的全部代码单元（跳过 %run 行），
并打印 S2–S9 各表形状、CH-3 因子月均收益、Fama–MacBeth 平均溢价与 NW t 值。

---

## 4. 环境变量

| 变量 | 作用 | 默认 |
|---|---|---|
| `RESSET_PROJECT_ROOT` | 项目根目录（含 data/raw 的目录） | 自 `Path.cwd()` 向上查找 |
| `RESSET_DATA_DIR` | 数据根目录（其下必须有 `raw/`） | `<root>/data` |

样例模式就是靠第二个变量指向 `data/sample` 实现的：

```
# Windows PowerShell
$env:RESSET_DATA_DIR = "$PWD\data\sample"
# macOS / Linux
export RESSET_DATA_DIR=$PWD/data/sample
```

---

## 5. 性能与内存提示

- 日表全样本约 1,800 万行（本机实测 18,217,775 行）；`read_daily_data()` 会把样本期内所有日表读进内存。
- 一次完整 B 线运行里，数据读取与特征计算会被重复执行多次（见 1.1），这是耗时的主要来源。
- 若内存吃紧：先把样本期改短（`config_0.ipynb` 的 `start_date/final_date`）做冒烟测试，
  再用全样本运行；不要靠删列或抽行来"优化"，那会改变结果。
- 换手率（250 日）与动量（11 个月）需要足够长的历史，缩短样本期会让前期因子整列为空。

---

## 6. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| FileNotFoundError: config_0.ipynb | 内核工作目录不在 Notebook 所在目录 | 在对应目录下启动 Jupyter |
| RuntimeError: 未找到项目根目录 | 仓库没有放在含 data/raw 的目录下，或该目录为空 | 建好 data/raw（仓库已带占位文件），或设 RESSET_PROJECT_ROOT |
| KeyError: 'monthly_mom' | 内联流水线漏了 get_momentum | 发布副本已修复（见 CHANGES.md）；旧副本请补一行 |
| 跑完没看到结果 | fama_macbeth_8.ipynb 的调用在同一个 cell 末尾，需整 cell 运行 | 整段运行该 cell |
| C 线报 KeyError: 'ClPr' | 月表列名被改成 Clpr | 保持 RESSET 原列名 |
