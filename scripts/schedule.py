#!/usr/bin/env python3
"""间隔重复调度脚本（ticket 03）——掌握度/考察结果 → 下次复习日。

用法：
    python schedule.py <input.json> <output.json>

输入输出格式、调度规则与用法见 ../resources/schedule-contract.md。

艾宾浩斯间隔重复：1 → 3 → 7 → 15 → 30 天推进。
- 考察通过 → 掌握度 +0.5（上限 5）+ 推进到下一档间隔（30 档保持 30）；
- 考察未通过 → 掌握度 -0.5（下限 1）+ 重置回 1 天。

三种操作（输入文件 op 字段）：
- due：查到期知识点（下次复习日 ≤ today），只读；
- add：新增知识点入调度表（间隔 1、明天复习）；
- record：记录一次考察结果，推进调度并原地写回调度表。
"""
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# 间隔阶梯（艾宾浩斯：1→3→7→15→30 天）
LADDER = (1, 3, 7, 15, 30)
PASS_MASTERY_DELTA = 0.5
FAIL_MASTERY_DELTA = 0.5
MASTERY_MIN = 1.0
MASTERY_MAX = 5.0
DEFAULT_MASTERY = 2.0

TITLE = "# 复习调度表"
HEADER = "| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |"
SEPARATOR = "| --- | --- | --- | --- |"


# --- 调度表解析与渲染（review/schedule.md） ---


def _parse_mastery(cell):
    """`x/5` → float(x)；也接受裸数字。解析失败返回 None。"""
    text = cell.split("/", 1)[0].strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_row(line):
    """解析一行 `| topic | mastery | next_date | interval |` → dict；失败返回 None。

    容错：单元格个数不对、掌握度/日期/间隔无法解析的行一律跳过，
    保证调度表里个别手改坏行不拖垮整体（与资料 frontmatter 解析同一策略）。
    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != 4:
        return None
    topic, mastery, next_date, interval = cells
    if not topic:
        return None
    m = _parse_mastery(mastery)
    if m is None:
        return None
    try:
        # 统一规范为 YYYY-MM-DD，保证字符串比较与写入格式一致
        next_date = datetime.strptime(next_date, "%Y-%m-%d").date().isoformat()
        iv = int(interval)
    except ValueError:
        return None
    return {
        "topic": topic,
        "mastery": m,
        "next_date": next_date,
        "interval": iv,
    }


def parse_schedule(text):
    """解析调度表文本 → 行列表 [{topic, mastery, next_date, interval}]。

    无 frontmatter 也可解析；表格内空行透明跳过（手改留白不中断表格），
    遇到真正的非表格内容行（如另一标题）才停止。
    """
    rows = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == HEADER:
            in_table = True
            continue
        if in_table:
            if not stripped:
                continue
            if not stripped.startswith("|"):
                break
            row = _parse_row(stripped)
            if row is not None:
                rows.append(row)
    return rows


def _mastery_display(value):
    """掌握度展示：整数去小数点（2.0 → "2"，2.5 → "2.5"）。"""
    return f"{value:g}"


def render_schedule(rows, updated):
    """行列表 → 调度表 Markdown 全文（frontmatter updated + 表头 + 行）。"""
    lines = [
        "---",
        f"updated: {updated}",
        "---",
        "",
        TITLE,
        "",
        HEADER,
        SEPARATOR,
    ]
    for row in rows:
        lines.append(
            f"| {row['topic']} | {_mastery_display(row['mastery'])}/5 | "
            f"{row['next_date']} | {row['interval']} |"
        )
    return "\n".join(lines) + "\n"


def read_schedule(path):
    """读调度表文件 → 行列表。文件不存在时抛 FileNotFoundError。"""
    return parse_schedule(Path(path).read_text(encoding="utf-8"))


def write_schedule(path, rows, updated):
    """把行列表原地写回调度表文件（保持既有行顺序，新增行追加在末尾）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_schedule(rows, updated), encoding="utf-8")


# --- 日期与调度规则 ---


def add_days(date_str, days):
    """ISO 日期 + days → ISO 日期。"""
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return (d + timedelta(days=days)).isoformat()


def _parse_today(value):
    """today 字段：缺省取系统日期；显式值必须为 YYYY-MM-DD（自动规范补零）。"""
    if value is None:
        return date.today().isoformat()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"today 必须是 YYYY-MM-DD 日期：{value!r}")


def next_interval(current):
    """考察通过后的下一档间隔；已在 30 天档则保持 30。"""
    for rung in LADDER:
        if current < rung:
            return rung
    return LADDER[-1]


def apply_outcome(row, result, today):
    """记录一次考察结果 → 更新后的行（不修改入参）。

    pass：掌握度 +0.5（上限 5）、推进下一档间隔；
    fail：掌握度 -0.5（下限 1）、重置回 1 天。
    """
    delta = PASS_MASTERY_DELTA if result == "pass" else -FAIL_MASTERY_DELTA
    mastery = min(MASTERY_MAX, max(MASTERY_MIN, row["mastery"] + delta))
    interval = next_interval(row["interval"]) if result == "pass" else LADDER[0]
    return {
        "topic": row["topic"],
        "mastery": mastery,
        "next_date": add_days(today, interval),
        "interval": interval,
    }


def due_rows(rows, today):
    """到期知识点（下次复习日 ≤ today），按 日期 → 知识点 排序。"""
    return sorted(
        (r for r in rows if r["next_date"] <= today),
        key=lambda r: (r["next_date"], r["topic"]),
    )


# --- 文件契约入口 ---


def _require_topic(req):
    topic = req.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("add/record 需要非空 topic 字段")
    topic = topic.strip()
    if "|" in topic or "\n" in topic:
        raise ValueError("知识点名不能包含 | 或换行（表格格式约束）")
    return topic


def _clamp_mastery(value):
    try:
        m = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"mastery 必须是数字：{value!r}")
    return min(MASTERY_MAX, max(MASTERY_MIN, m))


def _resolve_schedule_path(req, input_path):
    """schedule_path 字段：默认 review/schedule.md；相对路径以输入文件所在目录为基准。"""
    path = Path(req.get("schedule_path", "review/schedule.md"))
    if not path.is_absolute():
        path = input_path.parent / path
    return path


def _load_rows_or_empty(path):
    """读调度表；文件不存在时视为空表（due / add 共用）。"""
    if not Path(path).exists():
        return []
    return read_schedule(path)


def run(input_path, output_path):
    """文件契约入口：读输入 JSON → 调度操作 → 写输出 JSON（add/record 另原地写调度表）。

    输入字段：today（可选，默认系统日期）、schedule_path（可选，默认
    "review/schedule.md"，相对路径以输入文件所在目录为基准）、op（必填：
    "due" | "add" | "record"）；add 另需 topic/mastery（可选默认 2.0），
    record 另需 topic/result（"pass" | "fail"）。
    """
    input_path = Path(input_path)
    req = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(req, dict):
        raise ValueError("输入 JSON 必须是对象")
    today = _parse_today(req.get("today"))
    schedule_path = _resolve_schedule_path(req, input_path)
    op = req.get("op")
    if op not in ("due", "add", "record"):
        raise ValueError('输入缺少 op 字段（"due" / "add" / "record"）')

    if op == "due":
        rows = _load_rows_or_empty(schedule_path)
        result = {"op": "due", "today": today, "due": due_rows(rows, today)}
    elif op == "add":
        topic = _require_topic(req)
        mastery = _clamp_mastery(req.get("mastery", DEFAULT_MASTERY))
        rows = _load_rows_or_empty(schedule_path)
        if any(r["topic"] == topic for r in rows):
            raise ValueError(f"知识点已在调度表中：{topic}")
        new_row = {
            "topic": topic,
            "mastery": mastery,
            "next_date": add_days(today, LADDER[0]),
            "interval": LADDER[0],
        }
        rows.append(new_row)
        write_schedule(schedule_path, rows, today)
        result = {"op": "add", "today": today, "topic": topic, "row": new_row}
    else:  # op == "record"（op 已在上方校验为 due/add/record 三者之一）
        topic = _require_topic(req)
        outcome = req.get("result")
        if outcome not in ("pass", "fail"):
            raise ValueError('record 需要 result 字段（"pass" / "fail"）')
        if not schedule_path.exists():
            raise FileNotFoundError(f"调度表不存在：{schedule_path}")
        rows = read_schedule(schedule_path)
        idx = next((i for i, r in enumerate(rows) if r["topic"] == topic), None)
        if idx is None:
            raise ValueError(f"知识点不在调度表中（先用 add 加入）：{topic}")
        updated = apply_outcome(rows[idx], outcome, today)
        rows[idx] = updated
        write_schedule(schedule_path, rows, today)
        result = {
            "op": "record",
            "today": today,
            "topic": topic,
            "result": outcome,
            "row": updated,
        }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def main(argv=None):
    """CLI 入口：python schedule.py <input.json> <output.json>。"""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        sys.stderr.write(
            "用法：python schedule.py <input.json> <output.json>\n"
            "契约见 ../resources/schedule-contract.md\n"
        )
        return 2
    try:
        run(argv[0], argv[1])
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"调度失败：{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
