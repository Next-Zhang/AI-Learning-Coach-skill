# python-coach 持久层数据格式（六件套）

工作目录下的六个持久化数据文件/目录。写任何数据文件前先读本文件；字段名保持稳定（ADR-0002：`sources/` 的 frontmatter 即未来向量库切块元数据）。

| 文件 | 作用 | 更新者 |
| --- | --- | --- |
| `plan.md` | 当前学习计划：目标、范围声明、每日任务清单 | 计划生成/验证 |
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
- 知识点：`pandas.Series`, `pandas.DataFrame`
- 来源：sources/pandas-series.md；https://pandas.pydata.org/docs/user_guide/10min.html
```

**约定**
- frontmatter `goal` / `scope_covered` / `scope_excluded` 为计划适配性与失控防护锚点，改动需学习者确认。
- 生命周期：起步流程目标澄清阶段写入**草案**（`status: draft`，frontmatter 的 `goal`/`scope_covered`/`scope_excluded`/`status` 四字段 + 空每日任务，对话协议见 `resources/goal-scope-contract.md`）；计划生成三验证通过后落盘（`status: active`，每日任务齐备）。
- 每个 Day 区块：主题、目标清单（可勾选）、知识点、来源（引用 `sources/` 文件名或 URL）。
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
- 证据摘要：练习代码片段/运行结果说明

## 2026-08-21 — Day 2
- …
```

**约定**
- 每日总结**追加**在文件末尾，时间顺序递增，最新一天在最后。
- 完成度为合成值，格式 `x/5`，可附合成算式。
- 完成度合成由脚本 `scripts/completion.py` 计算（0.7 × agent + 0.3 × 自评，四舍五入到 0.5 档），契约见 `resources/completion-contract.md`。
- 难度反馈独立记录：`太难 | 刚好 | 太简单`，不参与完成度。
- 证据只存摘要与位置，不存大段代码（正文可引述关键几行）。

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

## 能力矩阵（知识点 × 水平分 1–5）
| 知识点 | 水平分 | 更新时间 | 来源 |
| --- | --- | --- | --- |
| pandas.Series | 2 | 2026-08-20 | 摸底测试 |
| pandas.DataFrame | 3 | 2026-08-21 | 验收 Day 1 |

## 增量记录
- 2026-08-20：摸底测试 → 初始矩阵
- 2026-08-21：验收 Day 1（完成度 4）→ pandas.Series +0.5（1.5→2）
```

**约定**
- 能力矩阵为唯一权威数据（与复习掌握度共用，见 `review/schedule.md`）。
- 增量更新规则：验收完成度 ≥ 4 → 该知识点 +0.5，上限 5；复习考察得分也写回。
- onboarding 字段固定 8 项；后续难度反馈只影响计划档位，不写入画像数值。
- 画像的读写与增量更新由脚本 `scripts/profile.py` 实现（`onboarding` / `acceptance` / `review`，契约见 `resources/profile-contract.md`）；onboarding 问卷写初值，验收/复习增量修正能力矩阵，难度反馈入增量记录。起步时对话式 onboarding 问卷流程见 `resources/onboarding-contract.md`。

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
- 掌握度与 `profile.md` 能力矩阵共用同一知识点 × 评分数据；本表是调度视图，矩阵是权威值。
- 本表的读写与推进由脚本 `scripts/schedule.py` 实现（`due`/`add`/`record`，契约见 `resources/schedule-contract.md`）。

---

## 变更原则

- 六件套 frontmatter 字段为契约：新增字段可以，改名/删字段需同步改脚本与测试（ticket 02–06）。
- 数据文件修改需学习者确认、删除需显式批准（SKILL.md 护栏 approval）。
