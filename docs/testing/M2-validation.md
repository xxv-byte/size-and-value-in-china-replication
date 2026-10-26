# M2 验证记录（testing）

日期：2026-10-26　分支：`m2-ci-activation`　被测源码：CI 检出 `refs/pull/2/merge` = `8d87c70`

## 最终证据

| 项目 | 值 |
|---|---|
| 触发 | PR #2 创建（`pull_request` 事件） |
| run id | **40313718145** ｜ [运行页面](https://github.com/xxv-byte/size-and-value-in-china-replication/actions/runs/40313718145) |
| 结论 | **success**（全部步骤通过） |
| 耗时 | 约 **37 秒**（含 pip 安装） |
| 平台 | `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39` · Python **3.11.17** |
| 测试 | `tests=25 failures=0 errors=0 skipped=0` → `buildResult=SUCCESS` |
| 数据布局检查 | `FAIL=0 WARN=2 PASS=23`（WARN 为可选表缺失，符合预期） |
| 结构化证据 | [`M2-results.json`](M2-results.json)（含 runId / headSha / mergeRefSha / per-suite） |
| 步骤 | 1 检出 · 2 setup-python · 3 安装依赖 · 4 数据布局 · 5 测试+证据 · 6 上传 artifact —— **全部 success** |

### 一个容易误读的点

`pull_request` 事件默认检出 **`refs/pull/2/merge`**（即 GitHub 把分支 head `b79f242` 合进 `main 403f7ca` 的临时合并提交），所以 CI 里记录的
`codeVersion = 8d87c70` **不是**分支 head。要核对"这次 CI 测的是哪份代码"，应同时看 `headSha` 与 `mergeRefSha`。

## 实际失败、修复与复验

| # | 现象 | 处理 |
|---|---|---|
| 1 | 本地 `git push` 连续失败（`github.com:443` 被重置 / 超时），无法推送分支 | 改用 **GitHub Git Data API** 创建 blob/tree/commit/ref；本地与远端的 **tree SHA 一致**（`4600984`），证明内容逐字节相同，仅提交对象不同（时间戳/签名） |
| 2 | 首次 `gh pr merge` 参数误用：`-m` 是 `--merge`，不是多行正文 | 改为 `--body-file`，合并成功 |
| 3 | 下载 CI artifact 时工作目录未切换，落到了原工作区 | 立即删除该目录并确认原工作区恢复原状；改到仓库内 `_ci_artifact`（用完即删） |

**CI 本身是首次运行即通过，没有需要修复的失败。** 上述三条都是"发布通道"的问题，不是代码问题。

## 契约核验（G1–G6）

| 门禁 | 结果 |
|---|---|
| G1 首次运行有据可查 | ✅ run 40313718145 / head `b79f242` / merge `8d87c70` / success |
| G2 测试数量不缩水 | ✅ 25 项，0 失败 0 错误 0 跳过 |
| G3 未削弱断言 | ✅ 本分支 diff 无 `continue-on-error` / `|| true` / `skip` / `xfail` |
| G4 无实证改动 | ✅ `git diff --stat main..HEAD` 只有文档 |
| G5 状态检查名称正确 | 待启用：检查名为 **`verify`**（workflow `sample-mode` / job `verify`），见下方"下一步" |
| G6 不泄漏 | ✅ 无个人绝对路径、无凭据、无真实数据 |

## 未执行项与边界（不得改写成"通过"）

1. **Require status checks 尚未启用**：本轮只拿到"检查存在且为绿"的事实；把它设成必需是下一步动作（顺序约束见 `M2-plan.md` §4）。
2. **只跑了 ubuntu-latest**：没有 Windows / macOS 矩阵。本地 Windows（Python 3.12）跑同一命令也是绿的，但那是本地手工执行，不算 CI。
3. **CI 不验证论文数值**，也不碰真实 RESSET 数据；"真实数据完整重跑未执行"这一条仍然成立（见 `docs/VALIDATION.md` §5）。
4. artifact 只在 CI 中保留（默认 90 天），仓库里保存的是转写后的 `M2-results.json`。
