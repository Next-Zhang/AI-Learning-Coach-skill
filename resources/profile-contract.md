# 画像更新契约（ticket 05）

v0 用户画像增量更新实现 `scripts/profile.py`——统一契约：**onboarding 问卷结果 / 摸底测试结果 / 验收完成度 / 复习考察得分 → 能力矩阵（领域 → 子领域 → 知识点/能力）**。脚本以「读输入文件 → 写输出文件」形式提供，纯 Python 标准库、无外部依赖，可在任意工作目录运行；画像文件（`.python-coach/state/profile.md`）由本脚本**原地读写**。

六件套正式文件均在 `.python-coach/state/`，路径约定与过程文件（`.python-coach/tmp/`，阶段完成即清）见 `resources/data-formats.md` 开头「工作区目录结构」：调用本脚本时 agent 一律**显式传** `profile_path=.python-coach/state/profile.md`。

本契约是技能内接口：起步流程把 onboarding 问卷写入画像初值（`onboarding`），摸底测试初始化能力矩阵（`placement`，含前置能力评估）；每日验收后把完成度写回能力矩阵、难度反馈留痕（`acceptance`）；复习考察后把得分写回能力矩阵（`review`）。更新规则与数据格式约定见 `resources/data-formats.md` §3。

---

## 1. 用法

```bash
python scripts/profile.py <input.json> <output.json>
```

- 退出码：`0` 成功；`1` 画像更新失败（输入文件缺失/JSON 非法/缺 op/date 非法/问卷字段缺失或非法/知识点不在矩阵/画像文件不存在等）；`2` 参数个数不对。
- 失败信息写到 stderr。
- 四种操作会**原地改写** `profile_path` 指向的画像文件（能力矩阵行、增量记录与 frontmatter `updated`），属持久层修改，执行前先经学习者确认（护栏 approval，见 SKILL.md「护栏」）。

## 2. 输入文件（JSON）

```json
{
  "date": "2026-08-21",
  "profile_path": "profile.md",
  "op": "acceptance",
  "topic": "pandas.Series",
  "score": 4,
  "difficulty": "刚好",
  "source": "验收 Day 1"
}
```

| 字段 | op | 必填 | 说明 |
| --- | --- | --- | --- |
| `op` | 全部 | 是 | `"onboarding"`（问卷入画像初值）/ `"placement"`（摸底测试初始化能力矩阵）/ `"acceptance"`（验收结果）/ `"review"`（复习考察结果）。 |
| `date` | 全部 | 否 | 基准日期 `YYYY-MM-DD`，默认系统日期。写入矩阵行的更新时间与增量记录日期。 |
| `profile_path` | 全部 | 否 | 画像路径，默认 `profile.md`。**相对路径以输入文件所在目录为基准**解析。使用阶段 agent 一律**显式传** `.python-coach/state/profile.md`。 |
| `answers` | onboarding | 是 | 8 题问卷答案对象，键为固定 8 项字段名（见 §6）；缺字段/含未知字段报错。 |
| `results` | placement | 是 | 摸底测试合成结果数组。知识点行 `[{topic, score}]`（兼容旧格式，type 缺省为 `"知识点"`）或 `[{topic, type: "知识点", score, domain?, subdomain?}]`；能力行 `[{topic, type: "能力", pre_status: "具备"\|"未具备", domain?, subdomain?}]`。`topic` 非空且不能重复；`score` 为数字（水平分 1–5，0.5 档）；能力行 `score` 不可用、`pre_status` 必填。 |
| `topic` | acceptance, review | 是 | 知识点名。不能为空、不能含 `\|` 或换行（表格格式约束）。默认须已存在于能力矩阵（先经摸底测试初始化）；**矩阵外 topic 走显式新增通道**（见 `add_new`）。**只接受知识点行**——能力行无水平分，不接受验收/复习增量（新增通道的能力行除外，见 §4）。 |
| `add_new` | acceptance, review | 否 | **显式新增通道开关（批次 4）**：topic 不在能力矩阵时默认报错（矩阵由摸底测试初始化）；置 `true`（agent 已征得学习者确认）→ 新建矩阵行。对矩阵内 topic 无影响（走正常增量）。 |
| `type` | acceptance, review | 否 | 新增行类型：`"知识点"`（默认）\| `"能力"`；仅新增通道生效。 |
| `domain` / `subdomain` | acceptance, review | 否 | 新增行的领域/子领域分层归属（如 数据分析/pandas）；仅新增通道生效，缺省为空。 |
| `pre_status` | acceptance, review | 否 | 新增**能力行**必填：`"具备" \| "未具备"`（水平分恒为 —）；仅新增通道生效。 |
| `score` | acceptance | 是 | 验收完成度分（由 `scripts/completion.py` 合成，1–5，可含 0.5 档）；超出范围自动截断到 [1, 5]。 |
| `difficulty` | acceptance | 否 | 难度反馈，封闭集合 `"太难" \| "刚好" \| "太简单"`；**独立记录，不影响矩阵数值**；缺省不记录。非法值报错。 |
| `result` | review | 是 | 复习考察结果：`"pass"`（通过）或 `"fail"`（未通过）。 |
| `source` | acceptance, review | 否 | 矩阵「来源」列文本与日志事件名；缺省时 acceptance 用 `"验收"`、review 用 `"复习考察"`。 |

`onboarding` 输入示例：

```json
{
  "op": "onboarding",
  "answers": {
    "学习目标": "用 Python 做数据分析",
    "Python 水平自评（1–5）": 2,
    "每日时间预算": "1 小时",
    "学习风格偏好": "视频 + 动手练习",
    "压力承受自评（1–5）": 3,
    "期望节奏": "平缓",
    "过往经历": "无编程经验",
    "复习意愿": "愿意每天 10 分钟"
  }
}
```

`placement` 输入示例（知识点行 + 能力行混合）：

```json
{
  "op": "placement",
  "date": "2026-08-20",
  "results": [
    { "topic": "pandas.Series", "score": 1.5, "domain": "数据分析", "subdomain": "pandas" },
    { "topic": "Python 工程组织", "type": "能力", "pre_status": "未具备", "domain": "工程", "subdomain": "工程素养" },
    { "topic": "OOP 类与对象", "type": "知识点", "score": 1, "domain": "编程基础", "subdomain": "面向对象" }
  ]
}
```

## 3. 输出文件（JSON）

`placement`：

```json
{
  "op": "placement",
  "date": "2026-08-20",
  "matrix": [
    { "topic": "pandas.Series", "type": "知识点", "score": 1.5, "pre_status": "—", "domain": "数据分析", "subdomain": "pandas", "date": "2026-08-20", "source": "摸底测试" },
    { "topic": "Python 工程组织", "type": "能力", "score": null, "pre_status": "未具备", "domain": "工程", "subdomain": "工程素养", "date": "2026-08-20", "source": "摸底测试" }
  ],
  "count": 2,
  "created": "2026-08-19",
  "log_entry": "- 2026-08-20：摸底测试 → 初始矩阵"
}
```

`acceptance` / `review`：

```json
{
  "op": "acceptance",
  "date": "2026-08-21",
  "topic": "pandas.Series",
  "score": 4,
  "difficulty": "刚好",
  "source": "验收 Day 1",
  "old_score": 1.5,
  "new_score": 2.0,
  "delta": 0.5,
  "updated": true,
  "log_entry": "- 2026-08-21：验收 Day 1（完成度 4，难度 刚好）→ pandas.Series +0.5（1.5→2）"
}
```

| 字段 | 说明 |
| --- | --- |
| `op` / `date` | 回显输入。 |
| `matrix` | 仅 `placement`：规范化后的矩阵行数组（`topic` / `type` / `score` / `pre_status` / `domain` / `subdomain` / `date` / `source`；知识点行 `score` 已 0.5 档舍入并截断 [1, 5]、`pre_status = —`，能力行 `score = null`、`pre_status = 具备\|未具备`）。 |
| `count` | 仅 `placement`：写入的行个数（知识点 + 能力）。 |
| `created` | 仅 `placement`：画像创建日（本次新建时为 date）。 |
| `log_entry` | 追加进增量记录的单行文本（placement 为「摸底测试 → 初始矩阵」；验收含难度反馈；新增通道为「→ 新增知识点 X（水平 Y）」/「→ 新增能力 X（前置状态 …）」）。 |
| `added` | 仅显式新增通道：`true` 表示本次为矩阵外**新增行**（`old_score`/`delta` 为 `null`、`updated = true`）；正常增量路径无此字段。 |
| `topic` / `score` / `difficulty` / `result` / `source` | 回显输入（`score` 已截断；`difficulty` 未提供时为 `null`）。 |
| `old_score` / `new_score` | 矩阵该知识点更新前后的水平分（新增通道：`old_score = null`、`new_score` = 初值，能力行为 `null`）。 |
| `delta` | 水平分变化量（`0.5` / `-0.5` / `0.0`；新增通道为 `null`）。 |
| `updated` | 是否发生了数值变化（验收未达阈值、或已达 5 上限 / 1 下限时 `false`；新增通道恒 `true`）。 |
| `answers` / `created` / `updated` | 仅 `onboarding`：规范化后的 8 题答案、画像创建日与更新日。 |

## 4. 能力矩阵增量更新规则

- **摸底（placement）**：`results` 内行**整体覆盖**为初始值（来源「摸底测试」、日期 = date）——知识点行写水平分（0.5 档半向上舍入 2.25 → 2.5、2.75 → 3.0 并截断 [1, 5]，合成公式见 `resources/placement-contract.md` §6）；能力行写前置状态（`具备 | 未具备`，水平分 = —，来自摸底前置能力评估题组）。不在 `results` 中的既有行保留；画像文件不存在时自动创建（与 onboarding 相同）。增量记录追加一条「摸底测试 → 初始矩阵」。**重走起步重新摸底时**：`results` 内行会被**重置**为新摸底结果（覆盖该行此前的验收/复习增量或前置状态；历史仍保留在增量记录中）——写前须明确告知学习者这一语义，经确认后才写（护栏 approval）。
- **验收（acceptance）**：完成度分 `score ≥ 4` → 该知识点行水平分 `+0.5`，上限 5；`score < 4` → 矩阵数值不变（日志记录事件）。难度反馈独立记录在增量日志中，**不改变矩阵数值**（只影响后续计划难度档位，见 spec「完成度评分」）。
- **复习（review）**：通过（`pass`）→ `+0.5`，上限 5；未通过（`fail`）→ `-0.5`，下限 1。与 `scripts/schedule.py` 的掌握度推进**同一规则、同一增量**，两处写回保持同步（调度表是视图，能力矩阵是权威值，见 `resources/data-formats.md` §6）。
- 更新时矩阵行同步改写「更新时间 = date、来源 = source」，**领域/子领域/类型/前置状态保持原行**；数值未变时保持原行不动。
- 知识点不在能力矩阵中 → 默认报错（矩阵由摸底测试初始化，见 `resources/placement-contract.md`；先入矩阵再验收/复习）；**矩阵外显式新增通道（批次 4，决策 5）**：学习中冒出矩阵外新知识点时，agent 先暂停并向学习者说明、征得确认，确认后由输入 `add_new: true` 放行新建矩阵行——
  - 知识点行：水平分初值 = 验收完成度（0.5 档截断 [1, 5]）/ 复习**通过 2.0**（与 `schedule.py` 的 `add` 默认掌握度一致）/**未通过 1.0**；`pre_status = —`；来源默认 `验收新增` / `复习新增`（agent 通常显式传 `验收新增 Day N`）；
  - 能力行（`type = 能力`）：水平分 = —、`pre_status = 具备 | 未具备`（必填），来源同上；
  - 领域/子领域缺省为空，可用 `domain`/`subdomain` 显式给出；
  - 增量记录写「新增知识点 X（水平 Y）/ 新增能力 X（前置状态 …）」，输出带 `added: true`；
  - 通道与调度表 `schedule.py op=add`、快查文档 `review.py op=append` 构成**三同步**（`resources/acceptance-contract.md` §6），运行期留痕入 `state/decision-log.md`（决策 15）。
- **能力行不接受验收/复习增量**：`topic` 指向能力行（`type = 能力`）→ 报错（能力行无水平分，前置状态为二值，只在摸底/计划修订时更新）。

## 5. 画像文件格式（profile.md）

```markdown
---
created: 2026-08-19
updated: 2026-08-21
---

# 用户画像

## Onboarding 问卷（8 题）
- 学习目标：用 Python 做数据分析
- Python 水平自评（1–5）：2
- 每日时间预算：1 小时
- 学习风格偏好：视频 + 动手练习
- 压力承受自评（1–5）：3
- 期望节奏：平缓
- 过往经历：无编程经验
- 复习意愿：愿意每天 10 分钟

## 能力矩阵（领域 → 子领域 → 知识点/能力）
| 领域 | 子领域 | 知识点 | 类型 | 水平分 | 前置状态 | 更新时间 | 来源 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 数据分析 | pandas | pandas.Series | 知识点 | 2 | — | 2026-08-21 | 验收 Day 1 |
| 数据分析 | pandas | pandas.DataFrame | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |
| 工程 | 工程素养 | Python 工程组织 | 能力 | — | 未具备 | 2026-08-20 | 摸底测试 |

## 增量记录
- 2026-08-20：摸底测试 → 初始矩阵
- 2026-08-21：验收 Day 1（完成度 4，难度 刚好）→ pandas.Series +0.5（1.5→2）
```

- **读写语义**：四种操作都原地改写同一文件——矩阵行按知识点更新、日志**追加**在末尾、frontmatter `updated` 更新为 date。文件不存在时：`onboarding`/`placement` 创建文件，`acceptance`/`review` 报错。
- **容错**：无 frontmatter 也可解析（写回时补齐 `created`/`updated`）；矩阵中个别无法解析的行（单元格数不对、类型非法、水平分/日期非法）被跳过，不拖垮整体；**旧 4 列画像（`| 知识点 | 水平分 | 更新时间 | 来源 |`）解析容错**——视作知识点行（领域/子领域为空、前置状态 = —），写回时升级为新 8 列格式；无 Onboarding 区块时写回输出空占位（与 `templates/profile.md` 一致）。
- **日期**：统一 `YYYY-MM-DD`；输入 `date` 自动规范补零。
- 能力矩阵为唯一权威数据（与 `review/schedule.md` 掌握度共用同一知识点 × 评分，见 `resources/data-formats.md` §3）。

## 6. onboarding 固定 8 题

| 字段名（answers 键） | 类型 | 说明 |
| --- | --- | --- |
| `学习目标` | 文本 | 一句话学习目标。 |
| `Python 水平自评（1–5）` | 数字 | 超出 [1, 5] 自动截断。 |
| `每日时间预算` | 文本 | 如「1 小时」。 |
| `学习风格偏好` | 文本 | 如「视频 + 动手练习」。 |
| `压力承受自评（1–5）` | 数字 | 超出 [1, 5] 自动截断。 |
| `期望节奏` | 文本 | 如「平缓」。 |
| `过往经历` | 文本 | 如「无编程经验」。 |
| `复习意愿` | 文本 | 如「愿意每天 10 分钟」。 |

字段名保持稳定（`resources/data-formats.md` §3 约定）；新增字段需同步改脚本与测试。

## 7. 测试

```bash
python scripts/test_profile.py        # 全部测试（Python unittest）
```

- 样例夹具在 `scripts/testdata/`：`profile/`（画像夹具，含空模板/完整画像/无 frontmatter/坏行/上下限/能力行/旧 4 列格式）、`input/`（场景输入）、`_out/`（运行输出与可写画像副本，已 gitignore）。
- 覆盖：onboarding（创建文件/覆盖保留矩阵/8 题校验/数值截断/日志）、验收增量（≥4 加 0.5、<4 不变、上限 5、难度反馈记录且不改矩阵、能力行报错）、复习写回（通过/未通过/下限 1）、placement（创建/覆盖保留/0.5 舍入截断/能力行写前置状态/能力行缺 pre_status 与非法 type 报错/upsert 保留能力行）、旧 4 列画像容错（解析为知识点行、写回升级 8 列）、矩阵与日志原文格式、坏行容错、错误处理、CLI 退出码。
- 测试 seam 与断言方式遵循 spec「测试 seam」章节：以样例输入文件驱动脚本，断言输出文件内容；涉及写回的用例另断言画像原文。

## 8. 用法示例（agent 流程）

1. **起步 onboarding**：收集 8 题答案 → `op=onboarding` 写入画像初值（首次自动创建 `profile.md`）。
2. **起步摸底测试**：范围驱动的摸底测试判分并合成后 → `op=placement`（`results` 为合成后的知识点水平分 + 前置能力评估题组的能力行 `{type: "能力", pre_status}`）→ 初始化能力矩阵（来源「摸底测试」），见 `resources/placement-contract.md` §3.4/§6。
3. **每日验收后**：先 `scripts/completion.py` 合成完成度分（agent 7:3 自评）→ 再 `op=acceptance`（`topic` 当日知识点、`score` 完成度、`difficulty` 难度反馈）→ 能力矩阵增量修正，难度反馈入日志。
4. **复习考察后**：先 `scripts/schedule.py`（`op=record`）推进调度表 → 再 `op=review`（`topic`、`result=pass|fail`）把掌握度写回能力矩阵（两处同规则保持同步）。
5. **矩阵外新增通道（批次 4）**：写回前核对发现 topic 不在能力矩阵 → 暂停，向学习者说明并确认 → 确认后 `op=acceptance`/`op=review` 带 `add_new: true`（能力行另带 `type: "能力"` + `pre_status`）新建矩阵行，并配套 `scripts/schedule.py op=add` 与 `scripts/review.py op=append` 完成三同步（流程见 `resources/acceptance-contract.md` §6）；学习者拒绝则跳过该 topic 并记录（decision-log）。
6. **过程文件清理**（目录与时机见 `resources/data-formats.md`「工作区目录结构」）：本脚本的 in/out JSON 放 `.python-coach/tmp/`——`onboarding`/`placement` 的**起步完成即清**，`acceptance`/`review` 的**当日验收完成即清**。清理为 agent 内部动作，不需逐条向学习者确认。
