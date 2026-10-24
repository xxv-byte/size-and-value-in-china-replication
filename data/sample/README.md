# data/sample —— 合成样例数据（非真实数据）

## 这是什么

一套**随机生成**的股票行情与财务报表，用于在没有 RESSET 权限时验证代码能否跑通：

- 40 只股票（20 只 `000001` ~ `000020`、20 只 `600001` ~ `600020`）
- 522 个交易日（2013-01-01 ~ 2014-12-31）、24 个自然月
- 20,880 行日表、960 行月表、每年 3 个财年的三张财务报表

## 这不是什么（重要）

1. **不是真实数据的抽样**。全部数值由 `numpy.random.default_rng(20240101)` 生成，
   股票代码只是占位符，公司名统一为"例股NN"。
2. **不能用来做任何实证结论**。它的收益、市值、财务指标没有经济学含义，
   跑出来的因子收益、alpha、t 值都不代表中国股市。
3. **不能替代 Full Mode**。论文复现必须在真实 RESSET 数据上运行。

## 目录结构（与 `data/raw` 完全一致）

`~
data/sample/raw/
├── RESSET_SAMPLE_日股票综合数据/RESSET_DRESSTK_SAMPLE.csv
├── RESSET_SAMPLE_月股票综合数据/RESSET_MRESSTK_SAMPLE.csv
├── RESSET_SAMPLE_资产负债表/RESSET_BS_ALL_1.csv
├── RESSET_SAMPLE_现金流量表/RESSET_SCF_ALL_1.csv
└── RESSET_SAMPLE_固定资产及折旧/RESSET_BSNOTE_FIXASSDEPR_SAMPLE.csv
`~

文件名刻意匹配代码里的 5 个 glob（`RESSET_DRESSTK_*.csv`、`RESSET_MRESSTK_*.csv`、
`RESSET_BS_ALL_1.csv`、`RESSET_SCF_ALL_1.csv`、`RESSET_BSNOTE_FIXASSDEPR_*.csv`）。

## 字段口径（与真实 RESSET 一致的部分）

| 字段 | 样例中的取值方式 | 与真实数据的一致性 |
|---|---|---|
| `Dret` / `DRfRet` | 小数（如 0.0146） | 一致：真实 RESSET 也是小数 |
| `Clpr` / `ClPr` | 元 | 一致 |
| `Fullshr` | 股 | 一致 |
| `PB` / `PE` | 倍 | 一致 |
| `EPS` | 元/股 | 一致（但样例没有报告期累计的季度结构） |
| `ROE` | 百分数 | 一致 |
| `Infopubdt` / `Enddt` / `Reporttype` | 年报公告日 = 报告期 + 4 个月 | 近似：真实公告日各不相同 |
| `Listedstate` | 全部 `Norm` | 简化：真实数据含 `ST` 等状态 |
| 财报表金额 | 元 | 一致（但样例只有 Q4，且合并/母公司只有一个版本） |

## 它覆盖了哪些代码路径

`scripts/run_sample_pipeline.py` 用这套数据真实执行了 9 个 Notebook 的全部代码单元，
覆盖：读取 → 清洗 → 股票池 → 15 个日频特征 → 月收益复利 → 形成月快照 → 错期合并 →
单变量十分位 / 5×5 规模中性 / CH-3 的 2×3 → 收益矩阵 → 时序回归 → 截面回归 →
Fama–MacBeth（Newey–West）。

## 它覆盖**不了**什么

- 真实数据的缺失模式（停牌、退市、财报缺失、B/H 股空代码）；
- 1999–2016 的长样本与 199 个有效月；
- 任何与论文数值有关的比较。

## 重新生成

`~
python scripts/make_sample_data.py                 # 默认参数，覆盖写入
python scripts/make_sample_data.py --stocks 60 --start 2010-01-01 --end 2014-12-31
`~

修改参数会改变行数，但不会改变列名与口径；生成后用
`python scripts/check_data_layout.py --data-dir data/sample` 自检。
