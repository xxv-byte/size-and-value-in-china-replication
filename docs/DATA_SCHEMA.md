# 数据字段口径（DATA_SCHEMA）

本文件是 [DATA_DOWNLOAD_GUIDE.md](DATA_DOWNLOAD_GUIDE.md) 的字段级附录。
所有列名、单位与示例值均取自**真实 RESSET 导出文件**（已抽样核对），
"代码读取"一列对应 `jupter_notebook_version/src_jup/data_io_1.ipynb` 与 `config_0.ipynb`。

---

## 1. 日股票综合数据（Daily Stock）

| 项目 | 内容 |
|---|---|
| RESSET 表名 | 日股票综合数据（RESSET/DB 股票库） |
| 文件名模式 | `RESSET_DRESSTK_*.csv`（可多分片、可嵌套目录） |
| 数据频率 | 日频 |
| 一行代表 | 某股票在某交易日的一条行情 + 当日可见的财务字段 |
| 唯一键 | `(Stkcd, Date)` |
| 必需字段 | `Stkcd, Listedstate, Date, Clpr, Trdvol, Trdsum, Fullshr, Dret, DRfRet, PB, ROE, EPS, Infopubdt, Enddt, Reporttype` |
| 字段单位 | 见下表 |
| 时间口径 | `Date` 为交易日；`Infopubdt/Enddt` 为当日财务字段的公告日/报告期 |
| 缺失值处理 | `cleaning()` 对必需列 `dropna`；数值列在 1%/99% 分位缩尾 |
| 用途 | 市值、收益、无风险利率、BM、EP、ROE、波动率、MAX、换手、非流动性 |
| 读取函数 | `read_daily_data()`（读取时即按 `start_date~final_date` 过滤） |

| 字段 | 真实示例 | 经济含义 | 单位 | 代码中的用途 |
|---|---|---|---|---|
| `Stkcd` | `"000001"` | 股票代码 | 六位字符串 | 主键；`normalize_stock_code` 统一补零 |
| `Listedstate` | `Norm` / `ST` | 上市状态 | 文本 | `universe()` 只保留 `Norm` |
| `Date` | `2011-01-04` | 交易日 | 日期 | 主键；形成月/持有月的来源 |
| `Clpr` | `16.0200` | 未复权收盘价 | 元 | 市值 = `Clpr × Fullshr`；EP 分母 |
| `Trdvol` | `35884061` | 成交量 | 股 | 日换手率 = `Trdvol / Fullshr` |
| `Trdsum` | `573343723.86` | 成交额 | 元 | Amihud 非流动性分母 |
| `Fullshr` | `3485013762` | 总股本 | 股 | 市值、换手率分母 |
| `Dret` | `0.0146` | 日收益率 | **小数** | 日超额收益、波动率、MAX、累积收益 |
| `DRfRet` | `0.000125` | 日无风险收益率 | **小数** | 超额收益 = `Dret − DRfRet` |
| `PB` | `1.81` | 市净率 | 倍 | `BM = 1/PB`（FF-3 的 HML） |
| `PE` | `8.88` | 市盈率 | 倍 | 仅作参考，未进入因子 |
| `EPS` | `0.49` | 每股收益（报告期累计） | 元/股 | `EP = EPS / Clpr`（CH-3 的 VMG 排序信号） |
| `ROE` | `5.2912` | 净资产收益率 | **百分数** | 盈利能力代理（FF-5 的 RMW 代理） |
| `Infopubdt` | `2010-10-28` | 财务字段公告日 | 日期 | **point-in-time 可用日** |
| `Enddt` | `2010-09-30` | 财务字段报告期末 | 日期 | 与资产负债表对齐 |
| `Reporttype` | `Q3` | 报告期类型 | 文本 | 年度事件只取 `Q4` |
| `AdjClpr1/2` | `637.8535` | 复权价 | 元 | **代码未使用** |

> 注意：日表列名是 `Clpr`（小写 r），月表是 `ClPr`（大写 P）。这是 RESSET 导出本身的差异，
> 代码里用 `close_price='Clpr'` 与 `monthly_close_price_raw='ClPr'` 两个常量分别处理。

---

## 2. 月股票综合数据（Monthly Stock）

| 项目 | 内容 |
|---|---|
| RESSET 表名 | 月股票综合数据 |
| 文件名模式 | `RESSET_MRESSTK_*.csv` |
| 数据频率 | 月频 |
| 一行代表 | 某股票在某月的月度行情 + 月末财务快照 |
| 唯一键 | `(Stkcd, Date)` |
| 必需字段 | `Stkcd, Date, ClPr, Monret, Monrfret, Montrds, Fullshr, PB, EPS, ROE, Infopubdt, Enddt, Reporttype` |
| 字段单位 | `Monret/Monrfret` 为小数；价格元；股本股 |
| 时间口径 | `Date` 为月末日；财务字段为月末时点可见值 |
| 缺失值处理 | C 线 `02_clean_local_tables` 统一类型后按 `(股票, 月)` 去重 |
| 用途 | C 线的月度收益（首选）与月末信号（缺失时回退日表） |
| 读取函数 | C 线 `reproduction_pipeline/01_read_local_data.ipynb` 直接 `pd.read_csv(usecols=...)` |

| 字段 | 示例 | 含义 | 单位 |
|---|---|---|---|
| `Monret` | `0.0284` | 月收益率 | 小数 |
| `Monrfret` | `0.003466` | 月无风险收益率 | 小数 |
| `Montrds` | `18`（交易日数） | 月内交易天数 | 天 |
| `ClPr` | `47.4200` | 月末收盘价 | 元 |
| 其余 | 同日表 | `PB/EPS/ROE/Infopubdt/Enddt` | 同 |

> 月表有两个列宽版本（37 列 / 57 列）。代码只用上表列出的字段，两个版本都包含，
> 因此**不需要统一列宽**；但列名大小写必须一致。

---

## 3. 资产负债表（Balance Sheet）

| 项目 | 内容 |
|---|---|
| RESSET 表名 | 资产负债表（`BS_ALL`） |
| 文件名模式 | `RESSET_BS_ALL_1.csv`（**完全一致**） |
| 数据频率 | 报告期（季/年） |
| 一行代表 | 某公司某报告期的资产负债表 |
| 唯一键 | 严格说是 `(A_StkCd, ReportType, EndDt)`；同一键仍可能有合并/母公司多版本 |
| 必需字段 | `A_StkCd, ReportType, EndDt, InfoPubDt, TotAss, TotCurrAss, TotCurLia, ShortLoan, LongLoan, TaxPay, CashEqv, TradAss, TotLiab` |
| 字段单位 | 金额均为**元** |
| 时间口径 | `EndDt` 报告期末；`InfoPubDt` 公告日（point-in-time 用） |
| 缺失值处理 | `bs_cleaning` 对必需列 `dropna`；短期借款等缺失在应计/NOA 中按 0 处理 |
| 用途 | 资产增长、AM（总资产/市值）、NOA、应计利润 |
| 读取函数 | `read_bs_data()`（`usecols` 只取 12 列） |

| 字段 | 含义 | 单位 | 代码中的用途 |
|---|---|---|---|
| `TotAss` | 总资产 | 元 | 资产增长 = 本期/上期；AM = 总资产/市值 |
| `TotCurrAss` | 流动资产合计 | 元 | 应计的 `ΔCA` |
| `TotCurLia` | 流动负债合计 | 元 | 应计的 `ΔCL` |
| `ShortLoan` | 短期借款 | 元 | 应计的 `ΔSTD` |
| `LongLoan` | 长期借款 | 元 | NOA 的 OL 计算 |
| `TaxPay` | 应交税费 | 元 | 应计的 `ΔTP` |
| `CashEqv` | 货币资金 | 元 | 应计的 `ΔCash`；NOA 的 OA 扣减项 |
| `TradAss` | 交易性金融资产 | 元 | NOA 的 OA 扣减项 |
| `TotLiab` | 总负债 | 元 | NOA 的 OL 起点 |

> **口径提醒**：代码不读 `ConFlg/AccStd/AdjFlg`，无法保证取到合并报表；
> 同一 `(股票, 报告期)` 的重复版本按"排序后取最后一条"处理。

---

## 4. 现金流量表（Cash Flow）

| 项目 | 内容 |
|---|---|
| RESSET 表名 | 现金流量表（`SCF_ALL`） |
| 文件名模式 | `RESSET_SCF_ALL_1.csv`（**完全一致**） |
| 数据频率 | 报告期 |
| 一行代表 | 某公司某报告期的现金流量表 |
| 唯一键 | `(A_StkCd, ReportType, EndDt)` |
| 必需字段 | `A_StkCd, ReportType, EndDt, InfoPubDt, CENetIncr, IntangAssAmort, DeferExpAmort` |
| 字段单位 | 元 |
| 时间口径 | `InfoPubDt` 为可用日；年度事件只取 `ReportType='Q4'` |
| 缺失值处理 | 摊销列缺失按 0 计入折旧摊销；净现金流缺失则该年度事件缺失 |
| 用途 | CP = 净现金流/市值；应计利润的摊销项 |
| 读取函数 | `read_cf_data()`（`usecols` 7 列） |

| 字段 | 含义 | 单位 | 用途 |
|---|---|---|---|
| `CENetIncr` | 现金及现金等价物净增加额 | 元 | CP 分子 |
| `IntangAssAmort` | 无形资产摊销 | 元 | 应计的摊销 |
| `DeferExpAmort` | 长期待摊费用摊销 | 元 | 应计的摊销 |

---

## 5. 固定资产及折旧（Fixed Assets）

| 项目 | 内容 |
|---|---|
| RESSET 表名 | 固定资产及折旧（`BSNOTE_FIXASSDEPR`） |
| 文件名模式 | `RESSET_BSNOTE_FIXASSDEPR_*.csv` |
| 数据频率 | 报告期 |
| 一行代表 | 某公司某报告期、某一固定资产类别的折旧明细 |
| 唯一键 | `(A_StkCd, ReportType, EndDt, FixAssType)` |
| 必需字段 | `A_StkCd, ReportType, EndDt, FixAssType, CurIncrAD` |
| 字段单位 | 元 |
| 时间口径 | 无公告日字段 → 代码用 `EndDt + 4 个月` 作为可用日（保守代理） |
| 缺失值处理 | 只保留 `FixAssType='99999'`（合计）与 `ReportType='Q4'` |
| 用途 | 应计利润的折旧项 `Dep` |
| 读取函数 | `read_fas_data()`（`usecols` 5 列） |

| 字段 | 含义 | 用途 |
|---|---|---|
| `FixAssType` | 固定资产类别，`99999` 为合计 | 过滤合计行 |
| `CurIncrAD` | 本期折旧增加额 | 应计的 Dep |

---

## 6. 可选表

| 表 | 文件名 | 用途 | 备注 |
|---|---|---|---|
| 三板/上市状态 | `RESSET_THIMKTSTKINFO_1.csv` | 上市状态辅助 | 核心流程不读 |
| 吸收合并 | `RESSET_MERG_1.csv` | 借壳/壳价值代理 | **不是**论文的 133 起借壳事件，仅作不足参照 |

---

## 7. 与代码常量的对应

| config 常量 | 值 | 出现在 |
|---|---|---|
| `stock_code` | `Stkcd` | 日表、月表 |
| `close_price` | `Clpr` | 日表 |
| `monthly_close_price_raw` | `ClPr` | 月表 |
| `daily_ret / daily_rfret` | `Dret / DRfRet` | 日表 |
| `monthly_return_raw / monthly_rfreturn_raw` | `Monret / Monrfret` | 月表 |
| `bs_stock_code / bs_end_date / bs_public_date` | `A_StkCd / EndDt / InfoPubDt` | 资产负债表 |
| `cf_code / cf_net_increase` | `A_StkCd / CENetIncr` | 现金流量表 |
| `fas_code / fasdepr_type` | `A_StkCd / FixAssType` | 固定资产表 |

---

## 8. 已知的口径不确定项（待核实，不作为结论）

1. `Dret` 的复权与分红处理：以 RESSET 数据词典为准，本仓库未逐字核对。
2. `EPS` 为报告期累计值，未做年化；EP 因此是"累计口径 E/P"，排序可用但量级不等于年化 E/P。
3. `ROE` 是百分数，直接作为排序信号使用（单调变换不影响分组）。
4. 资产负债表/现金流量表未按 `ConFlg/AccStd` 过滤，合并与母公司版本可能混用。
5. 三板/上市状态表与吸收合并表的字段口径未接入核心流程，仅扩展分析使用。
