# AI-Learning-Coach-skill
一个 ai 学习助手工具（skill 阶段）：**python-coach** —— AI 学习教练。

## 结构

- `SKILL.md`：技能主文件——五阶段闭环主流程（计划 → 执行 → 反馈 → 验收 → 总结 → 复习）与「护栏」章节（rules / permission / approval 三层面）。
- `resources/data-formats.md`：六件套持久层数据格式约定（plan.md / progress.md / profile.md / sources/ / review/ / review/schedule.md），含 frontmatter 元数据规范。
- `resources/retrieval-contract.md`：检索层契约（ticket 02）——输入查询 → 输出资料列表的输入输出格式、评分规则与用法。
- `scripts/`：纯逻辑脚本（测试 seam）——`retrieve.py` 检索层（`test_retrieve.py` 为其测试）；ticket 03–06 的调度/合成/画像/网页脚本将陆续加入。
- `templates/`：六件套数据文件初始模板（初始化项目数据时按模板生成）。
- `docs/adr/`：设计决策记录（ADR-0001 每日会话归档；ADR-0002 检索层抽象）。
- `CONTEXT.md`：领域词汇表（20 术语）。
- `.scratch/python-coach/`：规格与开发票据（spec.md + issues/01–13）。

## 使用

在 DeepSeek Harness 中输入 `python-coach` 开始一个学习日会话。首次使用会走「起步流程」：onboarding 问卷 → 目标澄清与范围声明 → 摸底测试 → 计划生成与三验证。
