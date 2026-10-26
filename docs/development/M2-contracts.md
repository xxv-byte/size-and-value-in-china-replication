# M2 契约：CI 启用

## 范围与门禁

只做"让 CI 真实跑通并接入门禁"，不动实证代码。门禁：

| 门禁 | 判定 |
|---|---|
| G1 首次运行有据可查 | 记录 `sample-mode` 的 run id、head SHA、结论（含失败时的失败步骤名） |
| G2 测试数量不缩水 | `M2-results.json` 的 `totals.tests ≥ 25`，且 `failures=errors=skipped=0`（skipped>0 需说明理由） |
| G3 未削弱断言 | 检查 diff：不得新增 `continue-on-error`、`|| true`、`skip`、`xfail`、`-k "not ..."` |
| G4 无实证改动 | `git diff --stat main..HEAD` 不含 `.ipynb` |
| G5 状态检查名称正确 | Ruleset 里配置的检查名与 workflow/job 实际名称一致（`sample-mode / verify`） |
| G6 不泄漏 | 新增文件无个人绝对路径、凭据、真实数据 |

## 证据状态

| 证据 | 位置 | 状态 |
|---|---|---|
| 首次运行记录 | 本节"运行记录"表 + `M2-validation.md` | 待填（开 PR 后） |
| 结构化测试结果 | `docs/testing/M2-results.json` | 待生成 |
| 规则集变更 | `main-protection` 的 `required_status_checks` | 待启用（须在 G1 绿之后） |

## 运行记录

| 轮次 | 触发 | run id | head SHA | 结论 | 失败步骤 / 备注 |
|---|---|---|---|---|---|
| 1 | PR 创建 | 待填 | 待填 | 待填 | 待填 |

## 已实施的本地门禁（2026-10-26）

- 本地等价预演：`python scripts/check_data_layout.py --data-dir data/sample` + `python scripts/export_test_results.py`，二者与 workflow 的两个步骤完全一致（同命令、同参数）。
- 差异仅在于运行平台（本地 Windows / CI ubuntu-latest）与 Python 版本（本地 3.12 / CI 3.11）。

## 最终契约核验

以 `docs/testing/M2-validation.md` 的"最终证据"一节为准；本文件不预先声称通过。
