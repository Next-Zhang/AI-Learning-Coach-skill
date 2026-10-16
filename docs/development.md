# 开发指南

本项目通过 agent 编排学习流程，通过标准库 Python 脚本执行文件契约。修改运行规则时以 `SKILL.md` 和对应 `resources/` 契约为准；`.scratch/python-coach/` 是历史规格与票据。

## 脚本职责

所有脚本的 CLI 形态都是 `python -B scripts/<名称>.py <input.json> <output.json>`。

| 脚本 | 操作 / 输入 | 对学习状态的影响 | 契约 |
| --- | --- | --- | --- |
| `retrieve.py` | `query`，可合并 `web_results` | 只读资料，输出关键词检索结果；自身不联网 | [retrieval](../resources/retrieval-contract.md) |
| `completion.py` | `agent_score`、`self_score`、可选 `difficulty` | 纯计算，仅写输出 JSON | [completion](../resources/completion-contract.md) |
| `profile.py` | `onboarding` / `placement` / `acceptance` / `review` | 更新画像与能力矩阵；新增通道使用 `add_new: true` | [profile](../resources/profile-contract.md) |
| `schedule.py` | `due` / `add` / `record` | `due` 只读；`add`、`record` 更新调度表 | [schedule](../resources/schedule-contract.md) |
| `page.py` | `plan_path`、`day`、可选 `knowledge` | 读取计划与来源，生成 HTML 和报告 JSON | [page](../resources/page-contract.md) |
| `review.py` | `generate` / `query` / `append` | 生成、查询或追加快查文档；不会自动执行 `schedule_add` | [review](../resources/review-contract.md) |
| `check.py` | 计划、画像、可选进度 / 决策日志 / 当日写回清单 | 只读核对，输出问题清单 | [check](../resources/check-contract.md) |

“只读”表示不修改学习状态，脚本仍会写出输出 JSON。`check.py` 成功执行可以返回退出码 0 且报告 `ok: false`，调用方须读取 `ok`、`problems` 和 `summary`。

## 路径解析

- CLI 的脚本路径、输入 JSON 路径、输出 JSON 路径由当前工作目录解析。
- JSON 内的数据路径字段相对于**输入 JSON 所在目录**解析，包括 `plan_path`、`profile_path`、`sources_dir`、`schedule_path`、`review_path`、`output_dir`。
- 计划内的本地来源路径相对于 **plan.md 所在目录**解析，例如 `sources/python-basics.md`。
- 使用阶段显式指定数据路径，不依赖默认值；不确定基准时使用绝对路径。Windows JSON 路径可用 `/`，或将反斜杠写为 `\\`。

例如，输入文件位于 `.python-coach/tmp/page-in.json`：

```json
{
  "plan_path": "../state/plan.md",
  "day": "Day 1",
  "output_dir": "pages"
}
```

在学习工作区运行（把脚本位置替换成实际安装路径）：

```powershell
python -B <skill安装路径>/scripts/page.py .python-coach/tmp/page-in.json .python-coach/tmp/page-out.json
```

HTML 输出到 `.python-coach/tmp/pages/`，具体文件路径见输出 JSON 的 `html_path`。执行页即使位于 `tmp/`，也须保留到学习者明确批准删除。

## 不修改学习状态的最小示例

在仓库根目录执行以下 PowerShell 命令（使用 UTF-8 无 BOM，兼容 Windows PowerShell 5.1）：

```powershell
New-Item -ItemType Directory -Force scripts/testdata/_out | Out-Null
$completionInput = Join-Path (Get-Location) 'scripts/testdata/_out/readme-completion-in.json'
[System.IO.File]::WriteAllText($completionInput, '{"agent_score":5,"self_score":3,"difficulty":"刚好"}', [System.Text.UTF8Encoding]::new($false))
python -B scripts/completion.py scripts/testdata/_out/readme-completion-in.json scripts/testdata/_out/readme-completion-out.json
Get-Content -Encoding UTF8 scripts/testdata/_out/readme-completion-out.json
```

预期 `raw` 为 `4.4`、`score` 为 `4.5`、`score_display` 为 `4.5/5`，难度反馈单独返回。

## 测试与维护

需要 Python 3.12+，当前已在 3.12.14 上通过 225 项测试。全部测试：

```powershell
python -B -m unittest discover -s scripts -p "test_*.py"
```

单个模块：

```powershell
python -B scripts/test_profile.py
```

测试通过输入 / 输出文件验证外部行为，静态夹具在 `scripts/testdata/`，运行输出在 `_out/`。测试会改写共享输出目录，应串行运行。错误输入测试会故意触发 stderr 提示，以最终 `OK` 和退出码判断结果。

修改文件格式或脚本行为时，同步更新对应契约、模板和契约测试。问卷、目标澄清、摸底、计划评审、每日教学与验收对话主要依赖人工演练；脚本回归不代表这些交互已验证。

## 分发边界

分发清单见 [README](../README.md#安装与开始使用)。保留运行所需相对目录结构、测试夹具、README 和 LICENSE，排除 `.git/`、`.scratch/`、`__pycache__/`、`scripts/testdata/_out/` 与 `.python-coach/`。

学习期间脚本禁止写字节码，数据落在学习者工作区。开发期间可以修改技能源码；学习数据确认规则适用于教练运行时，仓库维护按本次用户授权执行。

原始规格和票据保留在 `.scratch/python-coach/`，避免移动导致历史引用失效。设计取舍见 [ADR](adr/)，待解决问题见 [审查记录](maintenance-review.md)。
