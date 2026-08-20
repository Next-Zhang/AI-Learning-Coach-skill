#!/usr/bin/env python3
"""复习快查文档脚本（ticket 13）——课程结束的沉淀：生成快查文档 + 准备调度新增。

用法：
    python review.py <input.json> <output.json>

输入输出格式、字段约定与用法见 ../resources/review-contract.md。

两种操作（输入文件 op 字段）：
- generate：按课程一份生成 `review/NN-主题.md`（frontmatter course/date/topics
  + 每个知识点一行：概念一句话 + 关键代码/示例 + 常见坑 + 来源引用），默认拒绝
  覆盖既有文档；输出 JSON 同时给出 `schedule_add`（[{topic, mastery}]）供 agent
  接 `scripts/schedule.py`（op=add）把新知识点纳入调度表（知识点 → 掌握度 →
  下次复习日）。快查文档写盘属持久层修改，执行前 agent 须先经学习者确认
  （护栏 approval）；schedule_add 只是输出建议，实际写调度表由 schedule.py 完成。
- query：只读查阅——按知识点关键词和/或日期检索 `review/` 下快查文档，支持按
  知识点（topics / 行文本）、按日期（frontmatter date）直接定位；不写任何文件。

与 progress.md 的职责分离（spec「每日闭环」）：progress.md = 每日总结叙事（由
ticket 12 追加）；review/ = 每节课的知识沉淀（用户可读、按知识点/日期查阅）；
review/schedule.md = 调度视图（agent 复习只查调度表，性能护栏）。本脚本只负责
review/ 快查文档，不写 progress.md、不直接写调度表。
"""
import json
import math
import re
import sys
from datetime import date, datetime
from pathlib import Path

# 与 scripts/schedule.py 的 add 默认掌握度保持一致（新知识点入调度表的初始值）
DEFAULT_MASTERY = 2.0
MASTERY_MIN = 1.0
MASTERY_MAX = 5.0

# 调度表文件名（复习目录中的特殊文件，不当作快查文档参与查阅）
SCHEDULE_FILENAME = "schedule.md"

# 知识点行的解析：每行 `- **知识点**：内容`
_POINT_RE = re.compile(r"^-\s*\*\*(.+?)\*\*\s*[:：]\s*(.*)$")
# 来源引用：行尾 `；来源：xxx。`（来源可含中文/URL/路径，取到行尾去句号）
_SOURCE_RE = re.compile(r";?\s*来源[:：]\s*(.+?)。?\s*$")
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_HEADING_RE = re.compile(r"^#\s+(.*)$")


# --- 通用解析辅助 ---


def _strip_quotes(value):
    """去掉标量值首尾成对的引号，并清理引号内外的空白。"""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def _parse_list(value):
    """解析数组字段：`[a, b]`、`["a", 'b']` 或裸字符串 → 字符串列表。"""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        parts = [p.strip() for p in value[1:-1].split(",")]
    elif value:
        parts = [value]
    else:
        parts = []
    return [_strip_quotes(p) for p in parts if p]


def parse_frontmatter(text):
    """解析 frontmatter 块 → (dict, 正文)。无 frontmatter 返回 ({}, 全文)。

    topics 按数组解析；course/date 原样字符串；容错跳过错行。
    """
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "topics":
            fm[key] = _parse_list(value)
        else:
            fm[key] = _strip_quotes(value)
    return fm, text[m.end():]


# --- 快查文档解析（查询用） ---


def parse_review_doc(text, name="review.md"):
    """解析一份快查文档 → {file, course, date, topics, title, points}。

    points：每行一个知识点 {topic, text, source}（source 从行尾「来源：」提取，
    提取不到为 None）。容错：无 frontmatter 给默认值；无 `- **…**：` 行的文档
    视为空 points 但仍返回标题信息（查询时按 topics/标题匹配）。
    """
    fm, body = parse_frontmatter(text)
    course_raw = str(fm.get("course") or "").strip()
    try:
        course = int(course_raw) if course_raw else 0
    except ValueError:
        course = 0
    date_str = str(fm.get("date") or "").strip()
    if date_str:
        try:
            # 规范为 YYYY-MM-DD，保证与查询输入（_parse_date 已规范）可比
            date_str = datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass  # 手写非规范日期保留原样，按原始串比较（不中断解析）
    topics = fm.get("topics", [])

    title = ""
    points = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not title:
            hm = _HEADING_RE.match(stripped)
            if hm:
                title = hm.group(1).strip()
        pm = _POINT_RE.match(stripped)
        if pm:
            topic = pm.group(1).strip()
            rest = pm.group(2).strip()
            sm = _SOURCE_RE.search(rest)
            source = sm.group(1).strip() if sm else None
            points.append(
                {"topic": topic, "text": stripped, "source": source}
            )
    return {
        "file": name,
        "course": course,
        "date": date_str,
        "topics": topics,
        "title": title,
        "points": points,
    }


def _point_text(point):
    """按快查文档行格式拼一条知识点行（概念 → 关键代码 → 常见坑 → 来源）。

    与 templates/review-sheet.md 与 data-formats.md §5 一致：概念后直接跟行内
    代码（不带「示例：」标签）；无示例/常见坑时对应段省略。point 为归一化后
    的知识点 dict；mastery 仅用于调度新增建议，不渲染进正文。
    """
    line = f"- **{point['topic']}**：{point['concept']}"
    if point.get("example"):
        line += f"。`{point['example']}`"
    if point.get("pitfall"):
        line += f"；常见坑：{point['pitfall']}"
    line += f"；来源：{point['source']}。"
    return line


def slugify(text):
    """文档基名：小写 ASCII、中文保留、其余（含空格与标点）折叠为连字符。

    `pandas Series 与 DataFrame` → `pandas-series-与-dataframe`（Windows 文件
    名安全的字符集之外全部折叠）。
    """
    parts = []
    for ch in text.strip().lower():
        parts.append(ch if (ch.isalnum() or ch == "-") else "-")
    slug = re.sub(r"-{2,}", "-", "".join(parts)).strip("-")
    return slug or "review"


def render_doc(course, title, date_str, topics, points):
    """渲染一份完整快查文档 Markdown（frontmatter + H1 + 每知识点一行）。"""
    topics_text = "[" + ", ".join(topics) + "]" if topics else "[]"
    lines = [
        "---",
        f"course: {course:02d}",
        f"date: {date_str}",
        f"topics: {topics_text}",
        "---",
        "",
        f"# {course:02d} — {title}",
        "",
    ]
    lines.extend(_point_text(p) for p in points)
    return "\n".join(lines) + "\n"


# --- generate：写快查文档 ---


def _require_str(req, key, label):
    value = req.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}不能为空")
    return value.strip()


def _require_topic(topic):
    topic = _require_str({"t": topic}, "t", "知识点名")
    if "|" in topic or "\n" in topic:
        raise ValueError("知识点名不能包含 | 或换行（表格格式约束）")
    return topic


def _clamp_mastery(value):
    """掌握度解析：数字 → 规范到 0.5 档（半向上舍入）→ 截断到 [1, 5]。

    与 scripts/profile.py 的水平分规范化同一策略，保证写进调度表的建议值
    与能力矩阵/调度表的 0.5 档展示一致。
    """
    try:
        m = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"mastery 必须是数字：{value!r}")
    m = math.floor(m * 2 + 0.5) / 2
    return min(MASTERY_MAX, max(MASTERY_MIN, m))


def _parse_date(value):
    """date 字段：缺省取系统日期；显式值必须为 YYYY-MM-DD（自动规范补零）。"""
    if value is None:
        return date.today().isoformat()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"date 必须是 YYYY-MM-DD 日期：{value!r}")


def _resolve_path(req, input_path, key, default):
    """路径字段：缺省用默认值；相对路径以输入文件所在目录为基准解析。"""
    value = req.get(key, default)
    path = Path(value)
    if not path.is_absolute():
        path = input_path.parent / path
    return path


def _run_generate(req, input_path):
    """op=generate：生成一份复习快查文档。

    输入字段：review_path（可选，默认 "review"，相对路径以输入文件所在目录为
    基准）、course（必填，1–99）、title（必填）、date（可选，默认系统日期）、
    topics（可选数组）、points（必填数组，每项 {topic, concept, example?,
    pitfall?, source, mastery?}）、overwrite（可选，默认 false）。
    输出：review_path/filename/file_path + 归一化 points + schedule_add。
    """
    review_dir = _resolve_path(req, input_path, "review_path", "review")

    raw_course = req.get("course")
    try:
        course = int(raw_course)
    except (TypeError, ValueError):
        raise ValueError(f"course 必须是数字：{raw_course!r}")
    if not 1 <= course <= 99:
        raise ValueError("course 必须在 1–99 之间（文件名两位编号）")
    title = _require_str(req, "title", "title")
    date_str = _parse_date(req.get("date"))

    topics_raw = req.get("topics")
    if topics_raw is None:
        topics = []
    elif isinstance(topics_raw, list):
        topics = []
        for t in topics_raw:
            if not isinstance(t, str) or not t.strip():
                raise ValueError("topics 数组元素必须是字符串")
            topics.append(t.strip())
    else:
        raise ValueError("topics 必须是数组")

    points_raw = req.get("points")
    if not isinstance(points_raw, list) or not points_raw:
        raise ValueError("points 必须是非空数组（每课至少一个知识点）")
    points = []
    schedule_add = []
    for idx, item in enumerate(points_raw):
        if not isinstance(item, dict):
            raise ValueError(f"points[{idx}] 必须是对象")
        topic = _require_topic(item.get("topic"))
        concept = _require_str(item, "concept", "concept")
        source = _require_str(item, "source", "source")
        if "|" in source or "\n" in source:
            raise ValueError(f"points[{idx}].source 不能包含 | 或换行")
        example = item.get("example")
        example = str(example).strip() if example is not None else ""
        pitfall = item.get("pitfall")
        pitfall = str(pitfall).strip() if pitfall is not None else ""
        mastery = (
            _clamp_mastery(item.get("mastery"))
            if item.get("mastery") is not None
            else DEFAULT_MASTERY
        )
        points.append(
            {
                "topic": topic,
                "concept": concept,
                "example": example,
                "pitfall": pitfall,
                "source": source,
                "mastery": mastery,
            }
        )
        schedule_add.append({"topic": topic, "mastery": mastery})

    review_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{course:02d}-{slugify(title)}.md"
    file_path = review_dir / filename
    if file_path.exists() and not req.get("overwrite"):
        raise ValueError(
            f"快查文档已存在：{filename}（按课程一份，不覆盖；"
            "确需重写请在输入带 overwrite: true）"
        )
    file_path.write_text(
        render_doc(course, title, date_str, topics, points), encoding="utf-8"
    )

    echo_points = [
        {
            "topic": p["topic"],
            "concept": p["concept"],
            "example": p["example"],
            "pitfall": p["pitfall"],
            "source": p["source"],
        }
        for p in points
    ]
    return {
        "op": "generate",
        "review_path": str(review_dir.resolve()),
        "course": course,
        "course_label": f"{course:02d}",
        "title": title,
        "date": date_str,
        "topics": topics,
        "filename": filename,
        "file_path": str(file_path.resolve()),
        "line_count": len(points),
        "points": echo_points,
        "schedule_add": schedule_add,
    }


# --- query：查阅快查文档（只读） ---


def _matches_doc(doc, query):
    """知识点关键词是否命中：标题 / topics / 任一行文本（大小写不敏感子串）。"""
    if not query:
        return True
    q = query.casefold()
    if q in doc["title"].casefold():
        return True
    if any(q in t.casefold() for t in doc["topics"]):
        return True
    return any(q in p["text"].casefold() for p in doc["points"])


def _run_query(req, input_path):
    """op=query：按知识点关键词和/或日期查阅快查文档（只读）。

    输入字段：review_path（可选，默认 "review"）、query（可选，知识点关键词）、
    date（可选，YYYY-MM-DD）。query 为空且 date 为空 → 列出全部快查文档。
    输出：matches 数组（每项含 file/course/date/topics/title/points）。
    """
    review_dir = _resolve_path(req, input_path, "review_path", "review")
    query = req.get("query")
    if query is not None and not isinstance(query, str):
        raise ValueError("query 必须是字符串")
    if query is not None:
        query = query.strip()
    date_str = _parse_date(req.get("date")) if req.get("date") is not None else None

    matches = []
    if review_dir.exists():
        paths = sorted(review_dir.glob("*.md"))
        for path in paths:
            if path.name == SCHEDULE_FILENAME:
                continue  # 调度表不是快查文档，不参与查阅
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue  # 个别文件不可读则跳过，不拖垮整体
            doc = parse_review_doc(text, path.name)
            doc["path"] = str(path.resolve())
            if date_str is not None and doc["date"] != date_str:
                continue
            if not _matches_doc(doc, query):
                continue
            matches.append(doc)
    matches.sort(key=lambda d: (d["course"], d["file"]))

    return {
        "op": "query",
        "query": query,
        "date": date_str,
        "total_docs": len(matches),
        "matches": matches,
    }


# --- 文件契约入口 ---


def run(input_path, output_path):
    """文件契约入口：读输入 JSON → generate/query → 写输出 JSON。"""
    input_path = Path(input_path)
    req = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(req, dict):
        raise ValueError("输入 JSON 必须是对象")
    op = req.get("op")
    if op == "generate":
        result = _run_generate(req, input_path)
    elif op == "query":
        result = _run_query(req, input_path)
    else:
        raise ValueError('输入缺少 op 字段（"generate" / "query"）')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def main(argv=None):
    """CLI 入口：python review.py <input.json> <output.json>。"""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        sys.stderr.write(
            "用法：python review.py <input.json> <output.json>\n"
            "契约见 ../resources/review-contract.md\n"
        )
        return 2
    try:
        run(argv[0], argv[1])
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"快查文档处理失败：{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
