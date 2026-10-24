# 发布副本相对原工程的改动记录（CHANGES）

本仓库是从作者本地的完整工作区中**复制**出来的发布副本。为了让**别人**能在自己的机器上运行，
必须改掉三处"只在本机成立"的东西；除此之外：

> **没有改动**任何统计方法、股票筛选标准、样本期、因子定义、回归设定、A 股/C 线判定逻辑、
> `%run` 结构与目录名（`jupter_notebook_version` 的拼写保持不变）。

下面三处改动都属于"让代码能跑"，不属于"改结果"。但按照约定，任何可能影响数值的改动都必须
单独说明并交由作者审查——请重点看第 3 条。

---

## 改动 1（P0）：路径发现，去掉个人绝对路径

| 项目 | 内容 |
|---|---|
| 文件 | `jupter_notebook_version/src_jup/config_0.ipynb`（第 8 个代码单元） |
| 原代码 | `root = Path(r'E:\周子程的文件\大二上\因子投资论文复现')` |
| 新代码 | `_find_project_root()`：优先读环境变量 `RESSET_PROJECT_ROOT`，否则自 `Path.cwd()` 向上查找含 `data/raw` 的目录，找不到就抛出中文报错 |
| 另加 | `data_dir = Path(os.environ.get('RESSET_DATA_DIR', root / 'data'))`，用于把样例数据指给流水线 |
| 症状 | 别人克隆后一定 `FileNotFoundError` / 读到空表 |
| 是否影响结果 | **不影响**：只改变"去哪里找文件"，字段、样本期、计算全同 |
| 验证 | `tests/test_notebook_integrity.py::test_config_has_no_hardcoded_root`；`check_data_layout.py` 的"个人绝对路径"扫描 |

---

## 改动 2（P0）：月表收盘价列名大小写

| 项目 | 内容 |
|---|---|
| 文件 | `jupter_notebook_version/src_jup/config_0.ipynb`（最后一个代码单元） |
| 原代码 | `monthly_close_price_raw = close_price`，即 `'Clpr'` |
| 新代码 | `monthly_close_price_raw = 'ClPr'` |
| 原因 | RESSET **日表**列名是 `Clpr`，**月表**列名是 `ClPr`（已用真实导出文件核对）。C 线 `01_read_local_data.ipynb` 用 `usecols` 读月表时，若写 `'Clpr'` 会直接 `ValueError: Usecols do not match columns` |
| 是否影响结果 | **不影响**：只修正列名引用；月表这一列在 C 线中用于"月末价格回退"的 `ClPr_monthly` |
| 验证 | `check_data_layout.py` 分别校验日表 `Clpr` 与月表 `ClPr`；样例数据同时提供两种写法 |

> 如果你的原始工作区里这个常量本来就叫 `'ClPr'`，说明本副本的原始 Notebook 保存的是旧版本，
> 请以你实际运行成功的那份为准。

---

## 改动 3（P0，需作者确认）：三处内联流程补 `df = get_momentum(df)`

| 项目 | 内容 |
|---|---|
| 文件 | `time_series_regression_6.ipynb`、`cross_section_regression_7.ipynb`、`fama_macbeth_8.ipynb`（各自的末尾内联代码单元） |
| 原代码 | 内联段依次调用 `get_market_feature → get_cp → get_asset_growth → get_excess_return → get_bm → get_ep → …`，**独独没有调用 `get_momentum`** |
| 症状 | `get_form_signal(df)` 里 `snap.rename(... day_mom: monthly_mom ...)` 之后选列，抛 `KeyError: 'monthly_mom'` —— 即这三个 Notebook 在原始状态下**跑不通** |
| 新代码 | 在 `df = get_market_feature(df)` 之后补一行 `df = get_momentum(df)`，与 `monthly_4.ipynb` / `portfolio_5.ipynb` 的内联顺序完全一致 |
| 是否影响结果 | **会改变"能不能跑"，不改变方法**：动量因子本来就已在 `direction_dict` 与 `F` 的 10 列清单里（`mom_fac`），缺了它这三个 Notebook 连 Fama–MacBeth 都到不了。补回后因子清单、公式、样本期都不变 |
| 请作者确认 | 如果你本机跑通时用的是另一份 Notebook（例如在 `%run` 链里保留了上一次的 `df`），那么这三处属于"补全缺失调用"，请审阅后决定是否合并 |

---

## 改动 4（不影响计算）：发布副本清空了所有 Notebook 执行输出

- 原工程的 Notebook 里嵌着大量 `outputs`（打印的 `df.head()`、表格、图片）。
- 清空原因有两条：
  1. **再分发风险**：输出里会打印真实 RESSET 个股行（价格、股本、财务），属于受限数据；
  2. **结论可信度**：旧输出容易被误读成"本次运行结果"。
- 影响：打开 Notebook 不再看到历史输出；需要时重新运行即可（Sample Mode 约 15 秒）。

---

## 改动 5（新增，不动原逻辑）：发布所需的辅助文件

| 新增 | 作用 |
|---|---|
| `scripts/check_data_layout.py` | 运行前数据检查（PASS/WARN/FAIL） |
| `scripts/run_sample_pipeline.py` | Sample Mode：用合成数据执行 9 个 Notebook 的全部代码单元 |
| `scripts/make_sample_data.py` | 生成合成样例（固定随机种子，可重建） |
| `tests/notebook_loader.py` | 用 ast 从 Notebook 抽取函数定义，供测试调用 |
| `tests/test_notebook_integrity.py` | 静态检查（JSON、`%run` 目标、函数清单、个人路径） |
| `tests/test_core_logic.py` | 行为测试（清洗、错期、分组、回归…） |
| `data/sample/` | 合成样例数据（**不含任何真实数据**） |
| `docs/*.md`、`results/*` | 数据指南、运行指南、复现状态、结果摘要 |

这些文件**没有**被任何 Notebook 依赖，删掉也不影响原有流水线。

---

## 改动 6（新增）：Notebook 代码的换行结构规范化

- 复制时若把 `source` 列表错误地合并成一行，会让整段代码变成一条注释。
- 发布前对全部 Notebook 做了规范化：每个 `source` 元素以换行符结尾（Jupyter 的标准格式）。
- 不改任何字符内容；由 `tests/test_notebook_integrity.py` 保证 JSON 合法且可解析。

---

## 如何核对这些改动

1. 逐条看上面的"原代码 / 新代码"。
2. 打开对应 Notebook 搜索关键词（`root` / `monthly_close_price_raw` / `get_momentum`）。
3. 跑 `python -m unittest discover -s tests -v`，其中
   `test_momentum_call_present_in_downstream_pipelines` 会断言第 3 条改动存在。
4. 想知道"改完之后还能不能算对"：跑 `python scripts/run_sample_pipeline.py`，
   它会真实执行 9 个 Notebook 并检查 F/R/B/λ 的形状与基本性质。

---

## 没有做的事（明确声明）

- 没有把 A 线（`src/` + `main.py`）、D 线（`CH3/`）、E 线（`电子书解析文件夹/`）纳入仓库。
- 没有合并 B/C 两条线，没有把 `%run` 改成 import，没有引入第二套因子实现。
- 没有上传任何 RESSET 原始数据、论文 PDF、课堂作业、内部 Agent 工作记录。
- 没有为了"跑得快"而抽样、删列或缩短样本期。
