# 08 — 目标澄清与范围声明

**What to build:** 对话式目标澄清——学习者用一句话说出"想用 Python 做什么"的具体目标 → agent 圈定所需子领域 → 生成显式范围声明（覆盖什么、不涉及什么），写入 plan 草案。范围声明是检索源选择、验证评审对象、失控防护锚点。

**Blocked by:** 01 — 技能骨架与持久层数据格式

**Status:** done

- [x] 目标澄清对话流程（一句话目标）——契约见 `resources/goal-scope-contract.md` §3（起点为画像「学习目标」，具体性检查，追问上限 3 轮）
- [x] 子领域圈定逻辑——§4（必需/前置裁剪/3–7 个上限/检索查证/学习者确认）
- [x] 范围声明生成（覆盖/不涉及）——§5（scope_excluded 只排"易被误期待"领域，1–3 个，确认后落盘）
- [x] 写入 plan 草案——§6（`status: draft` + 空每日任务；已落盘计划重走起步的覆盖语义；approval 护栏）

**验证：** 对话式流程不设自动化 seam（spec「测试 seam」），以实际演练验证——模拟澄清对话（模糊目标追问 → 定稿）→ 圈定/确认范围 → 写草案 → 按 `page.py` 解析规则核对可解析（演练记录见 `resources/goal-scope-contract.md` §8；演练产物存于 `.scratch/python-coach/rehearsal-08/`）。
