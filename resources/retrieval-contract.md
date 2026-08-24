# 检索层契约（ticket 02，ADR-0002）

v0 检索层实现 `scripts/retrieve.py`——统一契约：**输入查询 → 输出资料列表**（标题/来源/摘要/链接）。脚本以「读输入文件 → 写输出文件」形式提供，纯 Python 标准库、无外部依赖，可在任意工作目录运行。

本契约是技能内接口（ADR-0002）：升级到 plugin/应用时仅替换实现为向量检索，**输入输出格式不变**，流程代码零改动。

---

## 1. 用法

```bash
python scripts/retrieve.py <input.json> <output.json>
```

- 退出码：`0` 成功；`1` 检索失败（输入文件缺失/JSON 非法/缺 query/资料目录不存在）；`2` 参数个数不对。
- 失败信息写到 stderr。

## 2. 输入文件（JSON）

```json
{
  "query": "pandas groupby 聚合",
  "sources_dir": "sources",
  "limit": 10,
  "web_results": [
    {
      "title": "Pandas Documentation",
      "source": "https://pandas.pydata.org/docs/",
      "summary": "pandas 官方文档主页。"
    }
  ]
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `query` | 是 | 查询字符串；空/缺失报错（退出码 1）。 |
| `sources_dir` | 否 | 资料库目录，默认 `sources`。**相对路径以输入文件所在目录为基准**解析（写在工作目录的输入文件配 `"sources_dir": "sources"` 即可）。使用阶段 agent 一律**显式传** `.python-coach/state/sources`（六件套路径约定见 `resources/data-formats.md` 开头「工作区目录结构」）。 |
| `limit` | 否 | 结果数上限，默认 10。 |
| `web_results` | 否 | agent 侧 `web_search`/`web_fetch` 检索到的补充结果数组（见 §5）。 |

## 3. 输出文件（JSON）

```json
{
  "query": "pandas groupby 聚合",
  "results": [
    {
      "title": "pandas groupby 分组聚合",
      "source": "https://pandas.pydata.org/docs/user_guide/groupby.html",
      "summary": "pandas groupby 官方指南，按列分组后聚合（sum/mean）。",
      "link": "D:/…/sources/pandas-groupby.md",
      "topics": ["pandas", "groupby", "聚合"],
      "date": "2026-08-19",
      "score": 14.0,
      "matched_terms": ["pandas", "聚合"],
      "origin": "local"
    }
  ]
}
```

每条结果字段：

| 字段 | 说明 |
| --- | --- |
| `title` / `source` / `summary` / `topics` / `date` | 资料 frontmatter 五字段（与 `sources/` 数据格式一致，ADR-0002）。web 结果的 `topics` 为空数组、`date` 为空串。 |
| `link` | 本地结果：资料文件绝对路径；web 结果：来源 URL（无本地文件，link 即 `source`）。 |
| `score` | 相关度分（见 §4）；web 结果为 `null`。 |
| `matched_terms` | 命中该资料的查询词；web 结果为空数组。 |
| `origin` | `local`（来自 `sources/`）或 `web`（来自 `web_results`）。 |

**稳定契约**：`title` / `source` / `summary` / `link` 四字段与 `origin`、frontmatter 五字段是跨引擎稳定字段（ADR-0002 升级承诺）。`score` 与 `matched_terms` 是 v0 关键词检索的产物，**非稳定字段**——升级向量引擎后可能被替换或移除，消费方不得依赖它们（见 §7）。

## 4. 关键词检索与评分

- **分词**：查询小写化，按非单词字符切分（`\w` 含中文与数字）。中文无需分词器，按子串匹配。
- **匹配**：对每份 `sources/*.md`，解析 frontmatter 五字段 + 正文，逐词做大小写不敏感子串匹配，命中即加权累加：

| 位置 | 权重 |
| --- | --- |
| `title` | 3.0 |
| `topics` | 2.0 |
| `summary` | 1.5 |
| `body` | 1.0 |

- **排序**：`score` 降序 → `date` 新者优先 → `link` 字典序。得分 ≤ 0（无任何命中）的资料不输出。
- **limit**：本地结果先按 limit 截断，web 结果只补充剩余名额，合并后统一受 limit 约束。
- 仅正文命中的低分结果排在后面；这是 v0 关键词检索的预期行为（精准度由评分排序兜底，升级向量检索后消失）。

## 5. web 检索补充（v0 分工）

脚本自身**不联网**：`web_search`/`web_fetch` 是 agent（DeepSeek Harness）侧工具。v0 工作方式：

1. agent 先跑本地检索 `scripts/retrieve.py`；
2. 本地结果不足时，agent 用 `web_search`/`web_fetch` 补检索；
3. 把 web 结果按 `web_results` 字段（标题/来源/摘要）并入输入文件重跑，脚本负责合并与去重。

**终止条件（护栏「禁止空转」）**：

- 本地结果 ≥ 3 条视为充足，**不再**发起 web 补充（阈值可按当日任务需要调整，但必须显式设定）；
- web 补充**至多一轮**：合并后仍不足也不迭代重跑；
- 脚本本身单遍执行、无任何循环/重试；「本地→web→并入」是 agent 侧的流程步骤，受上述两条约束，不会空转。

**去重**：按归一化 URL（去首尾空白、去结尾 `/`、转小写）比对 `source`；与本地结果重复、web 内部重复的都跳过。本地结果始终排在 web 结果之前。

## 6. 测试

```bash
python scripts/test_retrieve.py        # 全部测试（Python unittest）
```

- 样例夹具在 `scripts/testdata/`：`sources/`（4 份资料）、`edge/`（frontmatter 边界）、`input/`（检索输入）、`_out/`（运行输出，已 gitignore）。
- 覆盖：frontmatter 解析（含缺字段/无 frontmatter/引号主题）、评分与排序、limit、无结果、中文分词、web 合并去重、`run()` 文件契约、CLI 退出码。
- 测试 seam 与断言方式遵循 spec「测试 seam」章节：以样例输入文件驱动脚本，断言输出文件内容。

## 7. 升级路径（ADR-0002）

替换 `search_sources` 实现为向量检索即可。升级时**稳定不变**的部分：输入文件格式、四必需字段（标题/来源/摘要/链接）、`origin`、frontmatter 五字段、web 合并去重流程与测试契约；`score`/`matched_terms` 为 v0 关键词产物，升级时可替换或移除（消费方不得依赖，见 §3）。`sources/` 的 frontmatter 字段即向量库切块元数据，数据零迁移。

## 8. 过程文件清理

本脚本的 in/out JSON 放 `.python-coach/tmp/`，**当日使用完成即清**（目录与时机见 `resources/data-formats.md`「工作区目录结构」）。清理为 agent 内部动作，不需逐条向学习者确认。
