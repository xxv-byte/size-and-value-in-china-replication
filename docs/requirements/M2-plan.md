# M2 计划：CI 启用（requirements）

日期：2026-10-26　分支：`m2-ci-activation`　状态：进行中

## 1. 为什么做

M1 交付了 `.github/workflows/sample-mode.yml`，但它**从未真正运行过**：

- workflow 只在 `workflow_dispatch` 与 `pull_request` 上触发，而 M1 的分支是直接推送、没有开 PR；
- 因此 `main-protection` 里**不能**加 "Require status checks" —— 一旦加上，GitHub 会等一个永远不上报的检查，PR 永久卡住；
- 同时 `origin/m1-process-baseline` 这条远端分支已删除，本地还留着 remote-tracking 缓存。

M2 的唯一目的：**把这条 CI 变成"真实跑过、可依赖"的门禁**，从而闭合 M1 遗留的两项"未执行"。

## 2. 交付物

| # | 交付物 | 验收标准 |
|---|---|---|
| 1 | PR（本分支 → main） | 开 PR 即触发 `sample-mode` 首次运行，记录 run id 与 head SHA |
| 2 | 首次运行结论 | 绿：直接进第 3 步；红：定位真实原因、修复、记录在 `M2-validation.md` |
| 3 | `docs/testing/M2-results.json` | 由 CI artifact 或本地导出的等价证据；`totals.tests ≥ 25` |
| 4 | `docs/testing/M2-validation.md` | 含 run id / 结论 / 实际失败与修复 / 仍未执行项 |
| 5 | 规则集加 status check | `main-protection` 增加 "Require status checks"，指定 job 名 `verify`；加之前必须已有一次成功运行 |
| 6 | `.agent` 快照 | 本分支第一笔提交已完成（main=403f7ca、M1 合并与标签事实） |

## 3. 明确不做

- 不改任何 Notebook、不改 `scripts/check_data_layout.py` / `run_sample_pipeline.py` / `export_test_results.py` 的既有行为（除非 CI 暴露真实缺陷）；
- 不改 `requirements.txt` 的版本下界（除非 CI 证明某版本不可用，且要单独说明）；
- 不引入新的 workflow 文件；
- 不触碰 `data/raw`、不引入真实数据（CI 只用合成样例）；
- 不因"想让它绿"而弱化断言、跳过测试或加 `continue-on-error`。

## 4. 顺序（重要）

```
① 开 PR          → 触发首次运行
② 看结论        → 绿 / 红
③ 若红：修真因   → 重新触发（推新提交到本分支）
④ 绿之后        → 才允许在 Ruleset 里加 Require status checks
⑤ 合并 PR        → main 前进，门禁生效
```

**④ 必须在 ③ 完成之后**，否则会把自己锁在"PR 永远等检查"的状态里。

## 5. 边界说明

- CI 只验证：数据布局（合成样例）、25 项测试、证据导出。**不验证**论文数值、不做真实数据复现。
- CI 首次成功后，仍应保留"真实数据完整重跑未执行"这一条限制（见 `docs/VALIDATION.md` §5）。
