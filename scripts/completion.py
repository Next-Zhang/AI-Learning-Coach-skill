#!/usr/bin/env python3
"""完成度合成脚本（ticket 04）——agent 评分与学习者自评按 7:3 合成完成度分。

用法：
    python completion.py <input.json> <output.json>

输入输出格式、合成规则与用法见 ../resources/completion-contract.md。

合成规则（spec「混合式验收与完成度」+ SKILL.md「反馈与验收」）：
- 完成度分 = 0.7 × agent 评分 + 0.3 × 学习者自评，四舍五入到 0.5 档，截断在 [1, 5]；
- 难度反馈（太难 / 刚好 / 太简单）独立记录，不参与完成度分，只影响后续计划难度档位。

评分先折算为百分位整数，此后全程整数运算（加权和以 1/1000 分表示），
取整到 0.5 档用 half-up（x.25 进到 x.5），避免浮点取整边界误差。
"""
import json
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
from pathlib import Path

# 合成权重（7:3；以十分位整数运算，见 synthesize 注释）
WEIGHT_AGENT = 7
WEIGHT_SELF = 3
SCORE_MIN = 1.0
SCORE_MAX = 5.0
# 难度反馈封闭集合（独立记录，不参与完成度分）
DIFFICULTY_LEVELS = ("太难", "刚好", "太简单")


def _clamp_score(value, field):
    """分数解析与截断：数字（或数字字符串）→ [1, 5]；非法值报错。

    与 schedule.py 的 mastery 处理同一策略：可解析的数字超出范围自动截断，
    不可解析的（缺字段/非数字）报错，防止脏数据进入完成度分。
    """
    try:
        score = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} 必须是数字：{value!r}")
    return min(SCORE_MAX, max(SCORE_MIN, score))


def _number_text(value):
    """数值展示：整数去小数点（4.0 → "4"，4.5 → "4.5"）。"""
    return f"{value:g}"


def _to_hundredths(value):
    """评分 → 百分位整数（1/100 分）。只在折算时接触浮点，此后全程整数运算。"""
    return round(value * 100)


def synthesize(agent, self_score):
    """按 0.7×agent + 0.3×自评 合成 → (raw, score)。

    - raw：未取整的合成值（输入评分按百分位折算，结果精确到百分位）；
    - score：完成度分 = raw 四舍五入到 0.5 档（half-up，x.25 进到 x.5），截断在 [1, 5]。

    评分折算为百分位整数后全程整数运算：
    W10 = 7×agent_c + 3×self_c（= 合成值 × 1000，因 0.7 = 7/10、评分为百分位），
    raw = W10 / 1000；取整到 0.5 档（50 百分位）即 ((W10 + 250) // 500) × 50。
    """
    w10 = (
        WEIGHT_AGENT * _to_hundredths(agent)
        + WEIGHT_SELF * _to_hundredths(self_score)
    )
    raw = w10 / 1000
    rounded = ((w10 + 250) // 500) * 50
    score = min(SCORE_MAX, max(SCORE_MIN, rounded / 100))
    return raw, score


def _synthesis_line(agent, self_score, raw, score):
    """合成算式文本：`0.7 × 4 + 0.3 × 4 = 4`；取整后与 raw 不一致时用 ≈。"""
    expr = f"0.7 × {_number_text(agent)} + 0.3 × {_number_text(self_score)}"
    sep = "=" if raw == score else "≈"
    return f"{expr} {sep} {_number_text(score)}"


def run(input_path, output_path):
    """文件契约入口：读输入 JSON → 合成 → 写输出 JSON。

    输入字段：agent_score（必填，1–5，超出自动截断）、self_score（必填，
    1–5，超出自动截断）、difficulty（可选，"太难" | "刚好" | "太简单"，
    独立记录不参与合成；缺省输出 null）。
    输出：{"agent_score", "self_score", "raw", "score", "score_display",
    "synthesis", "difficulty"}。
    """
    input_path = Path(input_path)
    req = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(req, dict):
        raise ValueError("输入 JSON 必须是对象")
    agent = _clamp_score(req.get("agent_score"), "agent_score")
    self_score = _clamp_score(req.get("self_score"), "self_score")
    difficulty = req.get("difficulty")
    if difficulty is not None and difficulty not in DIFFICULTY_LEVELS:
        raise ValueError(
            f"difficulty 必须是 {'/'.join(DIFFICULTY_LEVELS)} 之一：{difficulty!r}"
        )

    raw, score = synthesize(agent, self_score)
    out = {
        "agent_score": agent,
        "self_score": self_score,
        "raw": raw,
        "score": score,
        "score_display": f"{_number_text(score)}/5",
        "synthesis": _synthesis_line(agent, self_score, raw, score),
        "difficulty": difficulty,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def main(argv=None):
    """CLI 入口：python completion.py <input.json> <output.json>。"""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        sys.stderr.write(
            "用法：python completion.py <input.json> <output.json>\n"
            "契约见 ../resources/completion-contract.md\n"
        )
        return 2
    try:
        run(argv[0], argv[1])
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"合成失败：{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
