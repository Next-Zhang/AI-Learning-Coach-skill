# python-coach Skill 修订方案 v1（2026-08 评审）

> 本方案由 grilling 会话（设计树全部分支收敛）产出，供学习者确认。**本方案不修改任何 skill 文件**；确认后按批次实施。
> 状态：**已确认并分批实施**（批次 0/1/2/3/4/5 全部完成；进度勾选见 §14）。

---

## 0. 背景：实际使用中发现的五个问题

1. **能力与知识点自动校验不足**——前置能力（Python 工程、OOP、ABM 等）未被初始计划识别；知识点、任务、验收证据之间无自动核对；更新能力矩阵时遇到矩阵外知识点直接报错、无法修改。
2. **过程文件无生命周期管理**——初始化 JSON、计划草稿、评审出入包、网页检查副本在阶段完成后不分类、不清理。
3. **文件存储位置不清晰**——`plan.md`、`profile.md` 等散落在根目录，正式状态 / 审计记录 / 临时文件边界不明。
4. **工作区与记忆隔离规则不足**——未明文规定只读当前项目、禁止跨项目继承、按需读取练习文件、工作区外访问须授权。
5. **skill 文件夹存在创建期的测试残留**——`.scratch/python-coach/rehearsal-08~12/` 演练产物、`scripts/testdata/_out/`、`scripts/__pycache__/`。

---

## 1. 已确认的决策汇总（grilling Round 1–3）

| # | 决策 | 结论 |
| --- | --- | --- |
| 1 | 本方案产出物 | 共享理解 + 书面修订方案；**文件改动在确认后的后续会话做** |
| 2 | 能力矩阵分层 | 领域 → 子领域 → 知识点 + 独立"前置能力"层（类型 = 知识点 / 能力） |
| 3 | 前置校验落点 | 计划生成阶段 + 每日行前，两层都做 |
| 4 | 自动核对机制 | 混合：`check.py`（机械校验）+ 契约规则（语义校验） |
| 5 | 矩阵外知识点 | 显式新增通道（暂停 → 说明 → 学习者确认 → 矩阵+调度+快查三同步） |
| 6 | 过程文件生命周期 | 三类区（正式 state / 过程 tmp / 学习者项目）+ 阶段边界自动清理 |
| 7 | 目录布局 | `python-coach/`（只读本体）+ `.python-coach/{state,tmp}` + `exercises/` + `project/` |
| 8 | 隔离护栏 | SKILL.md 护栏新增「工作区与记忆隔离」小节，DSH 沙箱在 permission 层兜底 |
| 9 | 测试残留 | 保留 spec+issues+测试夹具，删除 rehearsal 实体，清理 `_out/` 与 `__pycache__/` |
| 10 | skill 名称 | 保持 `python-coach`（不改成 AI-Learning-Coach-skill） |
| 11 | 分发方式 | 会装进 `~/.dsh/skills` 技能库，可能被多个 agent 引用 → 每工作区数据独立 |
| 12 | 脚本默认路径 | 保持脚本默认值，契约明文"使用阶段一律显式传路径" |
| 13 | 前置判定 | 知识点用矩阵水平分 **≥3** 为具备；能力用二值"具备/未具备"（摸底评估） |
| 14 | 缺口处置 | 计划阶段自动插入补前置天；行前阶段严重缺口（能力未具备或 ≤1.5 分）暂停回计划、轻度缺口（1.5<分<3）当日补讲导入段 |
| 15 | 运行期留痕 | 极简一行式，单文件 `state/decision-log.md`；`audit/` 目录取消 |
| 16 | progress 证据 | 自由文本 → 结构化条目（目标 → 证据 → 知识点） |
| 17 | 打包说明 | README 加"安装与分发"；运行脚本加 `PYTHONDONTWRITEBYTECODE=1` |

---

## 2. 目标工作区布局（正式/过程/学习者项目 三类边界）

```
工作区/
├── python-coach/            # Skill 本体：SKILL.md + resources/ + scripts/ + templates/ + docs/ + CONTEXT.md（只读）
├── .python-coach/           # 使用期数据目录（隐藏目录，每工作区独立）
│   ├── state/               # 六件套正式状态：plan.md / profile.md / progress.md / sources/ / review/ / review/schedule.md + decision-log.md
│   └── tmp/                 # 本会话过程文件（初始化 JSON、草稿、评审出入包、自检副本、脚本 in/out JSON）→ 阶段完成即清
├── exercises/               # 每日练习：agent 生成、学习者完成并保留（持久，按需读取）
└── project/                 # 最终项目（如 ABM）：综合实战交付物，agent 在该天辅助与验收
```

- 原设计中的 `.python-coach/audit/`（可选运行与评审记录）**取消**：运行期留痕统一为极简 `state/decision-log.md`（决策 15）。
- 项目边界定义：**当前项目 = 本工作区内的 `.python-coach/ + exercises/ + project/`**；其余目录（其他技能、`.git`、无关项目）一律不读不写。

---

## 3. 分层能力矩阵与前置能力机制

### 3.1 profile.md §3 新 schema（resources/data-formats.md）

```markdown
## 能力矩阵（领域 → 子领域 → 知识点/能力）
| 领域 | 子领域 | 知识点 | 类型 | 水平分 | 前置状态 | 更新时间 | 来源 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 编程基础 | 语法基础 | Python 变量与类型 | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |
| 编程基础 | 面向对象 | OOP 类与对象 | 知识点 | 1 | — | 2026-08-20 | 摸底测试 |
| 工程 | 工程素养 | Python 工程组织 | 能力 | — | 未具备 | 2026-08-20 | 摸底测试 |
```

- `类型 = 知识点 | 能力`；知识点行 `前置状态 = —`（其"具备"由水平分阈值判定）；能力行 `水平分 = —`、`前置状态 = 具备 | 未具备`。
- 一张扁平表加列（不建分组子表）：`profile.py` 现有表格解析改为按列解析，测试夹具同步小改。

### 3.2 前置声明（resources/plan-contract.md §3.3、data-formats §1）

- plan.md 每个 Day 区块新增字段：`- 前置：<知识点/能力名，逗号分隔>`，名称与能力矩阵行名对齐（page.py 的 list 解析规则可直接复用）。
- 生成计划时每 Day 声明前置；无前置则省略。

### 3.3 前置评估（resources/placement-contract.md）

- 摸底测试新增"前置能力评估"题组：对工程素养 / OOP 素养 / ABM 建模理解等能力行做几问快速评估，标记 `具备 | 未具备`，随 `op=placement` 写入矩阵。

### 3.4 判定规则

- 知识点前置：矩阵水平分 **≥ 3** 视为具备；`< 3` 为缺口。
- 能力前置：`前置状态 = 未具备` 即为缺口（二值）。

---

## 4. 前置缺口的两层处置

### 4.1 计划生成阶段（plan-contract §3.1/§3.4）

- 生成每日任务前，逐知识点核对 `- 前置：` 项是否具备；
- 有缺口 → 自动在主题序列中**插入"补前置天"**（只排缺口知识点/能力，来源照常检索），并入总天数 T 推导，请学习者确认后落盘。

### 4.2 每日行前阶段（session-start-contract §2）

- 会话开始读取当日 Day 后，对照矩阵做前置校验：
  - **严重缺口**：能力 `未具备` 或 前置知识点 ≤ 1.5 分 → 暂停当日任务，回计划插入补前置天（走计划修订）；
  - **轻度缺口**：1.5 < 分 < 3 → 当日先"补讲前置导入段"再进正题，当日总结中注明。

---

## 5. 自动核对：新增 `scripts/check.py`

### 5.1 校验范围（机械可判定部分）

- plan 的「知识点」「前置」引用 ⊆ 能力矩阵行；
- 当日任务知识点 ↔ 目标清单 ↔ 验收写回 topic 口径一致；
- progress.md 结构化证据条目的知识点与当日 plan 一致；
- decision-log.md 可读、日期合法。

### 5.2 触发点（三处）

1. **计划落盘前**（plan-contract §6 自检）；
2. **每日行前**（session-start-contract §2）；
3. **验收写回前**（acceptance-contract §6）。

### 5.3 输出与契约

- 输出结构化问题清单（不硬阻塞；是否阻断由对应契约规定）；
- 新增契约 `resources/check-contract.md` + `scripts/test_check.py` + testdata 夹具；
- 语义校验（证据是否真支撑目标、质量）留在验收契约规则里，不进脚本（决策 4）。

---

## 6. progress.md 证据结构化（data-formats §2 配套）

- 每日总结的「证据摘要」从自由文本改为条目式：

```markdown
- 证据：
  - [读懂 Series 创建] s = pd.Series([1,2,3]) 输出成功 → pandas.Series
  - [完成 3 个练习] 练习 1/2/3 结果见 exercises/… → pandas.DataFrame
```

- 与 check.py 的"证据知识点一致性"校验配套；验收逐目标核查的结论可直接落为这些条目。

---

## 7. 矩阵外知识点的显式新增通道

### 7.1 触发

- `op=acceptance` 或 `op=review` 的 `topic` 不在能力矩阵中（当前行为：profile.py 报错退出）→ 改为**暂停并进入通道**。

### 7.2 流程（acceptance-contract §6、profile-contract §4 同步改）

1. 检测到矩阵外知识点 → 暂停写回，向学习者展示："学习中出现了新知识点 `X`，将加入能力矩阵并纳入复习调度，是否确认？"；
2. 学习者确认后三同步：
   - `profile.py` 建矩阵行（类型 = 知识点，来源 = `验收新增 Day N` / `复习新增`；若属能力 → 类型 = 能力 + 前置状态）；
   - `schedule.py op=add` 纳入调度表；
   - 复习快查文档追加一行到**当日课程的** `review/NN-主题.md`（新知识点无独立课程归属，挂当日课，来源标注）。
3. 学习者拒绝 → 维持原样，写回跳过该知识点并记录。

- `op=review`（复习考察）对称走同一通道。

---

## 8. 过程文件生命周期（三类区 + 清理时机表）

| 过程物 | 存放 | 清理时机 |
| --- | --- | --- |
| onboarding 输入 JSON | `state/` 暂存 | 起步完成即清 |
| 计划草案 draft-1…n、修订记录 | `tmp/` | 落盘 `active` 后清 |
| 评审出入包 in-/out-*.md | `tmp/` | 评审完成即清（结论行入 decision-log） |
| page.py 自检副本（HTML/JSON） | `tmp/` | 自检完成即清 |
| 每日 due/record/acceptance 的 in/out JSON | `tmp/` | 当日验收完成即清 |
| **当日执行网页 HTML** | 学习者可见位置（默认系统临时目录，会话中给出路径） | **保持"学习者确认后删"**（approval 护栏，唯一例外） |
| 会话结束 | — | `tmp/` 全清，`state/` 只剩六件套 + decision-log |

- 各契约（plan / session-start / acceptance / profile / schedule / review）补对应清理条款；清理为 agent 内部动作，不需逐条向学习者确认（网页除外）。

---

## 9. 运行期留痕（极简）

- 单文件 `state/decision-log.md`，一行一条：
  `2026-08-25 | 计划落盘 | 评审 2 轮通过 | 检索命中 11 | 插入补前置天 1`
- 覆盖：计划落盘/修订、评审轮数与结论、检索命中数、矩阵新增知识点、计划调整。
- 与 progress.md 叙事分离，check.py 可读。

---

## 10. 工作区与记忆隔离护栏（SKILL.md 新增小节）

新增护栏小节「工作区与记忆隔离」，每次加载必读：

1. **只读当前项目**：只读当前工作区 `.python-coach/state/` 与 `exercises/`、`project/`；不 glob 整个工作区、不读其他技能目录、不读 `.git`。
2. **禁止跨项目继承**：plan / profile / progress / review 一律来自当前项目的 `.python-coach/state/`；不继承、不读取任何其他项目的画像、计划、调度。
3. **按需读取练习文件**：只按当日任务需要读取/写入 `exercises/` 的对应文件；不扫描全部练习。
4. **工作区外访问必须授权**：任何 `.python-coach/`、`exercises/`、`project/` 之外的读写（其他目录、系统目录、安装目录）需学习者显式授权（approval 层面）。
5. **运行期不写 skill 目录**：技能本体为只读组件；运行脚本统一加 `PYTHONDONTWRITEBYTECODE=1` 避免 `__pycache__` 落入安装目录。

记忆隔离：沿用 ADR-0001（不跨日延续会话）+ 新增"不跨项目"（见第 2 条）。

---

## 11. 存储 / 路径 / 安装分发

### 11.1 路径策略

- 六件套正式文件在 `.python-coach/state/`；脚本默认值**不改**（决策 12），各契约明文："使用阶段一律显式传 `.python-coach/state/…` 路径（相对当前工作区解析）。"
- 首次起步：按 `templates/` 初始化六件套到 `state/`（模板路径不变）。

### 11.2 安装与分发（README 新增"安装与分发"小节）

- 打包清单：`SKILL.md + resources/ + scripts/（含测试与 testdata 夹具）+ templates/ + docs/ + CONTEXT.md`；**剔除 `.scratch/`、`.git/`**。
- 部署到技能库/多个 agent 时：每个工作区各自建 `.python-coach/`，数据互不共享（对应隔离护栏）。
- skill 名称保持 `python-coach`（决策 10），不重命名目录与引用。

---

## 12. 测试残留清理清单（决策 9 / 你的 Q9 结论）

### 12.1 删除（实体删除）

- `.scratch/python-coach/rehearsal-08/`、`rehearsal-09/`、`rehearsal-10/`、`rehearsal-11/`、`rehearsal-12/`（整目录）。
- 磁盘上 `scripts/testdata/_out/`、`scripts/__pycache__/`（已 gitignore，直接清）。

### 12.2 保留

- `.scratch/python-coach/spec.md` + `issues/01–13/`（设计基线，开发票据）。
- `scripts/testdata/` 夹具与 `test_*.py`（回归安全网，spec 用户故事 25）；后续新增 check 夹具。
- `docs/adr/`、`CONTEXT.md`。

### 12.3 文档引用同步（演练记录压缩为一行摘要，删除对实体文件的引用）

| 文件 | 位置 | 处理 |
| --- | --- | --- |
| README.md | L20（scripts 段提到 rehearsal-10/11/12）、L24（.scratch 描述） | L20 改"对话式流程经实际演练验证（摘要见各契约）"；L24 保留 spec+issues 描述 |
| plan-contract.md | §8（L134–141，rehearsal-10 详录） | 压缩为一行"已演练"摘要 |
| session-start-contract.md | §9（L107–114，rehearsal-11 详录） | 压缩为一行摘要 |
| acceptance-contract.md | §10（L123–124，rehearsal-12 详录） | 压缩为一行摘要 |
| goal-scope-contract.md | §8（L72–73） | 压缩演练记录引用 |
| onboarding-contract.md | §8（L88–89） | 压缩演练记录引用 |
| placement-contract.md | §8（L128–129） | 压缩演练记录引用 |

- 各契约 §测试 对 `testdata/` 的引用**保留**（夹具仍在）。

---

## 13. 文件级变更清单

| 文件 | 变更 |
| --- | --- |
| `SKILL.md` | 护栏新增「工作区与记忆隔离」；「会话开始」读取路径改 `state/`；行前前置校验；数据文件小节指向 state/；运行期不写 skill 目录 |
| `resources/data-formats.md` | 目录地图新章节；六件套路径改 `state/`；矩阵 schema 加列；前置于段；progress 证据结构化 |
| `resources/profile-contract.md` | placement 增领域/子领域/类型/能力评估；acceptance/review 支持矩阵外新增（显式通道）；校验规则更新 |
| `resources/placement-contract.md` | 增加前置能力评估题组 |
| `resources/plan-contract.md` | Day 前置声明；补前置天插入逻辑；适配性评审加前置核查；落盘前跑 check.py；清理条款 |
| `resources/session-start-contract.md` | 行前前置校验（严重/轻度分级处置）；读取与清路径；清理条款 |
| `resources/acceptance-contract.md` | 矩阵外知识点显式通道（三同步）；证据结构化条目；写回前跑 check.py；清理条款 |
| `resources/review-contract.md` | 快查追加"当日课新增行"语义；清理条款 |
| `resources/check-contract.md` | **新增**：check.py 契约 |
| `resources/…（其余契约）` | 清理条款与 `state/` 路径统一注明 |
| `scripts/profile.py` | 表格解析/写出加列（领域/子领域/类型/前置状态）；placement 能力评估；acceptance/review 新增行（显式通道） |
| `scripts/check.py` + `test_check.py` | **新增**：引用一致性校验（§5） |
| `scripts/test_*.py` + `testdata/` | 同步新 schema 与新契约的夹具/断言 |
| `templates/profile.md` | 矩阵表头按新 schema 更新 |
| `templates/plan.md` | Day 区块加 `- 前置：` 占位说明 |
| `README.md` | 结构清单更新；演练引用压缩；新增"安装与分发" |
| `.scratch/python-coach/spec.md` | 追加两段决策记录（前置能力机制、目录化与生命周期）——保持设计基线同步 |

---

## 14. 实施批次建议（确认后按序执行）

- ✅ **批次 0（清理）**：12.1 删除 + 12.3 文档引用压缩（先做，破坏性最小、独立可验证）。
- ✅ **批次 1（目录化）**：data-formats 目录地图 + `state/` 路径约定 + templates 初始化为 state + 各契约清理/路径条款（决策 6/7/12）。
- ✅ **批次 2（分层矩阵+前置）**：矩阵 schema、profile.py/夹具、placement 前置能力评估、plan/session-start 前置校验与缺口处置、prechek 引用（决策 2/3/13/14）。
- ✅ **批次 3（check.py）**：脚本 + 契约 + 三触发点 + progress 证据结构化（决策 4/16）。
- ✅ **批次 4（新增知识通道）**：acceptance/review 对称显式通道（决策 5/15→decision-log）。
- ✅ **批次 5（护栏+分发）**：SKILL.md 隔离小节、README 安装分发、`PYTHONDONTWRITEBYTECODE=1`（决策 8/11/17）。
- 每批次结束：跑全量 `test_*.py` 回归（当前 7 套 225 例全绿）。

---

## 15. 明确不做（范围外）

- 不改 `page.py` 的 HTML 模板/四区块结构、不改间隔重复算法（1→3→7→15→30）、不改完成度合成（7:3/0.5 档）、不改检索算法、不做向量检索升级；
- 不推翻 ADR-0001（每日会话归档）、ADR-0002（检索层抽象）既有决策；
- 不做 plugin / 独立应用形态迁移（spec 演进路线方向不变）；
- 不改 skill 名称 `python-coach`。

---

## 16. 风险与连锁影响

- `profile.py` 表格加列 → 旧画像文件（无新列）解析容错需保留（旧行跳列不崩溃），与现有"坏行跳过"策略一致；
- 新增知识点通道放宽矩阵约束 → 用 `source` 标记 + 显式确认兜住质量，避免矩阵被静默污染；
- `check.py` 三触发点会增加每次落盘的行前开销（毫秒级，可忽略）；
- rehearsal 删除 + 文档压缩 → 历史可复现性下降，由各契约"一行摘要"补偿（决策 9 已接受）；
- 多 agent/多工作区部署 → 隔离护栏 + `PYTHONDONTWRITEBYTECODE=1` 是硬要求，批次 5 不得跳过。
