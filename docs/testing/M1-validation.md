# M1 验证记录（testing）

日期：2026-10-26　分支：`m1-process-baseline`　被测源码：见 `M1-results.json` 的 `codeVersion`

## 最终证据

| 项目 | 值 |
|---|---|
| 命令 | `python -m unittest discover -s tests` |
| 结果 | **SUCCESS**（`tests=25 failures=0 errors=0 skipped=0`） |
| 机器可读证据 | [`M1-results.json`](M1-results.json)（含 per-suite / per-case 状态与耗时） |
| 环境 | Windows-11-10.0.26300-SP0 · Python 3.12.14 · pandas 3.0.1 · numpy 2.3.5 · statsmodels 0.15.0 · scipy 1.18.1 |
| 样例数据自检 | `python scripts/check_data_layout.py --data-dir data/sample` → `FAIL=0 WARN=2 PASS=23`，退出码 0 |
| 改动范围 | 仅新增流程文件；`git status` 中 `.ipynb` 计数 = **0** |

## 实际失败、修复与复验

| # | 现象 | 原因 | 修复 | 复验 |
|---|---|---|---|---|
| 1 | `export_test_results.py` 抛 `ValueError: 'docs\testing\M1-results.json' is not in the subpath of …` | `--out` 传相对路径时，`Path.relative_to(REPO)` 失败 | 相对路径先拼到仓库根再解析 | 复跑 → `evidence -> docs/testing/M1-results.json`，退出码 0 |
| 2 | 首次证据的 `codeVersion` 记为 `… (dirty working tree)` | 先在未提交的工作区导出 | 改为**先提交流程文件、再导出证据**，使 SHA 指向干净提交 | 见下一个提交中的 `M1-results.json` |

## 契约逐条核验

| 门禁 | 结果 |
|---|---|
| G1 既有测试仍全绿 | ✅ 25/25 |
| G2 样例自检仍通过 | ✅ FAIL=0，退出码 0 |
| G3 证据可机器读 | ✅ `json.load` 通过，含 `totals` 与 `suites` |
| G4 证据与实际一致 | ✅ `totals.tests=25` 等于实际用例数；`buildResult=SUCCESS` 与退出码 0 一致 |
| G5 无副作用 | ✅ 新增文件清单内无 `.ipynb` |
| G6 不泄漏 | ✅ 新增文件无个人绝对路径、无凭据、无真实数据行 |

## 未执行项与边界（不得改写为"通过"）

1. **`.github/workflows/sample-mode.yml` 从未在本仓库触发过**：它只在 `workflow_dispatch` 与 `pull_request` 上运行，当前分支推送不会触发。首次运行记录待 PR 或手动触发后补。
2. **真实 RESSET 数据下的完整重跑仍未执行**：与 `docs/VALIDATION.md` §5 一致，受数据量（18,217,775 行）与耗时限制。
3. **测试运行环境是 Python 3.12.14**，而 `README.md` 记录的历史验证环境是 3.10.2；两者都通过，但未做跨版本矩阵。
4. **`M1-results.json` 的 `log` 字段不是完整日志**：只记录命令与说明，完整输出在终端/CI artifact。这是刻意的，避免把大段文本塞进版本库。
5. 本阶段**没有**验证任何论文数值，也没有改动任何实证代码。

## 复现方式

```bash
python -m unittest discover -s tests -v
python scripts/check_data_layout.py --data-dir data/sample
python scripts/export_test_results.py --milestone M1 --out docs/testing/M1-results.json --quiet
```
