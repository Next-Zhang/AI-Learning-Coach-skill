# 当日执行网页生成契约（ticket 06）

v0 当日执行视图生成实现 `scripts/page.py`——统一契约：**plan.md + 当日任务 → 单文件静态 HTML**（自包含、可离线打开，含当日知识内容（概念+示例）、完整链路（目标→今日位置）、今日目标清单（对照范围声明）、参考来源链接）。脚本以「读输入文件 → 写输出文件」形式提供，纯 Python 标准库、无外部依赖，可在任意工作目录运行；只读 `plan.md` 与来源资料文件，不改写任何持久层数据文件。

本契约是技能内接口：每个学习日会话开始（spec「当日执行网页」、SKILL.md「会话开始」第 4 步）由 agent 生成当日执行网页，供学习者当日使用；验收完成、当日总结写入后，agent 提出删除、学习者确认后删除（approval 护栏），HTML 模板代码留在技能内可复用。与复习快查文档分工：网页 = 当日临时执行视图（用完即删），快查文档 = 持久知识沉淀。

---

## 1. 用法

```bash
python scripts/page.py <input.json> <output.json>
```

- 退出码：`0` 成功；`1` 生成失败（输入文件缺失/JSON 非法/缺 day/plan.md 不存在或没有 Day 区块/找不到当日任务/knowledge 类型非法等）；`2` 参数个数不对。
- 失败信息写到 stderr。
- 输出 HTML 写到 **系统临时目录**（`tempfile.gettempdir()`），可用 `output_dir` 覆盖；输出 JSON 报告 `html_path` 与当日任务解析结果。

## 2. 输入文件（JSON）

```json
{
  "plan_path": "plan.md",
  "day": "Day 1",
  "output_dir": null,
  "knowledge": [
    {
      "topic": "pandas.Series",
      "concept": "Series 是一维带标签数组……",
      "example": "s = pd.Series([1, 2, 3])\nprint(s)"
    }
  ]
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `plan_path` | 是 | 学习计划文件路径，默认 `plan.md`。**相对路径以输入文件所在目录为基准**解析。使用阶段 agent 一律**显式传** `.python-coach/state/plan.md`（六件套路径约定见 `resources/data-formats.md` 开头「工作区目录结构」）。 |
| `day` | 是 | 当日任务标识，三种写法均可：`"Day 1"` / `"1"`（按 Day 编号）或 `"2026-08-20"`（按日期）。找不到报错。 |
| `output_dir` | 否 | HTML 输出目录；**缺省时输出到系统临时目录**（ticket 06 要求）。相对路径以输入文件所在目录为基准解析。 |
| `knowledge` | 否 | agent 从检索层（`scripts/retrieve.py`）提炼的当日知识内容数组（概念+示例）；未提供时脚本读取当日任务「来源」引用的本地 `sources/` 文件正文作为知识内容（见 §4）。 |

`knowledge` 每项字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `topic` | 否 | 知识点名（渲染为小标题）。 |
| `concept` | 否 | 概念说明（Markdown 文本，渲染为正文）。 |
| `example` | 否 | 示例代码（渲染为代码块，HTML 转义）。 |

三项全空的条目被忽略；`knowledge` 非数组、或数组元素非对象报错。

## 3. 输出

### 3.1 HTML 文件

- 文件名：`day-{编号}-{日期}.html`（当日任务无日期时为 `day-{编号}.html`），如 `day-1-2026-08-20.html`。
- 单文件自包含：**内联 CSS、无任何外部资源**（无外链样式/脚本/图片/字体），可直接双击离线打开（ticket 06「静态单文件、可离线打开」）。
- 页面四个区块（ticket 06「HTML 模板」）：
  1. **今日知识**：知识条目（概念 + 示例代码块）；未提供 `knowledge` 且来源文件不可读时，兜底显示当日知识点列表。
  2. **完整链路**：学习目标（frontmatter `goal`）→ 步骤条（目标 → Day 1 … Day M，当前天高亮），标注「今日位置：第 N / M 天」。
  3. **今日目标**：当日目标清单（可勾选 checkbox，保留 plan.md 中 `- [x]` 的已勾选状态）+ 范围声明对照（覆盖 / 不涉及，来自 frontmatter `scope_covered` / `scope_excluded`）。
  4. **参考来源**：当日任务「来源」字段的链接——本地 `sources/` 文件渲染为 `file://` 绝对路径链接，URL 渲染为外链。
- 所有动态文本经 HTML 转义，防止注入。

### 3.2 输出 JSON

```json
{
  "html_path": "C:/…/day-1-2026-08-20.html",
  "output_dir": "C:/…",
  "day": "Day 1",
  "day_number": 1,
  "total_days": 3,
  "date": "2026-08-20",
  "topic": "pandas 入门",
  "goal": "用 Python 做数据分析",
  "scope_covered": ["数据分析", "pandas"],
  "scope_excluded": ["Web 框架"],
  "objectives": ["读懂 Series 与 DataFrame 的创建", "完成 3 个练习"],
  "knowledge_points": ["pandas.Series", "pandas.DataFrame"],
  "sources": ["sources/pandas-series.md", "https://…"],
  "knowledge_count": 2
}
```

| 字段 | 说明 |
| --- | --- |
| `html_path` / `output_dir` | 生成的 HTML 绝对路径与输出目录（均为 resolve 后绝对路径）。 |
| `day` / `day_number` / `total_days` | 当日任务标识、Day 编号、计划总天数（完整链路用）。 |
| `date` / `topic` / `objectives` / `sources` | 当日任务解析结果（来源为原样分隔后的列表）。 |
| `goal` / `scope_covered` / `scope_excluded` | plan.md frontmatter 解析结果（缺省为空串/空数组）。 |
| `knowledge_points` | 当日任务「知识点」字段解析结果（逗号分隔，剥离反引号）。 |
| `knowledge_count` | 渲染进知识区块的条目数——输入 `knowledge` 时为其条目数；未提供时为兜底读取的来源文件数（可能为 0）。 |

## 4. 知识内容来源（概念+示例）

- **优先**：输入 `knowledge` 字段——agent 在会话开始用检索层（`scripts/retrieve.py`）检索当日知识点，把资料提炼为「概念 + 示例」条目传入，保证内容精准、用户可读。
- **兜底**：未提供 `knowledge` 时，脚本读取当日任务「来源」引用的**本地 `sources/` 文件正文**（资料正文即「概念散文 + 代码示例」结构，frontmatter `title` 作为条目小标题），经脚本内置的极简 Markdown 渲染器转 HTML；URL 来源不读取（脚本不联网），仅出现在来源区块。
- 本地来源路径以 plan.md 所在目录为基准解析；文件不存在时跳过（不报错）。

## 5. plan.md 解析规则

- frontmatter：`goal`（字符串）、`scope_covered` / `scope_excluded`（数组，支持 `[a, b]` 或裸字符串）。
- Day 区块：`### Day N — YYYY-MM-DD`（日期可省略）起，至下一个 `### Day` 止，逐行解析：
  - `- 主题：…`
  - `- 目标清单：` 后跟 `  - [ ] …` 子项
  - `- 知识点：`（逗号分隔，剥离反引号）
  - `- 来源：`（中文/英文分号或逗号分隔，`sources/` 文件名或 URL）
- `- 前置：`（批次 2 新增的可选行，声明当日前置知识点/能力，见 `resources/data-formats.md` §1）**不由本脚本解析**——它是 agent 前置校验的输入，本脚本遇到未知行直接忽略，不影响解析。
- 容错：无 frontmatter、字段缺失均解析为默认值；找不到当日任务报错。

## 6. 测试

```bash
python scripts/test_page.py        # 全部测试（Python unittest）
```

- 样例夹具在 `scripts/testdata/`：`plan/`（plan.md 夹具）、`sources/`（复用检索层资料）、`input/`（场景输入）、`_out/page/`（生成 HTML 与输出 JSON，已 gitignore）。
- 注意：沙箱下 `tempfile` 不可写，测试全部显式指定 `output_dir` 到 `_out/page/`；「默认输出到系统临时目录」通过 `run()` 缺省 `output_dir` 时路径落在 `tempfile.gettempdir()` 的行为断言（不改盘）。
- 覆盖：四区块渲染（知识/链路/目标/来源）、目标清单与范围声明对照、来源链接（本地 file:// 与 URL）、knowledge 优先与来源正文兜底、无来源/无目标/无知识点的兜底文案、HTML 转义（示例含 `<script>` 不注入）、day 匹配（编号/日期/找不到）、输出目录缺省与覆盖、输出 JSON 字段、CLI 退出码。
- 测试 seam 与断言方式遵循 spec「测试 seam」章节：以样例输入文件驱动脚本，断言输出文件内容。

## 7. 用法示例（agent 流程）

1. 会话开始读 `plan.md`，定位当日任务（`Day N` 或日期）。
2. （可选）用检索层 `scripts/retrieve.py` 检索当日知识点 → 提炼 `knowledge`（概念+示例）。
3. 调本脚本：输入 `plan_path` + `day` + （可选）`output_dir` + （可选）`knowledge` → 拿到 `html_path`，把 HTML 呈现给学习者。
4. 当日执行期间网页可勾选目标、随时离线查看；验收完成、当日总结写入后，提出删除、学习者确认后删除（approval 护栏）。

## 8. 过程文件清理与网页生命周期

- 脚本 in/out JSON 与自检副本（HTML/JSON）放 `.python-coach/tmp/`，**自检完成即清**（目录与时机见 `resources/data-formats.md`「工作区目录结构」）。
- **当日执行网页 HTML**：存学习者可见位置（默认系统临时目录，会话中给出路径），验收与当日总结完成后由 ticket 12 提出删除、**学习者确认后才删**（唯一例外：该文件删除不走"内部清理"）。
