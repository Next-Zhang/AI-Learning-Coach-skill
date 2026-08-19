# 02 — 检索层脚本

**What to build:** 检索层的 v0 实现——统一契约（输入查询 → 输出资料列表：标题/来源/摘要/链接），基于 sources/ 关键词检索（glob/grep）+ web_search/web_fetch 补充。脚本以「读输入文件 → 写输出文件」形式提供，附带测试。

**Blocked by:** 01 — 技能骨架与持久层数据格式

**Status:** ready-for-agent

- [x] 检索层契约输入输出格式定义
- [x] 关键词检索实现（sources/ 内检索）
- [x] web 检索补充实现
- [x] 样例输入输出测试通过
