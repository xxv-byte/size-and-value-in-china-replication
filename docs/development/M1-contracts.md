# M1 契约：过程基线

## 范围与门禁

本阶段只新增流程文件，不触碰实证代码。门禁：

| 门禁 | 判定 |
|---|---|
| G1 既有测试仍全绿 | `python -m unittest discover -s tests` 退出码 0，25 项全过 |
| G2 样例自检仍通过 | `python scripts/check_data_layout.py --data-dir data/sample` 退出码 0（FAIL=0） |
| G3 证据可机器读 | `docs/testing/M1-results.json` 能被 `json.load` 解析，且含 `totals/suites` |
| G4 证据与实际一致 | `totals.tests` 等于本轮实际用例数；`buildResult` 与实际退出码一致 |
| G5 无副作用 | `git diff --stat main..HEAD` 只包含流程文件，不含 `.ipynb` 改动 |
| G6 不泄漏 | 新增文件不含个人绝对路径、凭据、真实数据行 |

## 证据状态

| 证据 | 位置 | 本轮状态 |
|---|---|---|
| 测试结果（机器读） | `docs/testing/M1-results.json` | 由 `scripts/export_test_results.py` 生成 |
| 验证记录（人读） | `docs/testing/M1-validation.md` | 含"未执行项" |
| CI 定义 | `.github/workflows/sample-mode.yml` | 已定义，**未在本仓库实际触发过**（见 validation 的未执行项） |

## 已实施的本地门禁（2026-10-26）

- `scripts/export_test_results.py`：跑 unittest → 收集 per-suite 计数与用例名 → 写 JSON；捕获 `git rev-parse HEAD` 作为 `codeVersion`。
- 门禁顺序：先跑测试（G1）→ 跑样例检查（G2）→ 导出证据（G3）→ 人读核对（G4/G5/G6）。

## 最终契约核验

以 `docs/testing/M1-validation.md` 的"最终证据"一节为准；本文件不预先声称通过。
