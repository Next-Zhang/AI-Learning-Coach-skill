# 间隔重复调度契约（ticket 03）

v0 复习调度实现 `scripts/schedule.py`——统一契约：**考察结果/新知识点 → 下次复习日**，按艾宾浩斯间隔 1→3→7→15→30 天推进。脚本以「读输入文件 → 写输出文件」形式提供，纯 Python 标准库、无外部依赖，可在任意工作目录运行；调度表（`review/schedule.md`）由本脚本**原地读写**。

本契约是技能内接口：agent 每学习日开头查到期知识点（`due`），考察后记录结果（`record`），课后把新知识点纳入调度（`add`）。调度推进规则与数据格式约定见 `resources/data-formats.md` §6。

---

## 1. 用法

```bash
python scripts/schedule.py <input.json> <output.json>
```

- 退出码：`0` 成功；`1` 调度失败（输入文件缺失/JSON 非法/缺 op/today 非法/知识点不在表中/调度表不存在等）；`2` 参数个数不对。
- 失败信息写到 stderr。
- `add` / `record` 除写输出 JSON 外，还会**原地改写** `schedule_path` 指向的调度表文件。

## 2. 输入文件（JSON）

```json
{
  "today": "2026-08-21",
  "schedule_path": "review/schedule.md",
  "op": "record",
  "topic": "pandas.Series",
  "result": "pass"
}
```

| 字段 | op | 必填 | 说明 |
| --- | --- | --- | --- |
| `op` | 全部 | 是 | `"due"`（查到期）/ `"add"`（新增知识点）/ `"record"`（记录考察结果）。 |
| `today` | 全部 | 否 | 基准日期 `YYYY-MM-DD`，默认系统日期。用于计算下次复习日与判断到期。 |
| `schedule_path` | 全部 | 否 | 调度表路径，默认 `review/schedule.md`。**相对路径以输入文件所在目录为基准**解析（写在工作目录的输入文件配 `"schedule_path": "review/schedule.md"` 即可）。 |
| `topic` | add, record | 是 | 知识点名。不能为空、不能含 `\|` 或换行（表格格式约束）。 |
| `mastery` | add | 否 | 初始掌握度 1–5，默认 2.0；超出范围自动截断。 |
| `result` | record | 是 | 考察结果：`"pass"`（通过）或 `"fail"`（未通过）。 |

## 3. 输出文件（JSON）

`due`：

```json
{
  "op": "due",
  "today": "2026-08-21",
  "due": [
    { "topic": "pandas.Series", "mastery": 2.0, "next_date": "2026-08-21", "interval": 1 }
  ]
}
```

`add` / `record`：

```json
{
  "op": "record",
  "today": "2026-08-21",
  "topic": "pandas.Series",
  "result": "pass",
  "row": { "topic": "pandas.Series", "mastery": 2.5, "next_date": "2026-08-24", "interval": 3 }
}
```

| 字段 | 说明 |
| --- | --- |
| `op` / `today` | 回显输入。 |
| `due` | 到期知识点列表（下次复习日 ≤ today），按 日期 → 知识点 排序；调度表不存在或为空时为空数组。 |
| `row` | 本次 add/record 影响的知识点行。 |
| `result` | record 时回显考察结果。 |

`mastery` 为 1–5 的数字（可含 0.5 档），与调度表 `x/5` 展示格式对应（如 `2.5` ↔ `2.5/5`）。

## 4. 间隔重复规则（艾宾浩斯）

- **间隔阶梯**：1 → 3 → 7 → 15 → 30 天，只进不退的下一档由 `LADDER` 决定。
- **考察通过（pass）**：掌握度 +0.5（上限 5）；间隔推进到下一档（已在 30 天档则保持 30）；下次复习日 = today + 新间隔。
- **考察未通过（fail）**：掌握度 -0.5（下限 1）；间隔**重置回 1 天**；下次复习日 = today + 1。
- 掌握度增减量（`PASS_MASTERY_DELTA` / `FAIL_MASTERY_DELTA`）与 0.5 粒度对齐能力矩阵（`profile.md`），可调整但需同步修改文档与测试。
- 本表是**调度视图**，`profile.md` 能力矩阵是权威掌握度；两处写回用同一规则保持同步（复习得分写回矩阵由 ticket 05 脚本负责）。

## 5. 调度表文件格式（review/schedule.md）

```markdown
---
updated: 2026-08-21
---

# 复习调度表

| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |
| --- | --- | --- | --- |
| pandas.Series | 2.5/5 | 2026-08-24 | 3 |
| pandas.DataFrame | 3/5 | 2026-08-24 | 3 |
```

- **读写语义**：`due` 只读；`add`/`record` 原地改写同一文件——保持既有行顺序、新增行追加在末尾、frontmatter `updated` 更新为 today。文件不存在时：`due` 视为无到期（返回空）、`add` 创建文件、`record` 报错。
- **容错**：无 frontmatter 也可解析（写回时补齐）；表格中个别无法解析的行（掌握度/日期/间隔非法、单元格数不对）被跳过，不拖垮整体。
- **日期**：统一 `YYYY-MM-DD`；输入 `today` 自动规范补零。
- agent 只查本表决定复习什么，不扫描 `review/` 全部文档（性能护栏，见 CONTEXT.md「调度表」）。

## 6. 测试

```bash
python scripts/test_schedule.py        # 全部测试（Python unittest）
```

- 样例夹具在 `scripts/testdata/`：`schedule/`（调度表夹具，含边界/坏行/无 frontmatter/完整阶梯）、`input/`（场景输入）、`_out/`（运行输出与可写调度表副本，已 gitignore）。
- 覆盖：调度表解析与写回格式（含容错）、到期查询（边界日/空表/缺文件）、间隔推进全阶梯 1→3→7→15→30（30 保持）、通过/未通过、掌握度上下限（5/1）、add（新建/默认掌握度/重复/非法名）、错误处理、CLI 退出码。
- 测试 seam 与断言方式遵循 spec「测试 seam」章节：以样例输入文件驱动脚本，断言输出文件内容；涉及写回的用例另断言调度表原文。

## 7. 用法示例（agent 流程）

1. **会话开头查到期**：`op=due`，`today=今天` → 拿到到期知识点列表，逐一考察。
2. **考察后记录**：`op=record`，`topic=…`，`result=pass|fail` → 调度表推进、下次复习日更新。
3. **课后纳入新知识点**：`op=add`，`topic=…`，`mastery=<能力矩阵当前值>` → 明天起按 1 天间隔复习。
