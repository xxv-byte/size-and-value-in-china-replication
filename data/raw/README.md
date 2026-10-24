# data/raw —— 请把 RESSET 原始数据放在这里

本目录**不包含任何数据**，也**不会进入 Git**（见仓库根目录 `.gitignore`）。

## 放什么

按 [docs/DATA_DOWNLOAD_GUIDE.md](../../docs/DATA_DOWNLOAD_GUIDE.md) 下载 RESSET 的 5 张核心表
（外加 2 张可选表），把 CSV 放到本目录下的任意子目录里。目录名只是给人看的，
代码靠**文件名**匹配：

| 代码里的 glob | 你必须提供的文件名 |
|---|---|
| `RESSET_DRESSTK_*.csv` | 日股票综合数据，可按年份拆成多个文件，文件名必须以 `RESSET_DRESSTK_` 开头、`.csv` 结尾 |
| `RESSET_MRESSTK_*.csv` | 月股票综合数据，同上规则，前缀 `RESSET_MRESSTK_` |
| `RESSET_BS_ALL_1.csv` | 资产负债表，**文件名必须完全一致** |
| `RESSET_SCF_ALL_1.csv` | 现金流量表，**文件名必须完全一致** |
| `RESSET_BSNOTE_FIXASSDEPR_*.csv` | 固定资产及折旧，前缀 `RESSET_BSNOTE_FIXASSDEPR_` |
| `RESSET_THIMKTSTKINFO_1.csv` | （可选）三板/上市状态辅助表 |
| `RESSET_MERG_1.csv` | （可选）吸收合并事件 |

## 放完之后

```bash
python scripts/check_data_layout.py --deep
```

PASS/FAIL 会直接指出缺哪张表、文件名该叫什么、字段对不对。
