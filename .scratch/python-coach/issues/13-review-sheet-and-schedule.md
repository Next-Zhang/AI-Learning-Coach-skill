# 13 — 复习快查文档与调度维护

**What to build:** 课程完成后的沉淀——生成复习快查文档（按课程一份，用户可读、按知识点/日期可查阅；每个知识点：概念+代码/示例+常见坑+来源引用）；更新复习调度表（知识点 → 掌握度 → 下次复习日）。

**Blocked by:** 03 — 间隔重复调度脚本；12 — 验收、当日总结与网页清除

**Status:** done

- [x] 复习快查文档生成（可读、按课程一份）——`scripts/review.py`（`op=generate`）生成 `review/NN-主题.md`（frontmatter `course`/`date`/`topics` + 每个知识点一行：概念一句话 + 关键代码 + 常见坑 + 来源引用，行格式与 `templates/review-sheet.md` / `resources/data-formats.md` §5 同构），默认拒绝覆盖（按课程一份，`overwrite: true` 才重写）；来源为必填（护栏「引用规范」）。契约见 `resources/review-contract.md` §3。
- [x] 文档支持按知识点/日期查阅——`scripts/review.py`（`op=query`，只读）：按关键词（标题 / `topics` / 行文本，大小写不敏感）和/或日期（前后均规范为 `YYYY-MM-DD` 后匹配）检索 `review/` 下快查文档，排除调度表 `schedule.md`；无过滤时浏览全部。契约见 `resources/review-contract.md` §4。
- [x] 调度表更新（知识点/掌握度/下次复习日）——`generate` 输出 `schedule_add`（`[{topic, mastery}]`，mastery 规范到 0.5 档）建议 → 新知识点接 `scripts/schedule.py`（`op=add`）写入调度表（掌握度取能力矩阵当前值，已入表不重复 `add`，推进走 `record`）；`scripts/test_review.py` 的 `ScheduleIntegrationTest` 实测 `schedule_add` → `schedule.py add` 落盘 `review/schedule.md`。契约见 `resources/review-contract.md` §5。
- [x] 与当日总结（progress.md）职责分离——`review/` 快查文档 = 每节课的知识沉淀（用户可读、可按知识点/日期查阅）；`progress.md` = 每日总结叙事（ticket 12 追加）；`review/schedule.md` = 调度视图（agent 只查调度表决定复习什么，性能护栏）；`review.py` 不写 `progress.md`、不直接写调度表。契约见 `resources/review-contract.md` §6。

**验证：** 本票为脚本 seam，以自动化测试验证——新增 `scripts/review.py` + `scripts/test_review.py`（36 用例：生成行格式、按课程一份与 overwrite、默认目录解析、字段校验、按知识点/日期查阅与调度表排除、`schedule_add`→`schedule.py add` 调度联动、错误处理、CLI 退出码），全量测试通过（`test_retrieve` / `test_schedule` / `test_completion` / `test_profile` / `test_page` / `test_review` 全 PASS）。doc 联动：`README.md`、`SKILL.md`（反馈与验收 §7 + 复习机制）、`resources/data-formats.md` §5、`resources/session-start-contract.md` §4.1（出题依据可经 `review.py op=query` 定位快查文档）。
