# 复习快查文档契约（ticket 13）

v0 复习快查文档实现 `scripts/review.py`——统一契约：**课程结束的沉淀**——按课程一份生成快查文档（`.python-coach/state/review/NN-主题.md`）+ 按知识点/日期查阅 + 为调度表更新准备新增知识点 + 向当日课追加新知识点行（批次 4 显式新增通道的三同步之一）。脚本以「读输入文件 → 写输出文件」形式提供，纯 Python 标准库、无外部依赖，可在任意工作目录运行；`generate` 原地写 `.python-coach/state/review/` 下的快查文档，`query` 只读，`append` 原地追加一行到当日课文档。

六件套正式文件均在 `.python-coach/state/`，路径约定与过程文件（`.python-coach/tmp/`，当日验收完成即清）见 `resources/data-formats.md` 开头「工作区目录结构」。

本契约是技能内接口：每节课（每日任务）结束、当日总结写入 `progress.md` 后（见 `resources/acceptance-contract.md`），agent 生成当日课程的快查文档，并把课程新知识点纳入调度表（`scripts/schedule.py` `op=add`）。写 `.python-coach/state/review/` 下文档属持久层修改，执行前先经学习者确认（护栏 approval）。

---

## 1. 文档格式（review/NN-主题.md，data-formats.md §5）

```markdown
---
course: 03
date: 2026-08-23
topics: [pandas.Series, pandas.DataFrame]
---

# 03 — pandas Series 与 DataFrame

- **Series**：一维带标签数组。`s = pd.Series([1, 2, 3])`；常见坑：索引不连续时 `s[0]` 按位置取，标签恰为 0 时按标签取，易混；优先用 `s.iloc[0]` / `s.loc[0]`。来源：sources/pandas-series.md。
```

- **frontmatter**：`course`（两位编号 `NN`）、`date`（`YYYY-MM-DD`）、`topics`（知识点标签数组）；三个字段即「按课程 / 按日期 / 按知识点」的查阅索引。
- **H1**：`# NN — 课程主题`。
- **正文**：每个知识点一行——`- **知识点**：概念一句话。`关键代码`；常见坑：坑；来源：引用。`（行内代码紧随概念，**不带「示例：」标签**，与 `templates/review-sheet.md` 同构）；无示例/常见坑时对应段省略（`concept` 后直接 `；来源：…`）。
- 用户可读优先：术语用中文解释，代码简短可运行；`review/schedule.md` 是调度表、不是快查文档。

## 2. 用法

```bash
python scripts/review.py <input.json> <output.json>
```

- 退出码：`0` 成功；`1` 处理失败（输入文件缺失/JSON 非法/缺 op/字段非法/知识点无来源/文档已存在且未带 overwrite 等）；`2` 参数个数不对。
- 失败信息写到 stderr。

## 3. 操作一：generate —— 生成快查文档

### 3.1 输入

```json
{
  "op": "generate",
  "review_path": "review",
  "course": 3,
  "title": "pandas Series 与 DataFrame",
  "date": "2026-08-23",
  "topics": ["pandas.Series", "pandas.DataFrame"],
  "overwrite": false,
  "points": [
    {
      "topic": "Series",
      "concept": "一维带标签数组",
      "example": "s = pd.Series([1, 2, 3])",
      "pitfall": "索引不连续时 s[0] 按位置取，标签恰为 0 时按标签取，易混；优先用 s.iloc[0] / s.loc[0]",
      "source": "sources/pandas-series.md",
      "mastery": 2.5
    }
  ]
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `op` | 是 | `"generate"`。 |
| `review_path` | 否 | 快查文档目录，默认 `review`。**相对路径以输入文件所在目录为基准**解析（写在工作目录的输入文件配 `"review_path": "review"` 即可）。使用阶段 agent 一律**显式传** `.python-coach/state/review`。 |
| `course` | 是 | 课程编号，1–99（文件名两位编号）。 |
| `title` | 是 | 课程主题；用于 H1 与文件名（`NN-主题.md`）。 |
| `date` | 否 | 课程日期 `YYYY-MM-DD`，默认系统日期，自动规范补零。 |
| `topics` | 否 | 知识点标签数组（出现在 frontmatter，供按知识点查阅）。缺省为空数组。 |
| `overwrite` | 否 | 默认 `false`——同课程文档已存在时报错（「按课程一份」不静默覆盖）。确需重写才置 `true`（属持久层修改，agent 须先确认）。 |
| `points` | 是 | 知识点数组，**至少一项**；每项字段见下。 |

`points` 每项字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `topic` | 是 | 知识点名。不能为空、不能含 `\|` 或换行（快查卡行/调度表格式约束）。 |
| `concept` | 是 | 概念一句话。 |
| `example` | 否 | 关键代码/示例（渲染为行内代码）。 |
| `pitfall` | 否 | 常见坑。 |
| `source` | 是 | 来源引用（`sources/` 文件名或 URL）。**缺来源即无依据，禁止落盘**（护栏「引用规范」）；不能含 `\|` 或换行。 |
| `mastery` | 否 | 该知识点初始掌握度 1–5，自动**规范化到 0.5 档**（半向上舍入，如 2.7 → 2.5）并截断到 [1,5]，默认 2.0；只进入 `schedule_add` 建议，**不写入文档正文**。 |

### 3.2 输出

```json
{
  "op": "generate",
  "review_path": "C:/…/review",
  "course": 3,
  "course_label": "03",
  "title": "pandas Series 与 DataFrame",
  "date": "2026-08-23",
  "topics": ["pandas.Series", "pandas.DataFrame"],
  "filename": "03-pandas-series-与-dataframe.md",
  "file_path": "C:/…/review/03-pandas-series-与-dataframe.md",
  "line_count": 1,
  "points": [
    { "topic": "Series", "concept": "一维带标签数组", "example": "…", "pitfall": "…", "source": "sources/pandas-series.md" }
  ],
  "schedule_add": [ { "topic": "Series", "mastery": 2.5 } ]
}
```

| 字段 | 说明 |
| --- | --- |
| `review_path` / `file_path` / `filename` | 目录与生成文件的绝对路径（resolve 后）与文件名。 |
| `course` / `course_label` | 课程编号（数字）与两位编号（`"03"`）。 |
| `date` / `topics` / `points` | 归一化后的课程信息与知识点。 |
| `line_count` | 知识点数（= 文档知识点行数）。 |
| `schedule_add` | **调度表更新建议**：`[{topic, mastery}]`，按「知识点 → 掌握度 → 下次复习日」接线用的新增清单（见 §6）。 |

文件名 `NN-主题.md`：`course` 两位前导零 + 主题 slug（小写 ASCII、中文保留、空格与标点折叠为连字符，如 `pandas Series 与 DataFrame` → `pandas-series-与-dataframe`）。

## 4. 操作二：query —— 按知识点 / 日期查阅（只读）

### 4.1 输入

```json
{
  "op": "query",
  "review_path": "review",
  "query": "Series",
  "date": "2026-08-23"
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `op` | 是 | `"query"`。 |
| `review_path` | 否 | 快查文档目录，默认 `review`（解析规则同 §3.1）。 |
| `query` | 否 | 知识点关键词；命中文档标题 / `topics` / 任一行文本（大小写不敏感子串）。缺省/空串不按关键词过滤。 |
| `date` | 否 | 按日期过滤（frontmatter `date` 匹配；文档日期与查询日期都**规范为 `YYYY-MM-DD` 后比较**，手写 `2026-8-23` 也能命中 `2026-08-23`）。 |

不设过滤 → 列出全部快查文档（相当于「浏览索引」）。**本操作只读，不改写任何文件。**

### 4.2 输出

```json
{
  "op": "query",
  "query": "Series",
  "date": null,
  "total_docs": 1,
  "matches": [
    {
      "file": "03-pandas-series.md",
      "path": "C:/…/review/03-pandas-series.md",
      "course": 3,
      "date": "2026-08-23",
      "topics": ["pandas.Series", "pandas.DataFrame"],
      "title": "03 — pandas Series 与 DataFrame",
      "points": [
        { "topic": "Series", "text": "- **Series**：一维带标签数组。`s = pd.Series([1, 2, 3])`；常见坑：…；来源：sources/pandas-series.md。", "source": "sources/pandas-series.md" }
      ]
    }
  ]
}
```

| 字段 | 说明 |
| --- | --- |
| `query` / `date` | 回显过滤条件（date 缺省为 `null`）。 |
| `total_docs` | 命中的文档数（无目录/无命中为 0，不报错）。 |
| `matches` | 命中文档数组，按 `course → 文件名` 排序；每项含文档元数据与逐行解析的知识点（`points[].text` 为原始行、`source` 从行尾「来源：」提取，提取不到为 `null`）。 |

**排除项**：`review/schedule.md` 是调度表，不视为快查文档，永远不参与查阅。个别不可读/无 `- **…**：` 行的文档容错跳过（不从错误中断整体）。

## 5. 操作三：append —— 向当日课追加新知识点行（批次 4 显式新增通道）

新知识点**无独立课程归属**（学习中途冒出、不在能力矩阵、经学习者确认加入）：挂当日课——在当日课程的 `review/NN-主题.md` **末尾追加一行** `- **topic**：…`，并把 topic 并入 frontmatter `topics`（不在则加，供按知识点查阅）。本操作只改快查文档；调度表与画像分别由 `scripts/schedule.py op=add`、`scripts/profile.py`（`add_new: true`）完成（三同步，流程见 `resources/acceptance-contract.md` §6）。

### 5.1 输入

```json
{
  "op": "append",
  "review_path": "review",
  "course": 3,
  "topic": "pandas.merge",
  "concept": "按键合并两个 DataFrame",
  "example": "pd.merge(df1, df2, on='key')",
  "pitfall": "默认内连接；一对多会复制行",
  "source": "sources/pandas-series.md"
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `op` | 是 | `"append"`。 |
| `review_path` | 否 | 快查文档目录，默认 `review`（解析规则同 §3.1）。使用阶段 agent 一律**显式传** `.python-coach/state/review`。 |
| `course` | 是 | 当日课程编号，1–99；定位 `NN-*.md`（该课程文档须已 `generate`，否则报错；存在多份时报错）。 |
| `topic` | 是 | 新知识点名。不能为空、不能含 `\|` 或换行；**该课程文档中已存在同知识点 → 报错**（不重复追加）。 |
| `concept` | 是 | 概念一句话。 |
| `example` | 否 | 关键代码/示例（渲染为行内代码）。 |
| `pitfall` | 否 | 常见坑。 |
| `source` | 是 | 来源引用；**缺来源即无依据，禁止落盘**（护栏「引用规范」）；不能含 `\|` 或换行。 |

### 5.2 输出

```json
{
  "op": "append",
  "review_path": "C:/…/review",
  "course": 3,
  "course_label": "03",
  "filename": "03-pandas-series-与-dataframe.md",
  "file_path": "C:/…/review/03-pandas-series-与-dataframe.md",
  "added_topic": "pandas.merge",
  "topics": ["pandas.Series", "pandas.DataFrame", "pandas.merge"],
  "line_count": 3,
  "point": { "topic": "pandas.merge", "concept": "…", "example": "…", "pitfall": "…", "source": "sources/pandas-series.md" }
}
```

| 字段 | 说明 |
| --- | --- |
| `filename` / `file_path` | 被追加文档的绝对路径与文件名。 |
| `added_topic` | 本次追加的知识点。 |
| `topics` | 追加后 frontmatter `topics` 数组（新知识点已并入）。 |
| `line_count` | 追加后文档的知识点行数。 |
| `point` | 归一化后的知识点（示例/常见坑缺省为空串）。 |

- 文档正文只**追加一行**，原行与顺序保持；frontmatter `course`/`date` 保持原值。
- 写盘属持久层修改，执行前先经学习者确认（护栏 approval；三同步由 agent 一并说明）。

## 6. 调度表更新（知识点 → 掌握度 → 下次复习日）

每节课结束的「调度表更新」由 `generate` 输出 `schedule_add` + `scripts/schedule.py` `op=add` 两步完成（ticket 13 与 ticket 03 分工：`review.py` 负责快查文档并产出建议，`schedule.py` 是调度表唯一写手；测试见 `scripts/test_review.py` 的 `ScheduleIntegrationTest`）：

1. 对 `schedule_add` 内每个新知识点调 `scripts/schedule.py`，`op=add`，`topic`、`mastery=schedule_add[].mastery`（**掌握度取该知识点在 `profile.md` 能力矩阵的当前值**，`generate` 输入未给 `mastery` 时默认 2.0 提示值）→ 调度表新增一行：掌握度 / 下次复习日（today+1）/ 当前间隔 1。
2. **已**在调度表中的知识点不重复 `add`（`schedule.py` 会报「已在调度表中」）——只在现有行上做推进（复习考察 `record`）；`add`/`record` 会改写 `review/schedule.md`，执行前先经学习者确认（护栏 approval）。
3. `schedule_add` 的 `mastery` 只是「建议/回显」，agent 应核对能力矩阵当前值后传给 `schedule.py`，两处保持一致（矩阵为权威值，见 `resources/data-formats.md` §6）。

## 7. 与 progress.md、schedule.md 的职责分离

- `review/*.md`：**每节课的知识沉淀**——用户可读、按知识点/按日期直接查阅（本脚本 `query`）；agent 出考察题的依据、学习者自主复习的索引。
- `progress.md`：**每日总结叙事**（ticket 12 追加）——当天的过程、完成度、难度反馈、证据摘要；不是知识点索引。
- `review/schedule.md`：**调度视图**（ticket 03）——知识点 → 掌握度 → 下次复习日；agent **只查调度表**决定复习什么，不扫描全部快查文档（性能护栏，CONTEXT.md「调度表」），需要具体内容时才用 `query` 查阅。
- 三者相互独立：本脚本**不写** `progress.md`、不直接写调度表；生成与查阅都不改 `plan.md` / `profile.md`。

## 8. 测试

```bash
python scripts/test_review.py        # 全部测试（Python unittest）
```

- 样例夹具在 `scripts/testdata/`：`review/`（只读快查文档夹具，含一份 `schedule.md` 以验证不参与查阅）、`input/`（场景输入）、`_out/review/`（生成的文档副本，已 gitignore）。
- 覆盖：文档生成的行格式与 frontmatter（含仅概念/无示例无坑的省略段）、按课程一份与 overwrite 语义、默认目录解析、来源/知识点/日期/编号校验、按知识点与按日期查阅、调度表排除与排序、与 `schedule.py add` 的调度联动（`schedule_add` 实测落盘 `review/schedule.md`）、**append 当日课新增行**（追加行 + topics 并入 + 原行保持、无示例/无坑省略段、重复知识点拒绝、文档不存在报错、缺来源/概念报错、追加后可查阅）、错误处理、CLI 退出码。
- 测试 seam 与断言方式遵循 spec「测试 seam」章节：以样例输入文件驱动脚本，断言输出文件内容；生成/追加用例另断言写盘后的 `review/*.md` 原文。

## 9. 用法示例（agent 流程）

1. **课程收尾**：每日任务验收与当日总结（ticket 12）完成后，把当日课程各知识点整理为 `points`（概念 + 示例 + 常见坑 + 来源，来源不编造）→ 调本脚本 `op=generate` → 生成 `review/NN-主题.md`，拿到 `schedule_add`。
2. **纳入调度**：对 `schedule_add` 中不在调度表的知识点调 `scripts/schedule.py` `op=add`（掌握度取能力矩阵当前值）；已在表内的跳过。写回前经学习者确认。
3. **矩阵外新增（批次 4）**：验收/复习中学习者确认的新知识点 → 调本脚本 `op=append`（`course` 当日课、topic/concept/source 等）追加到当日课文档，配合 `profile.py add_new` 与 `schedule.py add` 完成三同步（流程见 `resources/acceptance-contract.md` §6）；确认后执行。
4. **查阅**：学习者/agent 想复习某知识点 → `op=query`（`query`=关键词 或 `date`=日期）→ 直接定位到对应文档与知识点行；agent 依据它出题考察（`resources/session-start-contract.md` §4）。
