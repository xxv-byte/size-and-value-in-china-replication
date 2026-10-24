# CH-3 因子统计（历史运行记录）

> **来源**：~~reproduction_pipeline/07_factor_returns.ipynb~~ 生成的 ~~f_ch3~~，
> 统计量由 ~~06_reproduction_report.ipynb~~ 汇总记录。
> **运行时间**：2026-10，真实 RESSET 全样本（1999-01 ~ 2016-12，有效 199 个月）。
> **本轮是否重跑**：否。合成样例上的 CH-3 数字没有意义，不能替代本表。

## 月均收益与显著性

| 因子 | 月均收益 | t 值 | 论文 Table 3 的对应项 |
|---|---|---|---|
| MKT | ≈0.727% | — | Table 3（市场） |
| SMB | ≈0.899% | ≈2.77 | Table 3（规模） |
| VMG | ≈0.954% | ≈3.49 | Table 3（价值，EP 口径） |

## 口径说明

- 因子收益为**月频小数收益**的百分比形式；MKT 为剔除市值最小 30% 后股票池的市值加权超额收益。
- SMB / VMG 由 2×3 六组合（S/B × G/M/V）市值加权合成，权重为总市值。
- 与论文的差异主要来自：数据源（WIND → RESSET）、样本月份（204 → 199）、
  EP 的分子（扣非净利润 → EPS 累计口径）。
- 复现报告同时记录："SMB 与 VMG 月均值的 t 值约 2.77 与 3.49，方向与显著性均与论文一致"。

## 如何重新生成

1. 准备 RESSET 数据 → ~~scripts/check_data_layout.py --deep~~（FAIL=0）；
2. 运行 ~~CH3_jup/CH_3_factors.ipynb~~；
3. 在 ~~07_factor_returns.ipynb~~ 的 ~~f_ch3~~ 上自行计算 ~~mean / std / t~~。
