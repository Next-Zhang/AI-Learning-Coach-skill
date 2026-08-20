# AI-Learning-Coach-skill
一个 ai 学习助手工具（skill 阶段）：**python-coach** —— AI 学习教练。

## 结构

- `SKILL.md`：技能主文件——五阶段闭环主流程（计划 → 执行 → 反馈 → 验收 → 总结 → 复习）与「护栏」章节（rules / permission / approval 三层面）。
- `resources/data-formats.md`：六件套持久层数据格式约定（plan.md / progress.md / profile.md / sources/ / review/ / review/schedule.md），含 frontmatter 元数据规范。
- `resources/retrieval-contract.md`：检索层契约（ticket 02）——输入查询 → 输出资料列表的输入输出格式、评分规则与用法。
- `resources/schedule-contract.md`：间隔重复调度契约（ticket 03）——掌握度/考察结果 → 下次复习日（1→3→7→15→30 天）的输入输出格式、调度规则与用法。
- `resources/completion-contract.md`：完成度合成契约（ticket 04）——agent 评分与自评（7:3）→ 完成度分（0.5 档）的输入输出格式、合成规则与用法；难度反馈独立记录。
- `resources/profile-contract.md`：画像更新契约（ticket 05）——onboarding 问卷 / 验收完成度 / 复习考察得分 → 能力矩阵增量修正的输入输出格式、更新规则与用法；难度反馈入增量记录。
- `resources/onboarding-contract.md`：onboarding 问卷流程契约（ticket 07）——对话式 8 题问卷的对话协议（一问一答、校验、中途修改、汇总确认）与写画像初值流程。
- `resources/page-contract.md`：当日执行网页生成契约（ticket 06）——plan.md + 当日任务 → 单文件静态 HTML（自包含、可离线打开，含知识/链路/目标/来源四区块）的输入输出格式、知识内容来源与用法。
- `scripts/`：纯逻辑脚本（测试 seam）——`retrieve.py` 检索层（`test_retrieve.py` 为其测试）、`schedule.py` 复习调度（`test_schedule.py` 为其测试）、`completion.py` 完成度合成（`test_completion.py` 为其测试）、`profile.py` 画像更新（`test_profile.py` 为其测试）、`page.py` 当日执行网页生成（`test_page.py` 为其测试）。
- `templates/`：六件套数据文件初始模板（初始化项目数据时按模板生成）。
- `docs/adr/`：设计决策记录（ADR-0001 每日会话归档；ADR-0002 检索层抽象）。
- `CONTEXT.md`：领域词汇表（20 术语）。
- `.scratch/python-coach/`：规格与开发票据（spec.md + issues/01–13）。

## 使用

在 DeepSeek Harness 中输入 `python-coach` 开始一个学习日会话。首次使用会走「起步流程」：onboarding 问卷 → 目标澄清与范围声明 → 摸底测试 → 计划生成与三验证。
