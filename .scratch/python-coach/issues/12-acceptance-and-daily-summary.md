# 12 — 验收、当日总结与网页清除

**What to build:** 每日任务验收流程——学习者提交当日证据 → agent 对照当日目标核查给结论（完成/部分完成/未完成 + 理由）→ 完成度合成（7:3）→ 学习者确认 → 写当日总结入 progress.md → 提出删除当日网页、学习者确认后清除。

**Blocked by:** 04 — 完成度合成脚本；05 — 画像更新脚本；11 — 每日会话开始

**Status:** done

- [x] 证据提交与核查流程——契约见 `resources/acceptance-contract.md` §3（逐项目标核查、判定与证据依据、结论三档（完成/部分完成/未完成）+ 理由；结论与分数的对应见 §4.1）
- [x] 完成度合成 + 难度反馈采集——§4（agent 与自评独立打分 → `completion.py` 合成（7:3、0.5 档）并展示算式；难度单独采集、独立记录不参与分数）
- [x] 学习者确认环节——§5（验收单确认/质疑；复核修正→重跑合成；难度与完成度语义澄清；确认后才写）
- [x] 验收结果写回画像——§6（`profile.py op=acceptance` 逐一写回当日知识点（同分同难度）；写回清单先确认；≥4 加 0.5 上限 5）
- [x] 当日总结写入 progress.md——§7（起草总结块 → 展示确认 → 追加 `progress.md` 尾并更新 frontmatter，不重构历史）
- [x] 网页删除（确认后）——§8（提出删除说明影响 → 学习者确认后删（approval）；拒绝则保留）

**验证：** 对话式流程不设自动化 seam（spec「测试 seam」），以**实际演练**验证——本次构建演练 Day 5 晚间场景（`rehearsal-12/`）：前置数据延续 rehearsal-11 早晨产物 + 补 Day 1–4 进度 → 证据提交（read_excel/to_excel/sheet_name 小程序代码+运行结果）→ 逐项目标核查（3/3 达成，结论「完成」）→ `completion.py` 真实合成（agent 4 / 自评 5 → 4.5/5，`0.7 × 4 + 0.3 × 5 ≈ 4.5`，难度「太难」）→ 学习者质疑评分与难度语义 → agent 复核维持（难度不参与完成度、loc 纠错计入评分理由）→ 确认 → `profile.py op=acceptance` 真实写回（Excel 读写 3→3.5，难度「太难」入日志）→ 总结块确认后追加 `progress.md`（与 before diff 仅尾加 + updated）→ 提出删除当日网页、学习者确认后删除。详细转写与脚本记录见 `rehearsal-12/rehearsal-log.md`；契约 `resources/acceptance-contract.md` §10。
