# M1 计划：过程基线（requirements）

日期：2026-10-26　分支：`m1-process-baseline`　状态：已实现，待审阅

## 1. 为什么做

当前仓库对"读者"是完整的（README + 7 份指南 + 31 个 Notebook + 25 项测试），但对"**下一次改动**"没有制度化：

- 没有"这一阶段要做到什么"的计划文件；
- 没有"做成什么样算过"的验收契约；
- 测试结果只存在于终端输出，无法与某次提交绑定；
- 改动与证据之间没有稳定的一对一关系。

## 2. 这一阶段要交付什么

| # | 交付物 | 验收标准 |
|---|---|---|
| 1 | `AGENTS.md` | 12~20 行内，写清四条纪律、提交规范、禁止事项，并指向 `.agent` |
| 2 | `.agent` | 含用法、当前阶段、快照（≤5 条、每条≤8 行、绑定日期/分支/commit） |
| 3 | `docs/requirements/M1-plan.md` | 本文件 |
| 4 | `docs/development/M1-contracts.md` | 四段式：范围与门禁 / 证据状态 / 已实施的本地门禁 / 最终核验 |
| 5 | `docs/testing/M1-results.json` | 由脚本从真实 `unittest` 运行导出，字段含 milestone/capturedAt/command/buildResult/platform/versions/codeVersion/totals/suites |
| 6 | `docs/testing/M1-validation.md` | 人读：最终证据 / 实际失败与复验 / 未执行项与边界 |
| 7 | `.github/workflows/sample-mode.yml` | 仅在 `workflow_dispatch` 与 `pull_request` 触发；跑样例数据检查 + 25 项测试；不因分支推送而触发 |
| 8 | `scripts/export_test_results.py` | 一条命令产出 results.json；缺字段时自检报错 |

## 3. 明确不做

- 不改任何 Notebook、不改 `scripts/check_data_layout.py` 与 `scripts/run_sample_pipeline.py` 的既有行为；
- 不动 `main` 上已发布的读者文档（7 份指南原样保留）；
- 不引入全量真实数据运行（仍受资源限制，见 `docs/VALIDATION.md` §5）。

## 4. 命名规则（本阶段确定，后续沿用）

| 对象 | 规则 | 例 |
|---|---|---|
| 里程碑分支 | `m<编号>-<kebab-主题>` | `m1-process-baseline`、`m2-ch3-table-repro` |
| 工具前缀 | **只有真的用该工具编辑过才加** | 真用过 Codex → `codex/m3-...`；未用过 → 不加 |
| 契约 / 证据 | `M<编号>-contracts.md` / `M<编号>-results.json` / `M<编号>-validation.md` | `M1-contracts.md` |
| 提交 | Conventional Commits + scope | `docs(m1): add process baseline` |

## 5. 后续里程碑的候选（未排期）

1. `m2-table3-verification`：把 CH-3 因子统计做成可复跑的导出（需真实数据）。
2. `m3-financial-vintage`：给资产负债表/现金流量表加 `ConFlg/AccStd` 过滤，评估对 EP/CP 的影响。
3. `m4-share-base`：拆分 A 股股本分母，重算市值加权。
