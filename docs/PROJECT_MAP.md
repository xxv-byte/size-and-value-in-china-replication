# 代码线全景（PROJECT_MAP）

给审阅者的最短路径：**先看这张图，再决定读哪个 Notebook。**

`~
                    data/raw（RESSET，用户自备）
                              │
        ┌─────────────────────┴──────────────────────┐
        │                                            │
   B 线 · src_jup/                             C 线 · CH3_jup/
   通用因子投资流水线                            论文（CH-3）复现
        │                                            │
   S0 原始日频表 ──────────────────────────────────► 01_read_local_data
        │                                            │
   S1 清洗 + 股票池                              02_clean_local_tables
        │                                            │
   S2 日频特征（15 个）◄──函数定义被借用────────────── 05_construct_characteristics
        │                                            │
   S3 月收益表 / S4 形成月快照 ──────────────────────► 03 / 04 / 06
        │                                            │
   S5 错期月度面板 ────────────────────────────────► monthly_final（剔最小 30%）
        │                                            │
   S6 组合收益表 ◄──get_groups_ch3 同公式──────────── 07_factor_returns（CH-3/FF-3/CH-4/FF-5）
        │                                            │
   S7 因子矩阵 F                                 08_anomaly_returns（10+ 异象）
        │                                            │
   S8 收益矩阵 R                                 09_daily_reversal
        │                                            │
   S9 回归结果（HC1 / NW(4)）◄──函数定义被借用────── CH3_核心解释实验、CH3_补充定价检验
                                                     │
                                              06_reproduction_report（覆盖率与差异）
`~

---

## 1. B 线：通用因子投资流水线（`src_jup/`）

| 顺序 | Notebook | 输入 → 输出 | 一句话 |
|---|---|---|---|
| 0 | `config_0.ipynb` | 无 → 常量 | 字段名、文件匹配规则、样本期、路径发现 |
| 1 | `data_io_1.ipynb` | CSV → df/bs_df/cf_df/fas_df | 四张表的读取（日表按样本期过滤） |
| 2 | `clean_and_universe_2.ipynb` | → 清洗后日表 | 类型规范化、去重、缩尾、股票池；三张表清洗；年度事件表 + point-in-time 对齐 |
| 3 | `features_3.ipynb` | → 日频特征表 | 市值、超额收益、动量、BM、EP、CP、资产增长、波动率、MAX、应计、NOA、非流动性、换手 |
| 4 | `monthly_4.ipynb` | → S3/S4/S5 | 月收益复利、形成月末快照、`ym = form + 1` 错期合并 |
| 5 | `portfolio_5.ipynb` | → S6/S7 | 单变量十分位、5×5 规模中性、CH-3 的 2×3 市值加权 |
| 6 | `time_series_regression_6.ipynb` | → R、B | 收益矩阵；逐股 OLS（HC1）求暴露 |
| 7 | `cross_section_regression_7.ipynb` | → E_R、E_F | **一次**截面回归（注意：这不是 Fama–MacBeth 第二步） |
| 8 | `fama_macbeth_8.ipynb` | → λ_t、λ̄、t | 逐月截面 + Newey–West(4) |
| 附 | `CH3_核心解释实验.ipynb` | → 主结果 | C 线主线实证 |
| 附 | `CH3_补充定价检验.ipynb` | → 补充表 | EP 赛马、GRS、CH-4 |

## 2. C 线：论文复现（`CH3_jup/`）

| 文件 | 作用 |
|---|---|
| `CH_3_factors.ipynb` | ★ 总入口：原值参照 → 数据管道 → 核心解释 → 补充检验 |
| `00_paper_targets.ipynb` | 论文 Table 1–10 / A1–A5 原值转录，只做逐格对照 |
| `01_data_and_factors.ipynb` | 管道调度器（`%run` 00→10） |
| `03_extended_analysis.ipynb` | 盈余公告、借壳与壳价值、30% 截断敏感性 |
| `04_behavior_checks.ipynb` | 11 项行为校验（错期、权重、GRS 单位不变性…） |
| `05_author_data_validation.ipynb` | 作者公开因子快照，作校准参照 |
| `06_reproduction_report.ipynb` | 复现报告：算了什么、还缺什么 |
| `07_bayesian_comparison.ipynb` | Barillas–Shanken 解析贝叶斯比较 |
| `08_additional_conclusions.ipynb` | 补充结论（盈余公告后半段、负 EP 稳健性） |
| `reproduction_pipeline/` | 11 步 CH-3 专用管道 |

## 3. 两条线的三种连接方式

| 方式 | 出现在 | 机制 | 注意 |
|---|---|---|---|
| `%run` 累积 | B 线各 Notebook | 执行上游全部代码单元、共享同一命名空间 | 下游会重复读取与重算（见 RUNNING_GUIDE §1.1） |
| `%run -i` + 开关 | `00_ch3_config.ipynb` | 先设 `run_features_pipeline = False`，再 `%run -i features_3.ipynb` | 只借函数定义，不触发全量计算 |
| ast 抽取 | `CH3_核心解释实验.ipynb` | `load_source_function` 从 Notebook JSON 里取出单个函数源码 | 不执行源 Notebook 的读数与画图代码 |

## 4. 与本仓库排除文件的关系

| 排除项 | 为什么不纳入 |
|---|---|
| `src/` + `main.py`（A 线） | 同一方法的早期模块化改写版，路径常量已失效，与 B 线重复 |
| `CH3/`（D 线） | CH-3 因子库的独立实现，无调用者；与 C 线重复且未接入 |
| `电子书解析文件夹/`（E 线） | 《因子投资：方法与实践》的电子书解析工具链，与实证代码零耦合 |
| `learning/`（49 份内部学习文档） | 面向作者的写作材料，含大量内部审查记录；其结论已提炼进 docs/ |
| `tests/test_learning_code_admission.py` 等 | 依赖 learning 文档的准入契约测试，脱离该目录无法运行 |
| `金融学作业/`、`金融市场学作业/` | 与本论文无关的课程作业 |
| `.superpowers/`、`docs/superpowers/` | Agent 工作过程记录（任务包、审查交接），不属于研究产出 |

> 想了解完整（含被排除部分）的工程结构，可参考作者工作区里的 `项目架构总览.md`；
> 本文件只描述**这个仓库里实际有什么**。
