#!/usr/bin/env python3
"""画像更新脚本（ticket 05）——用户画像（profile.md）的增量更新逻辑。

用法：
    python profile.py <input.json> <output.json>

输入输出格式、更新规则与用法见 ../resources/profile-contract.md。

四种操作（输入文件 op 字段）：
- onboarding：onboarding 问卷结果（8 题）写入画像初值；画像文件不存在时创建；
- placement：摸底测试结果（知识点 × 水平分）初始化能力矩阵（来源「摸底测试」）；
  画像文件不存在时创建；results 内知识点行整体覆盖，其余行保留；
- acceptance：记录一次验收结果（完成度 + 难度反馈）→ 能力矩阵增量修正
  （完成度 ≥ 4 → 该知识点 +0.5，上限 5；难度反馈独立记录，不改变矩阵数值）；
- review：记录一次复习考察结果 → 能力矩阵写回（通过 +0.5 上限 5；
  未通过 -0.5 下限 1），与 scripts/schedule.py 的掌握度推进同一规则。

本脚本原地读写 profile.md（能力矩阵 + 增量记录 + frontmatter updated）；
难度反馈只在增量记录中留痕，不写入矩阵数值（spec「完成度评分」：
难度反馈只影响后续计划难度档位）。
"""
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

# 能力矩阵增量规则（与 schedule.py 掌握度推进同一增量，保持两处同步）
ACCEPT_THRESHOLD = 4.0      # 验收完成度 ≥ 4 → 该知识点 +0.5
PASS_DELTA = 0.5            # 验收高分 / 复习通过 的增量
FAIL_DELTA = 0.5            # 复习未通过 的减量
LEVEL_MIN = 1.0
LEVEL_MAX = 5.0
PLACEMENT_SOURCE = "摸底测试"  # 摸底初始矩阵的「来源」列与日志事件名
# 难度反馈封闭集合（独立记录，不参与矩阵数值）
DIFFICULTY_LEVELS = ("太难", "刚好", "太简单")

TITLE = "# 用户画像"
ONBOARDING_HEADER = "## Onboarding 问卷（8 题）"
MATRIX_HEADER = "## 能力矩阵（知识点 × 水平分 1–5）"
LOG_HEADER = "## 增量记录"
MATRIX_HEADER_ROW = "| 知识点 | 水平分 | 更新时间 | 来源 |"
MATRIX_SEPARATOR = "| --- | --- | --- | --- |"

# onboarding 固定 8 题（label, 是否 1–5 数值自评）；字段名保持稳定
ONBOARDING_FIELDS = (
    ("学习目标", False),
    ("Python 水平自评（1–5）", True),
    ("每日时间预算", False),
    ("学习风格偏好", False),
    ("压力承受自评（1–5）", True),
    ("期望节奏", False),
    ("过往经历", False),
    ("复习意愿", False),
)


# --- 数值与日期辅助 ---


def _number_text(value):
    """数值展示：整数去小数点（2.0 → "2"，2.5 → "2.5"）。"""
    return f"{value:g}"


def _parse_level(cell):
    """`x/5` → float(x)；也接受裸数字。解析失败返回 None。"""
    text = cell.split("/", 1)[0].strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _clamp_level(value, field):
    """水平分解析与截断：数字 → [1, 5]；非法值报错（与 schedule.py 同一策略）。"""
    try:
        level = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} 必须是数字：{value!r}")
    return min(LEVEL_MAX, max(LEVEL_MIN, level))


def _round_half(value):
    """水平分规范到 0.5 档（半向上舍入，如 2.25 → 2.5、2.75 → 3.0）。

    能力矩阵的水平分统一按 0.5 档记录（增量 ±0.5 同档）；
    摸底合成结果经本函数兜底规范化，保证矩阵行格式稳定。
    """
    return math.floor(value * 2 + 0.5) / 2


def _parse_date(value):
    """date 字段：缺省取系统日期；显式值必须为 YYYY-MM-DD（自动规范补零）。"""
    if value is None:
        return date.today().isoformat()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"date 必须是 YYYY-MM-DD 日期：{value!r}")


def _require_topic(req):
    topic = req.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("需要非空 topic 字段（acceptance/review/placement）")
    topic = topic.strip()
    if "|" in topic or "\n" in topic:
        raise ValueError("知识点名不能包含 | 或换行（表格格式约束）")
    return topic


def _source_text(value, default):
    """来源字段：缺省/空串 → 默认来源；否则取去首尾空白的文本。"""
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"source 必须是文本：{value!r}")
    return value.strip() or default


# --- profile.md 解析与渲染 ---


def _parse_matrix_row(line):
    """解析一行矩阵行 `| topic | level | date | source |` → dict；失败返回 None。

    容错：单元格个数不对、水平分/日期无法解析的行一律跳过（与调度表解析同一策略）；
    表头行与分隔行的水平分不是数字，自然被跳过。
    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != 4:
        return None
    topic, level, updated, source = cells
    if not topic:
        return None
    level = _parse_level(level)
    if level is None:
        return None
    try:
        # 统一规范为 YYYY-MM-DD，保证字符串比较与写入格式一致
        updated = datetime.strptime(updated, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None
    return {"topic": topic, "level": level, "date": updated, "source": source}


def parse_profile(text):
    """解析画像文本 → {created, updated, onboarding, matrix, log}。

    - onboarding：Onboarding 问卷区块下的逐行原文（非空行）；
    - matrix：能力矩阵表格行 [{topic, level, date, source}]，坏行跳过；
    - log：增量记录区块的逐行原文（跳过空行与模板占位注释）。
    无 frontmatter / 缺区块均可解析（写回时补齐结构）。
    """
    created = updated = None
    onboarding = []
    matrix = []
    log = []

    lines = text.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        frontmatter = []
        while i < len(lines) and lines[i].strip() != "---":
            frontmatter.append(lines[i])
            i += 1
        if i < len(lines):
            i += 1  # 跳过闭合 ---
        for line in frontmatter:
            key, _, value = line.partition(":")
            if key.strip() == "created":
                created = value.strip() or None
            elif key.strip() == "updated":
                updated = value.strip() or None

    section = None
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == ONBOARDING_HEADER:
            section = "onboarding"
        elif stripped == MATRIX_HEADER:
            section = "matrix"
        elif stripped == LOG_HEADER:
            section = "log"
        elif stripped.startswith("## "):
            section = None
        elif section == "onboarding":
            if stripped:
                onboarding.append(lines[i])
        elif section == "matrix":
            row = _parse_matrix_row(stripped)
            if row is not None:
                matrix.append(row)
        elif section == "log":
            if stripped and not stripped.startswith("<!--"):
                log.append(lines[i])
        i += 1
    return {
        "created": created,
        "updated": updated,
        "onboarding": onboarding,
        "matrix": matrix,
        "log": log,
    }


def render_profile(data, updated):
    """画像数据 → profile.md 全文。created 缺失时取 updated；矩阵/日志保持既有行。"""
    created = data["created"] or updated
    lines = [
        "---",
        f"created: {created}",
        f"updated: {updated}",
        "---",
        "",
        TITLE,
        "",
        ONBOARDING_HEADER,
    ]
    if data["onboarding"]:
        lines.extend(data["onboarding"])
    else:
        # 尚无问卷内容时输出空占位（与 templates/profile.md 一致）
        for label, _ in ONBOARDING_FIELDS:
            lines.append(f"- {label}：")
    lines.extend(["", MATRIX_HEADER, MATRIX_HEADER_ROW, MATRIX_SEPARATOR])
    for row in data["matrix"]:
        lines.append(
            f"| {row['topic']} | {_number_text(row['level'])} | "
            f"{row['date']} | {row['source']} |"
        )
    lines.extend(["", LOG_HEADER])
    if data["log"]:
        lines.extend(data["log"])
    return "\n".join(lines) + "\n"


def read_profile(path):
    """读画像文件 → 解析结果；文件不存在时抛 FileNotFoundError。"""
    return parse_profile(Path(path).read_text(encoding="utf-8"))


def write_profile(path, data, updated):
    """把画像数据原地写回 profile.md。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_profile(data, updated), encoding="utf-8")


def _load_profile_or_empty(path):
    """读画像；文件不存在时视为空画像（onboarding/placement 首次创建场景共用）。"""
    if not Path(path).exists():
        return parse_profile("")
    return read_profile(path)


# --- 四种操作 ---


def _find_topic(data, topic):
    idx = next((i for i, r in enumerate(data["matrix"]) if r["topic"] == topic), None)
    if idx is None:
        raise ValueError(f"知识点不在能力矩阵中（先经摸底测试初始化）：{topic}")
    return idx


def _apply_delta(data, topic, delta, day, source, detail):
    """对能力矩阵某知识点应用增量并追加增量记录（acceptance/review 共用）。

    delta：期望增量（0 表示不变化，如验收未达阈值）；detail：括号内详情文本；
    source：矩阵「来源」列与日志事件名。数值实际截断在 [1, 5]，因此已达
    上限/下限时 updated=False、日志记「矩阵不变」。
    """
    idx = _find_topic(data, topic)
    old = data["matrix"][idx]["level"]
    new = min(LEVEL_MAX, max(LEVEL_MIN, old + delta))
    updated = new != old
    if updated:
        data["matrix"][idx] = {
            "topic": topic,
            "level": new,
            "date": day,
            "source": source,
        }
    if updated:
        sign = "+" if delta > 0 else "-"
        entry = (
            f"- {day}：{source}（{detail}）→ {topic} "
            f"{sign}{_number_text(abs(delta))}（{_number_text(old)}→{_number_text(new)}）"
        )
    else:
        entry = f"- {day}：{source}（{detail}）→ {topic} 矩阵不变"
    data["log"].append(entry)
    return {
        "topic": topic,
        "source": source,
        "old_score": old,
        "new_score": new,
        "delta": new - old,
        "updated": updated,
        "log_entry": entry,
    }


def _run_onboarding(req, data, day):
    """onboarding：问卷 8 题答案写入画像初值（替换既有问卷、保留矩阵与日志）。"""
    answers = req.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("onboarding 需要 answers 对象（8 题答案）")
    labels = dict(ONBOARDING_FIELDS)
    missing = [label for label in labels if label not in answers]
    if missing:
        raise ValueError(f"onboarding 缺少问卷字段：{'、'.join(missing)}")
    extra = [key for key in answers if key not in labels]
    if extra:
        raise ValueError(f"onboarding 含未知问卷字段：{'、'.join(extra)}")

    bullets = []
    normalized = {}
    for label, numeric in ONBOARDING_FIELDS:
        value = answers[label]
        if numeric:
            level = _clamp_level(value, label)
            text = _number_text(level)
        elif isinstance(value, (int, float)):
            text = _number_text(value)
        elif isinstance(value, str):
            text = value.strip()
        else:
            raise ValueError(f"{label} 必须是文本或数字：{value!r}")
        if not text:
            raise ValueError(f"{label} 不能为空")
        bullets.append(f"- {label}：{text}")
        normalized[label] = text

    data["onboarding"] = bullets
    data["log"].append(f"- {day}：onboarding 问卷 → 画像初值")
    return {"answers": normalized, "created": data["created"] or day, "updated": day}


def _run_placement(req, data, day):
    """placement：摸底测试结果（知识点 × 水平分）初始化能力矩阵。

    results = [{topic, score}]；topic 须非空且不重复，score 为数字（[1, 5] 截断
    + 0.5 档舍入兜底）。results 内知识点行整体按新值覆盖（来源「摸底测试」、
    日期 = day），其余行保留；日志追加一条「摸底测试 → 初始矩阵」。
    """
    results = req.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("placement 需要非空 results 数组（[{topic, score}]）")
    entries = []
    seen = set()
    for item in results:
        if not isinstance(item, dict):
            raise ValueError("placement 的 results 元素必须是对象（{topic, score}）")
        topic = _require_topic(item)
        if topic in seen:
            raise ValueError(f"placement 的 results 含重复知识点：{topic}")
        seen.add(topic)
        entries.append(
            {
                "topic": topic,
                "level": _round_half(_clamp_level(item.get("score"), "score")),
                "date": day,
                "source": PLACEMENT_SOURCE,
            }
        )

    for entry in entries:
        idx = next(
            (i for i, r in enumerate(data["matrix"]) if r["topic"] == entry["topic"]),
            None,
        )
        if idx is None:
            data["matrix"].append(entry)
        else:
            data["matrix"][idx] = entry

    log_entry = f"- {day}：{PLACEMENT_SOURCE} → 初始矩阵"
    data["log"].append(log_entry)
    # 输出视图与矩阵行同源（矩阵行键为 level，输出契约键为 score）
    matrix = [
        {
            "topic": entry["topic"],
            "score": entry["level"],
            "date": entry["date"],
            "source": entry["source"],
        }
        for entry in entries
    ]
    return {
        "matrix": matrix,
        "count": len(matrix),
        "created": data["created"] or day,
        "log_entry": log_entry,
    }


def _run_acceptance(req, data, day):
    """acceptance：验收完成度 ≥ 4 → 知识点 +0.5（上限 5）；难度反馈入日志不改矩阵。"""
    topic = _require_topic(req)
    score = _clamp_level(req.get("score"), "score")
    difficulty = req.get("difficulty")
    if difficulty is not None and difficulty not in DIFFICULTY_LEVELS:
        raise ValueError(
            f"difficulty 必须是 {'/'.join(DIFFICULTY_LEVELS)} 之一：{difficulty!r}"
        )
    source = _source_text(req.get("source"), "验收")
    delta = PASS_DELTA if score >= ACCEPT_THRESHOLD else 0.0
    detail = f"完成度 {_number_text(score)}"
    if difficulty is not None:
        detail += f"，难度 {difficulty}"
    out = _apply_delta(data, topic, delta, day, source, detail)
    out.update({"score": score, "difficulty": difficulty})
    return out


def _run_review(req, data, day):
    """review：复习考察通过 +0.5（上限 5）/ 未通过 -0.5（下限 1），写回能力矩阵。"""
    topic = _require_topic(req)
    result = req.get("result")
    if result not in ("pass", "fail"):
        raise ValueError('review 需要 result 字段（"pass" / "fail"）')
    source = _source_text(req.get("source"), "复习考察")
    delta = PASS_DELTA if result == "pass" else -FAIL_DELTA
    detail = "通过" if result == "pass" else "未通过"
    out = _apply_delta(data, topic, delta, day, source, detail)
    out.update({"result": result})
    return out


# --- 文件契约入口 ---


def _resolve_profile_path(req, input_path):
    """profile_path 字段：默认 profile.md；相对路径以输入文件所在目录为基准。"""
    path = Path(req.get("profile_path", "profile.md"))
    if not path.is_absolute():
        path = input_path.parent / path
    return path


def run(input_path, output_path):
    """文件契约入口：读输入 JSON → 画像更新 → 写输出 JSON（并原地改写画像文件）。

    输入字段：date（可选，默认系统日期）、profile_path（可选，默认 "profile.md"，
    相对路径以输入文件所在目录为基准）、op（必填："onboarding" | "placement" |
    "acceptance" | "review"）；onboarding 另需 answers（8 题），placement 另需
    results（[{topic, score}]），acceptance 另需 topic/score（difficulty/source
    可选），review 另需 topic/result。
    """
    input_path = Path(input_path)
    req = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(req, dict):
        raise ValueError("输入 JSON 必须是对象")
    day = _parse_date(req.get("date"))
    profile_path = _resolve_profile_path(req, input_path)
    op = req.get("op")
    handlers = {
        "onboarding": _run_onboarding,
        "placement": _run_placement,
        "acceptance": _run_acceptance,
        "review": _run_review,
    }
    if op not in handlers:
        raise ValueError(
            "输入缺少 op 字段（" + " / ".join(f'"{k}"' for k in handlers) + "）"
        )

    if op in ("onboarding", "placement"):
        data = _load_profile_or_empty(profile_path)
    else:
        if not profile_path.exists():
            raise FileNotFoundError(f"画像文件不存在：{profile_path}")
        data = read_profile(profile_path)
    result = handlers[op](req, data, day)

    write_profile(profile_path, data, day)
    out = {"op": op, "date": day, **result}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def main(argv=None):
    """CLI 入口：python profile.py <input.json> <output.json>。"""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        sys.stderr.write(
            "用法：python profile.py <input.json> <output.json>\n"
            "契约见 ../resources/profile-contract.md\n"
        )
        return 2
    try:
        run(argv[0], argv[1])
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"画像更新失败：{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
