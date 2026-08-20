# 09 — 摸底测试与能力矩阵

**What to build:** 范围驱动的摸底测试——15–20 题（选择题约 10–12 + 简答/实操约 5–8，覆盖范围声明内知识点，难度梯度 1–5），混合式作答（选择题对话内选、简答题贴文字/代码），agent 对照评分标准判分，产出能力矩阵（知识点 × 水平分）写入 profile.md。

**Blocked by:** 05 — 画像更新脚本；08 — 目标澄清与范围声明

**Status:** done

- [x] 摸底测试题目生成（范围驱动、难度梯度）——契约见 `resources/placement-contract.md` §3（题量/题型/难度硬约束、每题元数据、生成规则）
- [x] 混合式作答流程——§4（逐题作答、允许"不会/跳过"、不代答不提示、可回看修改）
- [x] 评分标准与判分——§5（选择题 0/1、简答/实操按评分要点 0/0.5/1、判分透明可质疑）
- [x] 能力矩阵写入画像——§6（难度加权合成公式 + `scripts/profile.py` `op=placement` 初始化矩阵，`test_profile.py` PlacementTest 自动化测试）

**验证：** 对话式流程不设自动化 seam（spec「测试 seam」），以实际演练验证——模拟出题（范围驱动、难度梯度 1–5 全覆盖）→ 混合式作答（含 1 次"不会"跳过、简答、实操）→ 对照评分标准判分 → 难度加权合成 → `profile.py op=placement` 写矩阵（退出码 0）→ 检查 `profile.md` 原文（初始矩阵行来源「摸底测试」+ 增量记录）。演练记录见 `resources/placement-contract.md` §8；演练产物存于 `.scratch/python-coach/rehearsal-09/`。矩阵写入路径另有 `scripts/test_profile.py` 的 PlacementTest 自动化测试（创建初始化 / 覆盖既有行 / 0.5 舍入与 [1,5] 截断 / 重复知识点与非法输入报错 / CLI）。
