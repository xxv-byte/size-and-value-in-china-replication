# Size and Value in China — 中国 A 股三因子模型复现

> 复现对象：**Liu, Jianan, Robert F. Stambaugh, and Yu Yuan (2019). "Size and Value in China."**
> *Journal of Financial Economics*, 134(1), 48–69. [doi:10.1016/j.jfineco.2019.03.004](https://doi.org/10.1016/j.jfineco.2019.03.004)

本仓库把一次实证资产定价科研训练的**完整处理流程**整理成可运行、可核查的形式：
从 RESSET 原始日频行情与财务报表出发，构造中国 A 股的市场（MKT）、规模（SMB）与价值（VMG）
三因子，再到时间序列 alpha 检验、Fama–MacBeth 特征回归、异象解释与模型比较。

**本仓库不包含任何 RESSET 原始数据，也不包含论文 PDF。** 数据需使用者自行下载（见
[数据准备指南](docs/DATA_DOWNLOAD_GUIDE.md)），仓库只附带一套**合成样例数据**用于跑通代码。

---

## 目录

| 主题 | 去哪里看 |
|---|---|
| 数据怎么来、怎么命名、放哪里 | [docs/DATA_DOWNLOAD_GUIDE.md](docs/DATA_DOWNLOAD_GUIDE.md) |
| 每张表的字段、单位、时间口径 | [docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md) |
| 怎么运行、Notebook 的调用关系 | [docs/RUNNING_GUIDE.md](docs/RUNNING_GUIDE.md) |
| 哪些做完了、哪些是代理变量、哪些没做 | [docs/REPRODUCTION_STATUS.md](docs/REPRODUCTION_STATUS.md) |
| 发布副本相对原工程的改动 | [docs/CHANGES.md](docs/CHANGES.md) |
| 代码线全景图与数据流 | [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md) |

---

## 1. 项目简介

论文的核心结论是：中国 A 股的定价模型应当用 **EP（盈利市值比）** 而不是 BM 来构造价值因子，
并且必须先剔除市值最小的 30% 股票（壳污染），才能得到干净的规模与价值溢价。复现目标有三层：

1. 把"日频原始表 → 月度错期面板 → 组合排序 → 因子收益 → 三步回归"的通用流水线跑通；
2. 按论文口径构造 **CH-3（MKT / SMB / VMG）** 与 **CH-4（加入换手因子）**；
3. 用时间序列 alpha、GRS、Fama–MacBeth 与贝叶斯比较，检验 CH-3 对中国十项已报道异象的解释力。

## 2. 主要研究内容

- **规模效应与壳价值**：剔除市值最小 30% 的做法、30% 截断的敏感性、壳价值的量级讨论。
- **价值效应与估值指标赛马**：EP / BM / AM / CP 四个估值指标的横截面解释力对比。
- **CH-3 因子构造**：市值中位数 × EP 30/70 分位的独立 2×3 双重排序、六组合市值加权、
  SMB 与 VMG 的合成公式。
- **资产定价检验**：单资产与组合的时间序列回归（HC1 稳健标准误）、alpha 联合检验（GRS）、
  Fama–MacBeth 两步回归（Newey–West 修正）。
- **模型比较**：CH-3 与 FF-3、CH-4、FF-5 代理的互相定价能力，以及解析贝叶斯比较（Barillas–Shanken）。
- **异象解释**：十项已报道异象在 CAPM 与 CH-3 下的平均 |alpha|、平均 R² 与显著性变化。

## 3. 项目结构

```text
size-and-value-in-china-replication/
├── README.md
├── requirements.txt
├── .gitignore
│
├── jupter_notebook_version/          ← 保留原工程目录名，避免破坏 %run 相对路径
│   ├── src_jup/                      ← B 线：通用因子投资主工作流（9 步 + 2 个 CH-3 实验）
│   │   ├── config_0.ipynb            字段常量、文件匹配规则、样本期、路径发现
│   │   ├── data_io_1.ipynb           读日表 / 资产负债表 / 现金流量表 / 固定资产表
│   │   ├── clean_and_universe_2.ipynb 清洗、股票池、三张表清洗、年度事件表与 point-in-time 对齐
│   │   ├── features_3.ipynb          15 个日频特征（市值/动量/BM/EP/CP/波动率/换手/应计/NOA…）
│   │   ├── monthly_4.ipynb           月收益复利、形成月快照、错期月度面板（S3/S4/S5）
│   │   ├── portfolio_5.ipynb         单变量十分位、5×5 规模中性、CH-3 的 2×3 市值加权
│   │   ├── time_series_regression_6.ipynb  收益矩阵 R、逐股 OLS 求暴露 B
│   │   ├── cross_section_regression_7.ipynb 单次截面回归（E_R 对 B.T）
│   │   ├── fama_macbeth_8.ipynb      Fama–MacBeth 两步 + Newey–West(4)
│   │   ├── CH3_核心解释实验.ipynb      CH-3 主线实证（需先跑 C 线数据管道）
│   │   └── CH3_补充定价检验.ipynb      EP 赛马 / GRS / CH-4 补充检验
│   └── CH3_jup/                      ← C 线：论文复现主体
│       ├── CH_3_factors.ipynb        ★ C 线总入口（依次 %run 下面四步）
│       ├── 00_paper_targets.ipynb    论文 Table 1–10 / A1–A5 原值参照（只对照，不参与计算）
│       ├── 01_data_and_factors.ipynb 数据管道调度器（%run reproduction_pipeline 00→10）
│       ├── 03_extended_analysis.ipynb 盈余公告 / 借壳 / 壳价值扩展检验
│       ├── 04_behavior_checks.ipynb  11 项行为校验（错期、权重、GRS 单位不变性…）
│       ├── 05_author_data_validation.ipynb 作者公开因子快照，仅作校准参照
│       ├── 06_reproduction_report.ipynb     复现报告：算了什么、还缺什么
│       ├── 07_bayesian_comparison.ipynb     Barillas–Shanken 解析贝叶斯比较
│       ├── 08_additional_conclusions.ipynb  补充结论（盈余公告后半段、负 EP 稳健性等）
│       └── reproduction_pipeline/    11 步 CH-3 专用数据管道
│
├── data/
│   ├── sample/                       ← 合成样例（可公开，用于 Sample Mode）
│   └── raw/                          ← 使用者自行放入 RESSET 数据（被 .gitignore 排除）
│
├── scripts/
│   ├── check_data_layout.py          运行前数据检查（PASS / WARN / FAIL）
│   ├── run_sample_pipeline.py        Sample Mode：用合成数据跑通 B 线主流水线
│   └── make_sample_data.py           重新生成合成样例数据
│
├── tests/                            25 项静态检查 + 行为测试
├── results/                          已计算结果摘要（含来源与验证状态说明）
└── docs/                             数据、运行、复现状态、改动记录
```

两条代码线的关系（详见 [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md)）：

- **B 线（src_jup）** 是通用因子投资流水线：任何因子/异象都能套用它的 S0→S9 表状态流转。
- **C 线（CH3_jup）** 是论文复现：它**不复制** B 线的代码，而是用
  `%run -i features_3.ipynb`（关掉流水线开关）与 `load_source_function`（ast 抽取函数）
  借用 B 线的特征函数与时间序列回归实现。

## 4. 数据准备

**仓库不附带 RESSET 原始数据。** 数据量约 12 GB，且再分发权限需由数据供应商授权，
因此只提供：

1. **[docs/DATA_DOWNLOAD_GUIDE.md](docs/DATA_DOWNLOAD_GUIDE.md)** —— 下载哪几张表、
   导成什么文件名、放在哪个目录、每张表的字段与单位、以及常见错误。
2. **[docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md)** —— 逐字段的口径说明（含已核实的真实列名）。
3. **data/sample/** —— 40 只股票、24 个月的**合成**数据，列名与真实 RESSET 导出一致，
   用于在没有数据权限时验证代码。

```text
data/
├── sample/                 # 合成样例（仓库自带）
│   └── raw/                # 结构与 data/raw 相同
└── raw/                    # ← 把你下载的 RESSET CSV 放到这里（不会进入 Git）
```

## 5. 环境配置

```bash
python -m pip install -r requirements.txt
```

- Python 3.10+
- 主要依赖：pandas、numpy、statsmodels、scipy、matplotlib
- 本次验证使用的版本：Python 3.10.2 / pandas 3.0.1 / numpy 2.3.5 / statsmodels 0.15.0 /
  scipy 1.18.1 / matplotlib 3.11.2
- 可选：PyMuPDF（`fitz`）——仅 `00_paper_targets.ipynb` 中"显示原论文页"的辅助函数需要，
  该函数默认注释掉，且需要你自行准备论文 PDF。

## 6. 快速验证（Sample Mode，无需 RESSET 数据）

三步即可确认环境与代码都正常：

```bash
# 1) 检查样例数据布局与字段（应为 FAIL=0）
python scripts/check_data_layout.py --data-dir data/sample

# 2) 用合成数据把 B 线主流水线完整跑一遍（约 15 秒）
python scripts/run_sample_pipeline.py

# 3) 跑静态检查与行为测试
python -m unittest discover -s tests -v
```

第 2 步会依次执行 9 个 Notebook 的全部代码单元（等价于在 Jupyter 里从
`fama_macbeth_8.ipynb` 一路运行），并打印 S2→S9 各表的形状与因子收益、平均风险溢价、
Newey–West t 值。**合成数据上的数字没有经济学含义，不能当作论文复现结果。**

## 7. 完整运行（Full Mode，使用真实 RESSET 数据）

1. 按 [docs/DATA_DOWNLOAD_GUIDE.md](docs/DATA_DOWNLOAD_GUIDE.md) 下载数据并放到 `data/raw/`。
2. 运行检查脚本，确认没有 FAIL：

   ```bash
   python scripts/check_data_layout.py --deep
   ```

3. 打开 `jupter_notebook_version/CH3_jup/CH_3_factors.ipynb`，全部运行。
   它会依次执行：论文原值参照 → 11 步数据管道 → 核心解释实验 → 补充定价检验。
4. 需要单步调试时，按 [docs/RUNNING_GUIDE.md](docs/RUNNING_GUIDE.md) 里的顺序逐个运行 Notebook。

> 完整数据下 B 线一次运行需要读入约 4 GB 日表并做多轮滚动计算，内存与耗时都不小；
> 下游 Notebook 通过 `%run` 重复执行上游流程是原始设计，见 [docs/RUNNING_GUIDE.md](docs/RUNNING_GUIDE.md)。

## 8. 当前研究成果

已实现（代码入口存在并可在合成数据上跑通的部分）：

| 模块 | 内容 | 入口 |
|---|---|---|
| 数据层 | 日/月/财务四表读取、清洗、股票池、年度事件表、point-in-time 对齐 | `src_jup` 前 3 个 Notebook |
| 特征层 | 市值、BM、EP、CP、动量（12-1）、波动率、MAX、非流动性、12 月换手、异常换手、应计利润、NOA | `features_3.ipynb` |
| 组合层 | 单变量十分位多空、5×5 规模中性、CH-3 的 2×3 市值加权 | `portfolio_5.ipynb` |
| 因子层 | MKT / SMB / VMG（CH-3）、CH-4 换手因子、FF-3 与 FF-5 代理 | `07_factor_returns.ipynb` |
| 回归层 | 时间序列 OLS（HC1）、单次截面、Fama–MacBeth（NW(4)）、GRS | `src_jup` 后三个 + `CH3_补充定价检验.ipynb` |
| 论文对照 | Table 1–10 / A1–A5 原值转录、逐表覆盖矩阵、复现报告 | `00_paper_targets.ipynb`、`06_reproduction_report.ipynb` |

已得到的主要本地结果与原文的对照、以及每项的验证状态，见
[docs/REPRODUCTION_STATUS.md](docs/REPRODUCTION_STATUS.md) 与
[results/README.md](results/README.md)。

## 9. 复现状态与局限

一句话：**方法链完整、代码可跑；数值上属于"部分复现"，不是论文的精确重制。** 主要局限：

- **数据口径**：论文用 WIND，本地用 RESSET；EPS 未做扣非、股本分母未拆 A 股与 A+B+H；
  无风险利率直接取 RESSET 月度字段，未与论文的一年期存款利率逐项核对。
- **样本月份**：论文声称 204 个月，本地严格实施"前一月至少 15 个交易日"后得到 199 个月；
  缺口的 5 个月**没有被放宽条件补齐**。
- **缺失数据导致的未完成项**：美国样本、真实借壳事件（CSRC 审批日）、1999–2006 完整财报、
  扣非/归母净利润历史、历史行业分类。
- **代理变量**：ROE、资产增长、应计利润、NOA、CP 的构造与论文附录存在可核对的差异；
  这些检验一律标注为"代理"。
- **本轮验证范围**：合成样例上的端到端运行与 25 项测试**已实际执行**；真实数据下的完整
  重跑**未在本轮执行**（数据约 12 GB，耗时以小时计），历史上的一次完整运行结果记录在
  `06_reproduction_report.ipynb` 与 [results/README.md](results/README.md)，
  并明确标注为"历史运行，未在本轮重跑"。

## 10. 参考论文

```bibtex
@article{liu2019size,
  title   = {Size and value in China},
  author  = {Liu, Jianan and Stambaugh, Robert F. and Yuan, Yu},
  journal = {Journal of Financial Economics},
  volume  = {134},
  number  = {1},
  pages   = {48--69},
  year    = {2019},
  doi     = {10.1016/j.jfineco.2019.03.004}
}
```

延伸阅读：Fama & MacBeth (1973)；Fama & French (1992, 1993, 2015)；Barillas & Shanken (2018)；
Hou, Xue & Zhang (2015)。方法层面的中文参考为石川、刘洋溢、连祥斌《因子投资：方法与实践》(2020)。

## 11. 实现说明

本仓库的代码是在 AI 辅助下完成与整理的：**研究问题、口径选择、结果解释由作者决定；
代码由作者在 AI 协助下编写，并辅以人工检查与测试。** 因此：

- 不应把本仓库读作"独立从零实现"或"论文已被完整复现"的证据；
- 所有"已实现"都附有代码入口；所有"已验证"都指**测试在本轮实际执行过**；
- 数值结论一律区分三类：论文原文数值、本地计算结果、以及尚未计算的项。

关于发布副本相对原工程做过的**最小必要修改**（路径发现、月表列名大小写、三处
`get_momentum` 调用缺失），逐条记录在 [docs/CHANGES.md](docs/CHANGES.md)。

---

## 版权与引用

- 论文与其中表格的版权归原作者与 Elsevier 所有；本仓库仅转录公开数值用于对照，
  未附带论文 PDF。
- RESSET 数据版权归北京聚源锐思数据科技有限公司所有；本仓库不附带任何原始或截取的
  真实数据，`data/sample` 为随机生成的合成数据。
- 若使用本仓库代码，请引用上面的论文条目。
