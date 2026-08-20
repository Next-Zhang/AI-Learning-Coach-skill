# Ticket 11 演练记录 — 每日会话开始流程（Day 5 早晨，2026-08-25）

本演练按 `resources/session-start-contract.md` 走通 Day 5 早晨的完整会话开头：**复习检查 → 一问一答考察与写回 → 随机抽查热场 → 当日网页生成 → 执行辅助**。所有脚本调用均为真实运行（退出码 0），产物见本目录。

## 0. 场景与前置数据

模拟「Day 1–4 已完成，其后各课知识点已按 ticket 13 纳入调度表」的 Day 5（2026-08-25）晨间状态：

- `plan.md`：ticket 10 终稿（`status: active`，9 天）；当日 Day 5 = 2026-08-25「Excel 读写」。
- `review/schedule.md`（before，见 `data-before/schedule.md`）：6 个知识点，各带档位。
- `profile.md`（before，见 `data-before/profile.md`）：能力矩阵 10 行，Day 1–4 验收/复习增量已入日志。
- `review/`：`01-variables-conditions.md`、`02-functions.md`、`03-pandas-series.md`、`04-reading-filtering.md` 四份复习快查卡（考察出题依据）。

## 1. 复习检查（到期知识点）

`scripts/schedule.py op=due`（today=2026-08-25）→ `output/due.out.json`：

```json
{
  "op": "due", "today": "2026-08-25",
  "due": [
    { "topic": "变量与数据类型", "mastery": 2.5, "next_date": "2026-08-25", "interval": 3 },
    { "topic": "数据读取与筛选", "mastery": 3.0, "next_date": "2026-08-25", "interval": 1 }
  ]
}
```

教练展示概览："今天到期 2 个知识点：`变量与数据类型`（上次 3 天前学的，掌握度 2.5）和 `数据读取与筛选`（昨天刚学，今天第一天复习）。我们逐一考一下。"

## 2. 一问一答考察（转写摘录）

**Q1 变量与数据类型**（依据 `review/01-variables-conditions.md`）：
教练："你在复习卡里记过一个『变量直接报错』的坑——写 `x = 3` 后再写 `x = 'hi'` 可以吗？那 `x` 的类型会变成什么？再举一个会让解释器直接报错的变量命名例子。"
学习者："可以重新赋值，x 会变成字符串。报错的例子……比如 `3x = 1`，以数字开头会报错。"
教练："答对了。变量可重新赋值、类型随之改变；以数字开头命名（`3x = 1`）报 SyntaxError。判定**通过**。"

**Q2 数据读取与筛选**（依据 `review/04-reading-filtering.md`）：
教练："上一题考读取：`df[df['金额'] > 100]['金额'] = 0` 这样把过滤后那几行的金额改成 0，能生效吗？为什么？"
学习者："应该能吧……过滤后再赋值，改了那一列。"
教练："答错了。链式索引赋值不生效（`df[...][...] = 0` 会触发 SettingWithCopyWarning，改的是副本），正确写法是 `df.loc[df['金额'] > 100, '金额'] = 0`。判定**未通过**——这个坑你复习卡里专门记过，Day 5 做读写练习时会再用到。"

**考察结果单（请学习者确认后统一写回）**：

| 知识点 | 结果 | 调度表推进 | 能力矩阵 |
| --- | --- | --- | --- |
| 变量与数据类型 | 通过 | 3/5，3→7 天，下次 09-01 | +0.5（2.5→3） |
| 数据读取与筛选 | 未通过 | 2.5/5，重置 1 天，下次 08-26 | -0.5（3→2.5） |

学习者："确认。"

**成对写回（真实脚本运行）**：
- `schedule.py record`（var, pass）→ `output/record-var.out.json`：`3.0 / 2026-09-01 / interval 7`
- `schedule.py record`（reading, fail）→ `output/record-reading.out.json`：`2.5 / 2026-08-26 / interval 1`（重置）
- `profile.py review`（var, pass）→ `output/review-var.out.json`：`old 2.5 → new 3.0`，日志「复习考察（通过）→ 变量与数据类型 +0.5（2.5→3）」
- `profile.py review`（reading, fail）→ `output/review-reading.out.json`：`old 3.0 → new 2.5`，日志「复习考察（未通过）→ 数据读取与筛选 -0.5（3→2.5）」

写回后调度表与矩阵同步一致（调度表是视图、矩阵是权威值），diff 见 `data-before/` ↔ `data/`。教练汇报："复习完成：变量通过推进到 7 天档；读取筛选未通过、已重置 1 天，明天会再见。"

## 3. 随机抽查热场（新课开头，不计分）

候选 = 非到期历史知识点（条件与循环、函数、pandas.Series、pandas.DataFrame）→ 随机抽 2 个：**函数**、**pandas.Series**。

教练："今天开始新课『Excel 读写』前，先热个身——随机抽两个学过的知识点，对对答案，不算分。"
教练："第一个：`def add(a, b=1): return a + b`，`add(3)` 返回多少？默认参数用 `[]` 当默认值有什么坑？"
学习者："返回 4。默认参数……用列表会有问题，函数间会共享那个列表。"
教练："对，默认参数在定义时求值，可变默认值会被多次调用共享。第二个：`pd.Series([1,2,3])` 是什么？里面取第一个元素用 `s[0]` 有没有坑？"
学习者："一维带标签数组；取第一个……`s[0]` 应该可以吧。"
教练："可以取，但标签为 0 时 `s[0]` 走标签、索引不连续时容易混——你复习卡里记的坑是优先用 `iloc[0]`。方向对了，放心练，今天读写完可以顺手翻一下 Series 卡。"
（热场**未判分、未写回、未推进调度表**——与 §2 到期考察严格区分。）

## 4. 当日网页生成

- 检索层 `retrieve.py`（query「Excel 读写 read_excel to_excel sheet」）→ `output/retrieve-excel.out.json`：本地 `sources/` 无相关命中，web 补充 3 条（read_excel 官方、to_excel 官方、视频），并入 `results`（`origin: web`）——符合「本地相关命中不足时允许一次 web 补充」。
- 提炼 knowledge（概念 + 示例）→ `page.py`（`plan_path` + `day=Day 5` + `knowledge`）→ `page-out/day-5-2026-08-25.html`（6181 字节，单文件自包含），输出 JSON 见 `page-out/page-day5.out.json`。
- 四区块齐全：`今日知识`（概念 + 示例）、`完整链路`（目标 → Day 1–9，Day 5 高亮）、`今日目标`（3 条可勾选 + 范围声明覆盖/不涉及）、`参考来源`（read_excel 官方 + 视频链接）。
- 教练交付："今天的执行页已生成（`day-5-2026-08-25.html`），双击可离线打开、可勾选目标。开始吧。"

## 5. 执行辅助（范围约束、来源引用）

教练："今天只做 Day 5：`read_excel` / `to_excel` / 指定 `sheet_name`，清洗 Day 6 才引入（计划里已注明），范围外（Web 框架、网络爬虫）不碰。参考官方文档：https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html 。先试试：读入你手头的报表，看看前 5 行。"
学习者："`import pandas as pd`，然后 `df = pd.read_excel('报表.xlsx')`……报错说没有 openpyxl。"
教练："对——那是 read_excel 的常见坑：读 .xlsx 需要 `pip install openpyxl`（官方文档同样要求）。装好后 `df.head()` 看前 5 行，再试 `sheet_name='明细'` 指定工作表。"
（当日完成后进入「反馈与验收」（ticket 12）；本流程不写 `progress.md`、不生成复习快查、不删网页。）

## 6. 产物清单

- `data/`：演练后工作数据（`plan.md`、`profile.md`、`review/` 可写状态）
- `data-before/`：写回前 `profile.md` / `schedule.md` 快照
- `input/` → `output/`：due / record ×2 / review ×2 / retrieve 的输入输出 JSON
- `page-out/`：`day-5-2026-08-25.html` 与输出 JSON
- 本文件：演练记录
