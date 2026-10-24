# 模型比较（历史运行记录）

> **来源**：~~07_factor_returns.ipynb~~（构造 ~~f_ch3 / f_ff3 / f_ch4 / f_ff5~~）+ ~~CH3_补充定价检验.ipynb~~（互相定价与 GRS）。
> **运行时间**：2026-10，真实数据；**本轮未重跑**。

## 已构造的因子集

| 模型 | 因子 | 说明 |
|---|---|---|
| CH-3 | MKT, SMB, VMG | 论文主模型 |
| FF-3 | MKT, ~~ff_size_factor~~, ~~ff_value_factor~~ | HML 用 BM（~~1/PB~~）替代 EP |
| CH-4 | MKT, SMB, VMG, ~~turnover_factor_pmo~~ | CH-3 + 异常换手因子（取负号） |
| FF-5 代理 | MKT, ~~ff_size_factor~~, ~~ff_value_factor~~, ~~ff_profit_factor~~, ~~ff_invest_factor~~ | 盈利用 ROE 代理、投资用资产增长代理 |

## 结论方向（来自 06 报告的记录）

- 加入 CH-3 后，十项异象的平均绝对 alpha 由 CAPM 的 ≈0.974% 降到 ≈0.465%，
  平均 R² 由 ≈0.061 升到 ≈0.470；5% 显著 alpha 由 5 项降到 4 项。
- ROE 盈利能力代理因子在 CH-3 下的 alpha ≈0.153%（t≈0.93，199 个月）；
  资产增长投资代理因子 ≈0.002%（t≈0.01，95 个月）。**未拒绝零 alpha ≠ 证明 alpha 为零。**
- GRS 检验在 CH-3 与 FF-3 的共同样本月份上计算；样本月份与论文不同，p 值不可直接对比。

## 注意

- 以上是"代理变量下的本地结论"，不能读作"论文结论已被精确复现"。
- FF-5 的两个因子是代理（ROE / 资产增长），不是论文的营业利润与投资口径。
