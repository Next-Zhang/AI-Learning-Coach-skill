# python-coach
一个 ai 学习助手工具（skill 阶段）：**python-coach** —— AI 学习教练。

## 结构

- `SKILL.md`：技能主文件——五阶段闭环主流程（计划 → 执行 → 反馈 → 验收 → 总结 → 复习）与「护栏」章节（rules / 工作区与记忆隔离 / permission / approval）。
- `resources/data-formats.md`：六件套持久层数据格式约定（plan.md / progress.md / profile.md / sources/ / review/ / review/schedule.md），含 frontmatter 元数据规范与「工作区目录结构」（`.python-coach/{state,tmp}` 三类区 + 过程文件生命周期）。
- `resources/retrieval-contract.md`：检索层契约（ticket 02）——输入查询 → 输出资料列表的输入输出格式、评分规则与用法。
- `resources/schedule-contract.md`：间隔重复调度契约（ticket 03）——掌握度/考察结果 → 下次复习日（1→3→7→15→30 天）的输入输出格式、调度规则与用法。
- `resources/completion-contract.md`：完成度合成契约（ticket 04）——agent 评分与自评（7:3）→ 完成度分（0.5 档）的输入输出格式、合成规则与用法；难度反馈独立记录。
- `resources/profile-contract.md`：画像更新契约（ticket 05）——onboarding 问卷 / 验收完成度 / 复习考察得分 → 能力矩阵增量修正的输入输出格式、更新规则与用法；难度反馈入增量记录。
- `resources/page-contract.md`：当日执行网页生成契约（ticket 06）——plan.md + 当日任务 → 单文件静态 HTML（自包含、可离线打开，含知识/链路/目标/来源四区块）的输入输出格式、知识内容来源与用法。
- `resources/onboarding-contract.md`：onboarding 问卷流程契约（ticket 07）——对话式 8 题问卷的对话协议（一问一答、校验、中途修改、汇总确认）与写画像初值流程。
- `resources/goal-scope-contract.md`：目标澄清与范围声明流程契约（ticket 08）——起步流程第 2 步的对话协议（一句话目标澄清、子领域圈定、覆盖/不涉及范围声明、写 plan.md 草案）。
- `resources/placement-contract.md`：摸底测试流程契约（ticket 09）——起步流程第 3 步的对话协议（范围驱动的 15–20 题：选择 10–12 + 简答/实操 5–8、难度梯度 1–5；混合式作答；评分标准与判分；难度加权合成能力矩阵并写入画像）。
- `resources/plan-contract.md`：计划生成与三验证流程契约（ticket 10）——起步流程第 4 步的对话协议（按天划分、含来源引用的草案生成；独立评审 agent 三验证：真实性/合理性/适配性；评审→修订→再评审循环轮次上限 3；通过后落盘 `plan.md` 为 `active`）。
- `resources/session-start-contract.md`：每日会话开始流程契约（ticket 11）——会话开头的对话编排（复习检查：到期知识点一问一答考察、考察结果单确认后成对写回调度表与能力矩阵；新课开头随机抽查 2 个历史知识点热场不计分；当日网页生成；执行辅助的范围约束与来源引用）。
- `resources/acceptance-contract.md`：验收、当日总结与网页清除流程契约（ticket 12）——当日收尾的对话编排（证据提交 → 逐目标核查 → 结论三档（完成/部分完成/未完成 + 理由）→ 完成度合成与难度采集（`completion.py`，难度独立不参与分数）→ 学习者确认 → 验收结果写回画像（`profile.py op=acceptance`）→ 当日总结写入 `progress.md` → 提出删除当日网页、确认后清除）。
- `resources/review-contract.md`：复习快查文档契约（ticket 13）——按课程一份生成 `review/NN-主题.md`（`review.py op=generate`），按知识点/日期查阅（`op=query`），把新知识点纳入调度表的 `schedule_add` 建议 + `schedule.py op=add` 两步更新，以及向当日课追加矩阵外新知识点行（`op=append`，批次 4 新增通道三同步之一）；与 `progress.md` 职责分离。
- `resources/check-contract.md`：自动核对契约（修订批次 3）——`check.py` 对 plan ↔ 能力矩阵 ↔ progress 证据 ↔ decision-log 的机械引用/口径一致性校验（error/warning 问题清单，不硬阻塞；三触发点：计划落盘前 / 每日行前 / 验收写回前）。
- `scripts/`：纯逻辑脚本（测试 seam）——`retrieve.py` 检索层（`test_retrieve.py` 为其测试）、`schedule.py` 复习调度（`test_schedule.py` 为其测试）、`completion.py` 完成度合成（`test_completion.py` 为其测试）、`profile.py` 画像更新（onboarding 问卷初值、摸底初始矩阵、验收/复习增量修正、矩阵外显式新增 `add_new`；`test_profile.py` 为其测试）、`page.py` 当日执行网页生成（`test_page.py` 为其测试）、`review.py` 复习快查文档生成/查阅/当日课追加（`test_review.py` 为其测试；generate 输出 `schedule_add` 接 `schedule.py add` 完成调度表更新，append 向当日课追加矩阵外新知识点行——批次 4 新增通道三同步之一）、`check.py` 自动核对（计划/矩阵/进度/决策日志的引用一致性；`test_check.py` 为其测试）。对话式流程（起步各步、验收）不设自动化 seam，构建时经实际演练验证（演练摘要见各流程契约「验证方式」）。
- `templates/`：六件套数据文件初始模板（首次起步按模板初始化六件套到 `.python-coach/state/`，模板路径不变）。
- `docs/adr/`：设计决策记录（ADR-0001 每日会话归档；ADR-0002 检索层抽象）。
- `CONTEXT.md`：领域词汇表（20 术语）。
- `.scratch/python-coach/`：规格与开发票据（spec.md + issues/01–13）。

## 工作区目录（使用期）

技能本体（本仓库）只读；学习数据落在**学习者工作区**内（每个工作区独立）：

- `.python-coach/state/`：六件套正式状态（plan / progress / profile / sources / review / review 的 schedule）。
- `.python-coach/tmp/`：会话过程文件（初始化 JSON、草稿、评审出入包、自检副本、脚本 in/out JSON）→ 阶段完成即清。
- `exercises/`、`project/`：每日练习与最终项目交付物（persistent，按需读取）。

使用阶段一律按 `resources/data-formats.md` 的路径约定显式传 `.python-coach/state/…` 路径。

## 安装与分发

- **打包清单**：`SKILL.md + resources/ + scripts/（含测试与 testdata 夹具）+ templates/ + docs/ + CONTEXT.md`；**剔除 `.scratch/`、`.git/`**（开发票据与版本库不进技能包）。
- **安装**：把打包清单内容复制到技能库目录（DeepSeek Harness 默认 `~/.dsh/skills/python-coach/`）；skill 名称保持 `python-coach`（决策 10），不重命名目录与引用。
- **多 agent / 多工作区部署**：每个工作区各自建 `.python-coach/`（state / tmp 数据目录），数据互不共享——对应 SKILL.md「工作区与记忆隔离」护栏。
- **运行期不写技能目录**：`scripts/` 各脚本内置 `sys.dont_write_bytecode = True`（等价 `PYTHONDONTWRITEBYTECODE=1`），运行不产生 `__pycache__`，安装目录保持只读。

## 使用

在 DeepSeek Harness 中输入 `python-coach` 开始一个学习日会话。首次使用会走「起步流程」：onboarding 问卷 → 目标澄清与范围声明 → 摸底测试 → 计划生成与三验证。
