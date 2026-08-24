# python-coach 持久层数据格式（六件套）

正式状态文件（六件套）存于当前工作区的 `.python-coach/state/`。写任何数据文件前先读本文件；字段名保持稳定（ADR-0002：`sources/` 的 frontmatter 即未来向量库切块元数据）。

## 工作区目录结构（三类区 + 生命周期）

本技能在**学习者工作区**内运作。正式数据与过程文件按三类区分离存放，区域边界即权限边界（决策 7）：

```
工作区/
├── python-coach/            # Skill 本体：SKILL.md + resources/ + scripts/ + templates/ + docs/ + CONTEXT.md（只读）
├── .python-coach/           # 使用期数据目录（隐藏目录，每工作区独立）
│   ├── state/               # 六件套正式状态：plan.md / progress.md / profile.md / sources/ / review/ / review/schedule.md
│   └── tmp/                 # 本会话过程文件（初始化 JSON、草稿、修订记录、评审出入包、自检副本、脚本 in/out JSON）→ 阶段完成即清
├── exercises/               # 每日练习：agent 生成、学习者完成并保留（持久，按需读取）
└── project/                 # 最终项目（如 ABM）：综合实战交付物，agent 在该天辅助与验收
```

**约定（决策 6/7/12）**

- **六件套正式文件一律放 `.python-coach/state/`**：下表列出的 `plan.md`、`progress.md`、`profile.md`、`sources/`、`review/`、`review/schedule.md` 均指该目录内的文件。
- **路径约定（决策 12）**：脚本默认路径值**不改**（`profile.md`、`plan.md`、`sources`、`review`、`review/schedule.md`）；使用阶段 agent **一律显式传** `.python-coach/state/…` 路径（相对当前工作区解析；输入 JSON 放在 `.python-coach/tmp/` 时，相对路径按输入文件所在目录解析，可传 `../state/…` 或绝对路径）。
- **过程文件生命周期（决策 6）**：起步与每日流程产生的过程文件（初始化 JSON、计划草稿/修订记录、评审出入包、`page.py` 自检副本、各脚本 in/out JSON）放 `.python-coach/tmp/`，**所属阶段完成即清**；会话结束时 `.python-coach/tmp/` 全清、`state/` 只剩六件套。清理为 agent 内部动作，**不需逐条向学习者确认**（**当日执行网页除外**——其删除必须学习者显式批准，见 SKILL.md 护栏 approval）。
- **项目边界**：**当前项目 = 本工作区内的 `.python-coach/ + exercises/ + project/`**；其余目录（其他技能、`.git`、无关项目）一律不读不写。
- **首次起步**：按 `templates/` 初始化六件套到 `.python-coach/state/`（模板路径不变）。

| 文件（`.python-coach/state/` 内） | 作用 | 更新者 |
| --- | --- | --- |
| `plan.md` | 当前学习计划：目标、范围声明、每日任务清单 | 目标澄清（草案）/ 计划生成与验证（落盘） |
| `progress.md` | 逐日学习进度，每日总结追加 | 每日验收 |
| `profile.md` | 用户画像：onboarding 问卷、能力矩阵、增量 | 验收/复习 |
| `sources/` | 资料库：带 frontmatter 的 Markdown 资料 | 检索层数据源 |
| `review/` | 复习快查文档（按课程一份） | 每节课结束 |
| `review/schedule.md` | 复习调度表：知识点 → 掌握度 → 下次复习日 | 复习考察 |

---

## 1. plan.md — 学习计划

```markdown
---
goal: 用一句话说清"想用 Python 做什么"的具体目标
scope_covered: [数据分析, pandas, 数据可视化]   # 范围声明：覆盖的子领域
scope_excluded: [Web 框架, 网络爬虫]            # 范围声明：不涉及的子领域
status: active                                   # draft | active | completed | archived
created: 2026-08-19
updated: 2026-08-19
---

# 学习计划

## 每日任务

### Day 1 — 2026-08-20
- 主题：pandas 入门
- 目标清单：
  - [ ] 读懂 Series 与 DataFrame 的创建
  - [ ] 完成 3 个练习
- 前置：Python 变量与类型, Python 工程组织
- 知识点：`pandas.Series`, `pandas.DataFrame`
- 来源：sources/pandas-series.md；https://pandas.pydata.org/docs/user_guide/10min.html
```

**约定**
- frontmatter `goal` / `scope_covered` / `scope_excluded` 为计划适配性与失控防护锚点，改动需学习者确认。
- 生命周期：起步流程目标澄清阶段写入**草案**（`status: draft`，frontmatter 的 `goal`/`scope_covered`/`scope_excluded`/`status` 四字段 + 空每日任务，对话协议见 `resources/goal-scope-contract.md`）；计划生成三验证通过后落盘（`status: active`，每日任务齐备）。
- 每个 Day 区块：主题、目标清单（可勾选）、**前置（可选）**、知识点、来源（引用 `sources/` 文件名或 URL）。
- **前置声明（决策 3.2）**：`- 前置：<知识点/能力名，逗号分隔>`，名称与能力矩阵行名对齐；无前置则省略该行。计划生成阶段据此插入补前置天、每日行前据此做前置校验（判定规则见 §3）。
- 来源为必需字段；无来源的 Day 视为未验证，不得落盘（护栏「引用规范」）。

---

## 2. progress.md — 学习进度

```markdown
---
learner: <学习者标识，如姓名/昵称>
started: 2026-08-19
updated: 2026-08-20
---

# 学习进度

## 2026-08-20 — Day 1
- 当日任务：pandas 入门
- 完成度：4/5（agent 4 × 0.7 + 自评 4 × 0.3 = 4）
- 难度反馈：刚好
- 当日总结：掌握了 Series 创建，DataFrame 列操作还需练习……
- 证据：
  - [读懂 Series 创建] s = pd.Series([1,2,3]) 输出成功 → pandas.Series
  - [完成 3 个练习] 练习 1/2/3 结果见 exercises/… → pandas.DataFrame

## 2026-08-21 — Day 2
- …
```

**约定**
- 每日总结**追加**在文件末尾，时间顺序递增，最新一天在最后。
- 完成度为合成值，格式 `x/5`，可附合成算式。
- 完成度合成由脚本 `scripts/completion.py` 计算（0.7 × agent + 0.3 × 自评，四舍五入到 0.5 档），契约见 `resources/completion-contract.md`。
- 难度反馈独立记录：`太难 | 刚好 | 太简单`，不参与完成度。
- **证据条目式结构化（决策 16，批次 3）**：`- 证据：` 后跟**条目子列表**，每条 `- [<目标/动作>] <证据描述> → <知识点>`：
  - `[<目标/动作>]` 对应当日目标清单的某一项目标；
  - `→ <知识点>` 尾部与**当日计划「知识点」**口径一致（`scripts/check.py` 的 `evidence_consistent` 校验，契约见 `resources/check-contract.md`）；
  - 证据只存要点与位置，不存大段代码（正文可引述关键几行）；验收逐目标核查的结论可直接落为这些条目（`resources/acceptance-contract.md` §7）。
- 当日总结的起草、展示、追加与确认协议见 `resources/acceptance-contract.md`（ticket 12）。

---

## 3. profile.md — 用户画像

```markdown
---
created: 2026-08-19
updated: 2026-08-20
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
| 编程基础 | 语法基础 | Python 变量与类型 | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |
| 编程基础 | 面向对象 | OOP 类与对象 | 知识点 | 1 | — | 2026-08-20 | 摸底测试 |
| 工程 | 工程素养 | Python 工程组织 | 能力 | — | 未具备 | 2026-08-20 | 摸底测试 |

## 增量记录
- 2026-08-20：摸底测试 → 初始矩阵
- 2026-08-21：验收 Day 1（完成度 4）→ pandas.Series +0.5（1.5→2）
```

**约定**
- 能力矩阵为唯一权威数据（与复习掌握度共用，见 `review/schedule.md`）。
- **分层 schema（决策 2）**：一张扁平表 `| 领域 | 子领域 | 知识点 | 类型 | 水平分 | 前置状态 | 更新时间 | 来源 |`，不建分组子表。
  - `类型 = 知识点 | 能力`；知识点行 `前置状态 = —`（其"具备"由水平分阈值判定）；能力行 `水平分 = —`、`前置状态 = 具备 | 未具备`。
  - 领域/子领域为分层归属（如 编程基础/语法基础、工程/工程素养），与 `plan.md` 的 `scope_covered` 口径对齐。
- **前置判定规则（决策 13）**：知识点前置 → 矩阵水平分 **≥ 3** 视为具备（`< 3` 为缺口）；能力前置 → `前置状态 = 未具备` 即为缺口（二值）。判定用于计划生成（补前置天）与每日行前（缺口分级处置），见 `resources/plan-contract.md` §3.1 与 `resources/session-start-contract.md` §2。
- 初始矩阵由**摸底测试**建立（范围驱动的 15–20 题，按知识点判分合成 + 前置能力评估题组，对话协议见 `resources/placement-contract.md`）；增量更新规则：验收完成度 ≥ 4 → 该知识点 +0.5，上限 5；复习考察得分也写回。**增量只作用于知识点行**（能力行无水平分）。
- **矩阵外显式新增（批次 4，决策 5）**：验收/复习中发现矩阵外新知识点，经学习者确认后由 `profile.py`（`add_new: true`）新建矩阵行——知识点行初值：验收 = 完成度 / 复习通过 2.0、未通过 1.0；能力行（`type = 能力`）写前置状态二值；来源 `验收新增 Day N` / `复习新增`。三同步配套 `schedule.py op=add`（纳入调度表）与 `review.py op=append`（追加到当日课快查文档），流程与留痕见 `resources/acceptance-contract.md` §6。
- onboarding 字段固定 8 项；后续难度反馈只影响计划档位，不写入画像数值。
- 画像的读写与增量更新由脚本 `scripts/profile.py` 实现（`onboarding` / `placement` / `acceptance` / `review`，契约见 `resources/profile-contract.md`）；onboarding 问卷写初值，摸底测试初始化能力矩阵（行来源「摸底测试」），验收/复习增量修正能力矩阵，难度反馈入增量记录。起步时对话式 onboarding 问卷流程见 `resources/onboarding-contract.md`。调用 `profile.py` 时**显式传** `.python-coach/state/profile.md` 路径（见「工作区目录结构」路径约定）。

---

## 4. sources/ — 资料库

每份资料一个 Markdown 文件，文件名小写短横线（如 `pandas-series.md`）。

```markdown
---
title: pandas 十分钟入门
source: https://pandas.pydata.org/docs/user_guide/10min.html
topics: [pandas, 入门]
date: 2026-08-19
summary: pandas 官方 10 分钟速览，覆盖 Series/DataFrame 基础操作。
---

# <标题>

<正文，Markdown。内容按主题组织，可被检索层切块。>
```

**约定（ADR-0002，字段稳定）**
- frontmatter 五字段：`title`（标题）、`source`（来源 URL）、`topics`（主题标签数组）、`date`（日期）、`summary`（一句话摘要）。
- 这是检索层（ticket 02）的输入格式，也是未来向量库的切块元数据；字段名不可随意改动。
- 正文为可读 Markdown；检索层按关键词匹配 frontmatter 与正文。
- 检索层脚本（`scripts/retrieve.py`）使用阶段**显式传** `.python-coach/state/sources` 路径（路径约定见开头「工作区目录结构」）。

---

## 5. review/ — 复习快查文档

按课程一份，命名 `NN-主题.md`（如 `01-pandas-groupby.md`）。

```markdown
---
course: 01
date: 2026-08-20
topics: [pandas, groupby]
---

# 01 — pandas groupby

- **groupby 分组聚合**：按列分组后聚合。`df.groupby('key').sum()`；常见坑：分组列默认变索引，用 `reset_index()` 恢复；来源：sources/pandas-groupby.md。
- **agg 多聚合**：`df.groupby('key').agg(['sum','mean'])`；常见坑：多级列名；来源：sources/pandas-groupby.md。
```

**约定**
- 每个知识点一行：概念一句话 + 关键代码/示例 + 常见坑 + 来源引用。
- 用户可读优先：术语用中文解释，代码简短可运行。
- 支持按知识点（`topics`）、按日期（`date`）直接查阅；agent 依据它出题考察。
- 每节课结束的生成（`review/NN-主题.md`）与按知识点/日期查阅由脚本 `scripts/review.py` 实现（`generate` / `query`，契约见 `resources/review-contract.md`）；新知识点纳入调度表由 `generate` 输出的 `schedule_add` 接 `scripts/schedule.py`（`op=add`）完成。调用 `review.py` 时**显式传** `.python-coach/state/review` 路径（路径约定见开头「工作区目录结构」）。

---

## 6. review/schedule.md — 复习调度表

```markdown
---
updated: 2026-08-20
---

# 复习调度表

| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |
| --- | --- | --- | --- |
| pandas.Series | 2/5 | 2026-08-21 | 1 |
| pandas.DataFrame | 3/5 | 2026-08-24 | 3 |
```

**约定**
- 间隔重复：1 → 3 → 7 → 15 → 30 天推进。
- 考察通过 → 掌握度更新 + 下一档间隔（如 1→3）；未通过 → 掌握度下调 + 重置回 1 天。
- agent 只查本表决定复习什么，不扫描 `review/` 全部文档（性能护栏）。
- 掌握度与 `profile.md` 能力矩阵共用同一知识点 × 评分数据；本表是调度视图，矩阵是权威值。**能力行不进入复习调度表**（无水平分、前置状态二值，不做间隔重复）。
- 本表的读写与推进由脚本 `scripts/schedule.py` 实现（`due`/`add`/`record`，契约见 `resources/schedule-contract.md`）。调用时**显式传** `.python-coach/state/review/schedule.md` 路径（路径约定见开头「工作区目录结构」）。

---

## 变更原则

- 六件套 frontmatter 字段为契约：新增字段可以，改名/删字段需同步改脚本与测试（ticket 02–06）。
- 六件套正式文件一律在 `.python-coach/state/`；过程文件放 `.python-coach/tmp/`、阶段完成即清（见开头「工作区目录结构」）。
- 数据文件修改需学习者确认、删除需显式批准（SKILL.md 护栏 approval）。
