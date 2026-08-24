# 自动核对契约（修订批次 3，决策 4/16）

机械可判定部分的跨文件引用一致性校验 `scripts/check.py`——**计划（plan.md）↔ 能力矩阵（profile.md）↔ 进度证据（progress.md）↔ 决策日志（decision-log.md）** 之间的引用与口径核对。脚本以「读输入文件 → 写输出文件」形式提供，纯 Python 标准库、无外部依赖，**只读不改任何数据文件**（区别于 `profile.py`/`schedule.py` 的写回语义）。

自动核对是**混合机制**的一半（决策 4）：本脚本做**机械校验**（引用存在性、结构、口径一致），输出结构化问题清单；**语义校验**（证据是否真支撑目标、质量、教学合理性等）留在各流程契约的规则里（计划评审 `resources/plan-contract.md` §4、验收核查 `resources/acceptance-contract.md` §3），**不进脚本**。

---

## 1. 用法

```bash
python scripts/check.py <input.json> <output.json>
```

- 退出码：`0` 成功（**与是否发现问题无关**——脚本只报告，不硬阻塞）；`1` 核对失败（输入文件缺失/JSON 非法/day 找不到/acceptance_topics 缺 day 等操作级错误）；`2` 参数个数不对。
- 失败信息写到 stderr；`0` 时是否阻断由**调用它的流程契约**决定（见 §5）。
- 本脚本不原地改写任何数据文件；只写输出 JSON。

## 2. 输入文件（JSON）

```json
{
  "date": "2026-08-22",
  "plan_path": "../state/plan.md",
  "profile_path": "../state/profile.md",
  "progress_path": "../state/progress.md",
  "decision_log_path": "../state/decision-log.md",
  "day": "Day 1",
  "acceptance_topics": ["pandas.Series", "pandas.DataFrame"]
}
```

> 路径约定（`resources/data-formats.md` 开头「工作区目录结构」）：脚本 in/out JSON 放 `.python-coach/tmp/` 时，`plan_path` 等相对路径**以输入文件所在目录为基准**解析——从 `tmp/` 引用 `state/` 六件套用 `../state/…`，或用绝对路径；输出 JSON 同样写 `tmp/`。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `date` | 否 | 核对日期 `YYYY-MM-DD`，默认系统日期；仅写入输出回显，不参与判定。 |
| `plan_path` | 是* | 计划文件路径，默认 `plan.md`。**相对路径以输入文件所在目录为基准**解析；`plan.md` 缺失 → 操作级错误（退出码 1）。使用阶段 agent 一律**显式传** `.python-coach/state/plan.md`（六件套路径约定见 `resources/data-formats.md` 开头「工作区目录结构」）。 |
| `profile_path` | 是* | 画像文件路径，默认 `profile.md`；缺失 → 操作级错误。 |
| `progress_path` | 否 | 进度文件路径，默认 `progress.md`；**文件不存在时对应校验（`evidence_consistent`）跳过**并记入 `summary.skipped`（首次使用/尚无进度时正常）。 |
| `decision_log_path` | 否 | 决策日志路径，默认 `decision-log.md`；文件不存在时 `decision_log` 校验跳过（批次 4 引入该文件）。 |
| `day` | 否 | 作用域：`Day N` / `N` / `YYYY-MM-DD`（与 `scripts/page.py` 定位规则一致）。提供时 `plan_structure`/`plan_refs` 只查该天；找不到 → 操作级错误。 |
| `acceptance_topics` | 否 | 验收**写回前清单**（`resources/acceptance-contract.md` §6 场景）：将要写回的知识点数组。提供时必须同时提供 `day`，否则操作级错误。 |

\* 两个文件路径实际必填（默认值即指向它们）；缺文件为操作级错误，不会产出问题清单。

## 3. 输出文件（JSON）

```json
{
  "date": "2026-08-22",
  "ok": false,
  "problems": [
    {
      "level": "error",
      "check": "plan_refs",
      "day": "Day 1",
      "topic": "未知知识点",
      "message": "知识点 未知知识点 不在能力矩阵中"
    }
  ],
  "summary": {
    "checks_run": ["plan_structure", "plan_refs", "writeback_consistent"],
    "skipped": ["evidence_consistent", "decision_log"],
    "errors": 1,
    "warnings": 0
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `date` | 回显输入核对日期。 |
| `ok` | `summary.errors == 0`。**只作汇总标志，不代表"允许/禁止"**——是否阻断由调用契约决定。 |
| `problems` | 问题清单，按 出现顺序 排列；每项 `level`（`error`/`warning`）+ `check`（校验 id）+ `message`（可操作的中文说明），`day`/`topic` 为定位上下文（可有可无）。 |
| `summary.checks_run` | 实际执行的校验 id 列表。 |
| `summary.skipped` | 因对应文件缺失而跳过的校验 id。 |
| `summary.errors` / `summary.warnings` | 问题计数。 |

**level 语义**：`error` = 引用/结构/口径矛盾，需要修复（阻断与否见 §5）；`warning` = 结构建议、历史记录无法核对、格式提示等，不阻断，由 agent 判断处理或记录。

## 4. 校验范围（五类，机械可判定部分）

| check id | 校验内容 | error（需修复） | warning（不阻断） |
| --- | --- | --- | --- |
| `plan_structure` | plan.md 可解析、Day 区块字段齐备 | 无任何 Day 区块；Day 缺/非法日期（YYYY-MM-DD）；缺「知识点」行；缺「来源」行（来源为必需字段，`data-formats.md` §1） | 缺「主题」；缺「目标清单」；目标清单项不是 `- [ ]` checkbox |
| `plan_refs` | Day 的「知识点」「前置」引用 ⊆ 能力矩阵行 | 知识点不在矩阵；知识点**误引能力行**（计划知识点应为知识点行）；前置不在矩阵 | — |
| `writeback_consistent` | 验收写回 topic 与当日计划知识点口径一致（两路：画像增量记录「验收」事件 + 输入 `acceptance_topics` 写回前清单） | 验收事件/写回清单中的 topic 不在对应 plan Day 知识点中 | 画像验收记录日期不在计划中（无法核对）；写回清单未覆盖当日某知识点（如为有意遗漏可忽略） |
| `evidence_consistent` | progress.md 结构化证据条目的「→ 知识点」与对应 plan Day 知识点一致 | 证据知识点不在当日计划知识点中 | 证据条目缺 `→ 知识点` 引用；证据条目格式不符 `- [目标] 描述 → 知识点`；progress 日期不在计划中（无法核对） |
| `decision_log` | decision-log.md 可读、日期合法（批次 4 引入，缺失跳过） | 非空非注释行不是 `YYYY-MM-DD \| …` 或日期非法 | — |

**判定规则依赖**（不重复定义，只引用）：能力矩阵行结构与「知识点/能力」区分见 `resources/data-formats.md` §3 与 `scripts/profile.py`（解析复用其 `parse_profile`）；plan Day 字段与定位规则见 `data-formats.md` §1 与 `scripts/page.py`；progress 证据条目结构见 `data-formats.md` §2（决策 16）。

**显式新增通道例外（批次 4）**：`writeback_consistent` 跳过画像增量记录中「新增知识点 / 新增能力」行（来源「验收新增 …」）——那是学习者确认的矩阵外写回（`resources/acceptance-contract.md` §6 三同步），本就有意不在当日计划知识点中，不误报为口径错误；`plan_refs` 不因此受影响（矩阵内新行照常被引用）。

**明确不做**（语义部分，留在契约规则）：证据是否真支撑目标、目标清单 ↔ 知识点 的语义对齐（目标是否覆盖知识点、是否写范围外目标）、来源真实性、教学合理性——分别由计划评审（`plan-contract.md` §4）与验收核查（`acceptance-contract.md` §3）负责，脚本不判。

## 5. 三触发点与阻断语义

本脚本**不硬阻塞**（§1 退出码 0/1 只表脚本自身成败）；是否阻断由以下三个流程契约规定。三处调用统一放 `.python-coach/tmp/` 的 in/out JSON（过程文件，阶段完成即清，见 `resources/data-formats.md`「工作区目录结构」）。

| 触发点 | 调用方式 | 阻断语义 |
| --- | --- | --- |
| **计划落盘前**（`resources/plan-contract.md` §6） | 全量核对：`plan_path`/`profile_path` 显式传 `.python-coach/state/…`（progress/decision 缺失跳过） | `plan_refs`/`plan_structure` 的 **error → 不落盘**，修订后重跑至无 error；warning → 可落盘但修订说明里记录 |
| **每日行前**（`resources/session-start-contract.md` §2） | 带作用域：`day` = 当日，`plan_path`/`profile_path` 显式传 | 当日 `plan_refs`/`plan_structure` **error → 先修复再执行当日任务**（对齐矩阵行名或补矩阵行）；历史类问题（writeback/evidence 的历史记录）→ 记录、择机修复，不阻断当日 |
| **验收写回前**（`resources/acceptance-contract.md` §6） | 带清单：`day` = 当日 + `acceptance_topics` = 写回清单知识点 | `writeback_consistent` **error → 修正写回清单后再写回**（禁止把计划外 topic 写进矩阵）；warning（未覆盖）→ agent 判断（有意遗漏可忽略） |

## 6. 与既有脚本/流程的分工

- `scripts/page.py`：解析 plan.md 渲染当日网页（只读）；check.py 的 plan 解析与其口径一致但**独立实现**（check 需要「前置」行与结构严格性，page 只需容错渲染）。
- `scripts/profile.py`：能力矩阵的读写（onboarding/placement/acceptance/review）；check.py **只读**复用其 `parse_profile` 解析矩阵，不写回。
- 前置**缺口分级处置**（严重/轻度）是 `session-start-contract.md` §2 的 agent 侧判定（批次 2），check.py 只保证引用存在（矩阵外引用 → error），不替代缺口判定。

## 7. 测试

```bash
python scripts/test_check.py        # 全部测试（Python unittest）
```

- 样例夹具在 `scripts/testdata/`：`check/`（plan/profile/progress/decision-log 的正反夹具）、`input/`（场景输入）、`_out/check/`（运行输出，已 gitignore）。
- 覆盖：全量好数据全绿（五类全跑、skipped 为空）；全量坏数据逐类报错（矩阵外知识点/前置、知识点引能力行、日期非法、来源缺失、目标清单格式、验收写回不一致、证据不一致、决策日志坏行）；`day` 作用域（只查指定 Day）；`acceptance_topics` 一致/不一致；结构专用夹具；CLI 退出码（0/1/2）与操作级错误（缺 plan、day 找不到、acceptance_topics 缺 day）。
- 测试 seam 与断言方式遵循 spec「测试 seam」章节：以样例输入文件驱动脚本，断言输出文件内容与返回一致。

## 8. 过程文件清理

本脚本的 in/out JSON 放 `.python-coach/tmp/`，**所属阶段完成即清**（计划落盘后 / 当日验收完成后，目录与时机见 `resources/data-formats.md`「工作区目录结构」）。清理为 agent 内部动作，不需逐条向学习者确认。
