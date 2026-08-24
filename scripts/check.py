#!/usr/bin/env python3
"""自动核对脚本（修订批次 3）——跨文件引用一致性校验（决策 4/16）。

用法：
    python check.py <input.json> <output.json>

输入输出格式、校验范围与阻断语义见 ../resources/check-contract.md。

本脚本做「机械可判定」部分的自动核对（修订方案 §5.1），输出结构化问题清单
（level: error | warning），**不硬阻塞**——是否阻断由对应流程契约规定
（resources/plan-contract.md §6 落盘前 / session-start-contract.md §2 行前 /
acceptance-contract.md §6 验收写回前）。语义校验（证据是否真支撑目标、质量等）
留在验收契约规则里，不进本脚本（决策 4）。

校验范围：
- plan_structure：plan.md 结构（Day 区块齐备：日期合法、知识点/来源行存在）；
- plan_refs：plan.md 各 Day 的「知识点」「前置」引用 ⊆ profile.md 能力矩阵行
  （知识点误引能力行为错误；前置可引知识点行或能力行）；
- writeback_consistent：profile.md 增量记录中「验收」事件的 topic 与对应
  plan Day 知识点口径一致；输入 acceptance_topics（写回前清单）同样核对；
- evidence_consistent：progress.md 结构化证据条目的「→ 知识点」与对应
  plan Day 知识点一致（决策 16）；
- decision_log：decision-log.md 可读、日期合法（批次 4 引入该文件，缺失时跳过）。

本脚本**只读**：不原地改写任何数据文件（区别于 profile.py/schedule.py）。
"""
import json
import re
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
from datetime import date, datetime
from pathlib import Path

# 复用 profile.py 的能力矩阵解析（同一 scripts/ 目录；测试同目录模块同理）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile import TYPE_ABILITY, parse_profile  # noqa: E402

# --- plan.md / progress.md / decision-log.md 解析 ---

_DAY_HEAD_RE = re.compile(r"^###\s+Day\s+(\d+)(?:\s*[-—]\s*(\S+))?")
_TOPIC_RE = re.compile(r"^-\s*主题\s*[:：]\s*(.*)$")
_OBJECTIVES_HEAD_RE = re.compile(r"^-\s*目标清单\s*[:：]\s*$")
_OBJECTIVE_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")
_RAW_BULLET_RE = re.compile(r"^\s*-\s+(.*)$")
_KNOWLEDGE_RE = re.compile(r"^-\s*知识点\s*[:：]\s*(.*)$")
_PREREQ_RE = re.compile(r"^-\s*前置\s*[:：]\s*(.*)$")
_SOURCES_RE = re.compile(r"^-\s*来源\s*[:：]\s*(.*)$")
_FIELD_LINE_RE = re.compile(r"^-\s*[^:：]*[:：]")  # 任一 `- 字段：` 行

_PROG_DAY_RE = re.compile(r"^##\s*(\d{4}-\d{2}-\d{2})\s*[-—]\s*Day\s+(\d+)")
_EVIDENCE_HEAD_RE = re.compile(r"^-\s*证据\s*[:：]\s*$")
_EVIDENCE_LEGACY_RE = re.compile(r"^-\s*证据摘要\s*[:：]")
_EVIDENCE_ITEM_RE = re.compile(r"^\s*-\s*\[([^\]]*)\]\s*(.*)$")

_LOG_LINE_RE = re.compile(r"^-\s*(\d{4}-\d{2}-\d{2})\s*[:：](.*)$")
_ARROW = "→"
_UNCHANGED_TAIL = "矩阵不变"
_DECISION_LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*\|")


def _parse_date(value):
    """date 字段：缺省取系统日期；显式值必须为 YYYY-MM-DD（自动规范补零）。"""
    if value is None:
        return date.today().isoformat()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"date 必须是 YYYY-MM-DD 日期：{value!r}")


def _valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def _split_list(text):
    """知识点/前置：按中英文逗号分隔，剥离反引号与空白（与 page.py 一致）。"""
    return [p.strip().strip("`").strip() for p in re.split(r"[，,]", text) if p.strip()]


def parse_plan(text):
    """解析 plan.md → [{number, date, topic, objectives, raw_objectives,
    knowledge, prereq, has_sources}]。

    raw_objectives：目标清单子项原文（含未用 checkbox 的行，供结构告警）；
    knowledge/prereq 按逗号拆分；date 为头部原始文本（合法性与否由调用方判定）。
    """
    days = []
    current = None
    in_objectives = False
    for line in text.splitlines():
        stripped = line.strip()
        m = _DAY_HEAD_RE.match(stripped)
        if m:
            current = {
                "number": int(m.group(1)),
                "date": m.group(2) or "",
                "topic": "",
                "objectives": [],
                "raw_objectives": [],
                "knowledge": [],
                "prereq": [],
                "has_sources": False,
            }
            days.append(current)
            in_objectives = False
            continue
        if current is None:
            continue
        if _OBJECTIVES_HEAD_RE.match(stripped):
            in_objectives = True
            continue
        if in_objectives:
            om = _OBJECTIVE_RE.match(stripped)
            if om:
                current["objectives"].append(om.group(2).strip())
                current["raw_objectives"].append(stripped)
                continue
            if stripped and _FIELD_LINE_RE.match(stripped):
                in_objectives = False  # 进入下一个字段行，停止收集目标子项
            else:
                bm = _RAW_BULLET_RE.match(stripped)
                if bm:
                    current["raw_objectives"].append(stripped)
                    continue
                if stripped:
                    in_objectives = False
                else:
                    continue
        tm = _TOPIC_RE.match(stripped)
        if tm:
            current["topic"] = tm.group(1).strip()
            in_objectives = False
            continue
        km = _KNOWLEDGE_RE.match(stripped)
        if km:
            current["knowledge"] = _split_list(km.group(1))
            in_objectives = False
            continue
        pm = _PREREQ_RE.match(stripped)
        if pm:
            current["prereq"] = _split_list(pm.group(1))
            in_objectives = False
            continue
        sm = _SOURCES_RE.match(stripped)
        if sm:
            current["has_sources"] = bool(sm.group(1).strip())
            in_objectives = False
    return days


def find_day(days, day):
    """按输入 day 标识定位当日任务：`Day 1` / `1`（编号）或 `YYYY-MM-DD`（日期）。

    找不到时抛 ValueError（含可用编号/日期提示）。
    """
    day = str(day).strip() if day is not None else ""
    if not day:
        raise ValueError("day 字段不能为空")
    m = re.match(r"(?:day\s*)?(\d+)$", day, re.IGNORECASE)
    if m:
        number = int(m.group(1))
        for info in days:
            if info["number"] == number:
                return info
        raise ValueError(f"计划中找不到 Day {number}")
    for info in days:
        if info["date"] == day:
            return info
    raise ValueError(f"计划中找不到日期 {day}")


def parse_progress(text):
    """解析 progress.md → [{date, day, evidence, malformed, legacy}]。

    evidence 条目：{label, desc, topic, raw}（topic 为 `→ 知识点` 尾部，无引用时为空串）；
    malformed：证据子列表下不符合 `- [目标] 描述` 的 bullet 原文；
    legacy：该日仍使用旧 `- 证据摘要：` 自由文本格式（批次 3 起应改为条目式）。
    """
    days = []
    current = None
    in_evidence = False
    for line in text.splitlines():
        stripped = line.strip()
        m = _PROG_DAY_RE.match(stripped)
        if m:
            current = {
                "date": m.group(1),
                "day": int(m.group(2)),
                "evidence": [],
                "malformed": [],
                "legacy": False,
            }
            days.append(current)
            in_evidence = False
            continue
        if current is None:
            continue
        if _EVIDENCE_HEAD_RE.match(stripped):
            in_evidence = True
            continue
        if _EVIDENCE_LEGACY_RE.match(stripped):
            current["legacy"] = True
            continue
        if in_evidence:
            em = _EVIDENCE_ITEM_RE.match(line)
            if em:
                label = em.group(1).strip()
                rest = em.group(2).strip()
                desc, _, topic = rest.partition(_ARROW)
                current["evidence"].append(
                    {
                        "label": label,
                        "desc": desc.strip(),
                        "topic": topic.strip(),
                        "raw": stripped,
                    }
                )
                continue
            if stripped and _FIELD_LINE_RE.match(stripped):
                in_evidence = False  # 进入下一个字段行，停止收集证据子项
            elif _RAW_BULLET_RE.match(stripped):
                current["malformed"].append(stripped)
                continue
            elif stripped:
                in_evidence = False
            continue
    return days


# --- 问题累积与五类校验 ---


def _problem(problems, level, check, message, day=None, topic=None):
    entry = {"level": level, "check": check, "message": message}
    if day is not None:
        entry["day"] = day
    if topic is not None:
        entry["topic"] = topic
    problems.append(entry)


def _check_structure(days, problems, scoped):
    """plan_structure：Day 区块齐备（日期合法、知识点/来源必需，主题/目标清单建议）。"""
    if not days:
        _problem(problems, "error", "plan_structure", "plan.md 中没有解析到任何 Day 区块")
        return
    for info in days:
        if scoped is not None and info["number"] != scoped["number"]:
            continue
        day_label = f"Day {info['number']}"
        if not info["date"]:
            _problem(problems, "error", "plan_structure", f"{day_label} 缺少日期（应为 YYYY-MM-DD）", day=day_label)
        elif not _valid_date(info["date"]):
            _problem(problems, "error", "plan_structure", f"{day_label} 日期非法（应为 YYYY-MM-DD）：{info['date']}", day=day_label)
        if not info["knowledge"]:
            _problem(problems, "error", "plan_structure", f"{day_label} 缺少知识点行（必需字段）", day=day_label)
        if not info["has_sources"]:
            _problem(problems, "error", "plan_structure", f"{day_label} 缺少来源行（必需字段）", day=day_label)
        if not info["topic"]:
            _problem(problems, "warning", "plan_structure", f"{day_label} 缺少主题", day=day_label)
        if not info["objectives"] and not info["raw_objectives"]:
            _problem(problems, "warning", "plan_structure", f"{day_label} 缺少目标清单", day=day_label)
        for raw in info["raw_objectives"]:
            if not _OBJECTIVE_RE.match(raw):
                _problem(
                    problems,
                    "warning",
                    "plan_structure",
                    f"{day_label} 目标清单项应为 `- [ ]` checkbox：{raw}",
                    day=day_label,
                )


def _check_refs(days, matrix, problems, scoped):
    """plan_refs：Day 的「知识点」「前置」引用 ⊆ 能力矩阵行。"""
    for info in days:
        if scoped is not None and info["number"] != scoped["number"]:
            continue
        day_label = f"Day {info['number']}"
        for topic in info["knowledge"]:
            row = matrix.get(topic)
            if row is None:
                _problem(problems, "error", "plan_refs", f"知识点 {topic} 不在能力矩阵中", day=day_label, topic=topic)
            elif row["type"] == TYPE_ABILITY:
                _problem(problems, "error", "plan_refs", f"知识点 {topic} 引用了能力行（计划知识点应为知识点行）", day=day_label, topic=topic)
        for topic in info["prereq"]:
            if topic not in matrix:
                _problem(problems, "error", "plan_refs", f"前置 {topic} 不在能力矩阵中", day=day_label, topic=topic)


def _log_topic(tail):
    """从增量记录 `→ topic …` 尾部提取 topic；解析失败返回 None。"""
    if not tail:
        return None
    if tail.endswith(_UNCHANGED_TAIL):
        return tail[: -len(_UNCHANGED_TAIL)].strip()
    head = tail.split("（", 1)[0].strip()
    parts = head.rsplit(" ", 1)
    if len(parts) == 2 and re.fullmatch(r"[+-]?\d+(?:\.\d+)?", parts[1]):
        return parts[0].strip()
    return head


def _check_writeback(log, days, problems, acceptance_topics, scoped):
    """writeback_consistent：验收写回 topic 与当日计划知识点口径一致。"""
    for line in log:
        lm = _LOG_LINE_RE.match(line)
        if not lm:
            continue
        event_date = lm.group(1)
        if "验收" not in lm.group(2):
            continue
        tail = lm.group(2).partition(_ARROW)[2].strip()
        if tail.startswith("新增知识点") or tail.startswith("新增能力"):
            # 批次 4 显式新增通道：学习者确认的矩阵外写回（来源「验收新增 …」），
            # 本就有意不在当日计划知识点中，不参与口径核对（见 acceptance-contract §6）
            continue
        topic = _log_topic(tail)
        if topic is None:
            continue
        day = next((d for d in days if d["date"] == event_date), None)
        if day is None:
            _problem(
                problems,
                "warning",
                "writeback_consistent",
                f"画像验收记录 {event_date} 不在计划中，无法核对知识点口径",
                day=event_date,
                topic=topic,
            )
        elif topic not in day["knowledge"]:
            _problem(
                problems,
                "error",
                "writeback_consistent",
                f"验收写回 topic {topic} 与当日计划知识点不一致（{event_date}）",
                day=f"Day {day['number']}",
                topic=topic,
            )
    if acceptance_topics is not None:
        day_label = f"Day {scoped['number']}" if scoped is not None else ""
        for topic in acceptance_topics:
            if scoped is None or topic not in scoped["knowledge"]:
                _problem(
                    problems,
                    "error",
                    "writeback_consistent",
                    f"写回 topic {topic} 不在当日计划知识点中",
                    day=day_label,
                    topic=topic,
                )
        if scoped is not None:
            for topic in scoped["knowledge"]:
                if topic not in acceptance_topics:
                    _problem(
                        problems,
                        "warning",
                        "writeback_consistent",
                        f"写回清单未覆盖当日知识点 {topic}（如为有意遗漏可忽略）",
                        day=day_label,
                        topic=topic,
                    )


def _check_evidence(progress_days, plan_days, problems):
    """evidence_consistent：progress 证据条目的「→ 知识点」与当日 plan 一致。"""
    for pday in progress_days:
        plan_day = next((d for d in plan_days if d["date"] == pday["date"]), None)
        if plan_day is None:
            _problem(
                problems,
                "warning",
                "evidence_consistent",
                f"progress 记录 {pday['date']} 不在计划中，无法核对证据知识点",
                day=pday["date"],
            )
        for item in pday["evidence"]:
            if not item["topic"]:
                _problem(
                    problems,
                    "warning",
                    "evidence_consistent",
                    f"证据条目缺少 `→ 知识点` 引用（{pday['date']}）：{item['raw']}",
                    day=pday["date"],
                )
            elif plan_day is not None and item["topic"] not in plan_day["knowledge"]:
                _problem(
                    problems,
                    "error",
                    "evidence_consistent",
                    f"证据知识点 {item['topic']} 与当日计划知识点不一致（{pday['date']}）",
                    day=pday["date"],
                    topic=item["topic"],
                )
        if pday["legacy"]:
            _problem(
                problems,
                "warning",
                "evidence_consistent",
                f"证据摘要为旧自由文本格式（{pday['date']}），批次 3 起改用条目式证据（data-formats §2）",
                day=pday["date"],
            )
        for raw in pday["malformed"]:
            _problem(
                problems,
                "warning",
                "evidence_consistent",
                f"证据条目格式不符合 `- [目标] 描述 → 知识点`（{pday['date']}）：{raw}",
                day=pday["date"],
            )


def _check_decision_log(text, problems):
    """decision_log：决策日志每行 `YYYY-MM-DD | …` 可读、日期合法。"""
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        m = _DECISION_LINE_RE.match(stripped)
        if not m or not _valid_date(m.group(1)):
            _problem(
                problems,
                "error",
                "decision_log",
                f"第 {i} 行不是合法记录行（YYYY-MM-DD | …）：{stripped}",
            )


# --- 文件契约入口 ---


def _resolve_path(req, input_path, key, default):
    """路径字段：默认值；相对路径以输入文件所在目录为基准（与 profile.py 一致）。"""
    path = Path(req.get(key, default))
    if not path.is_absolute():
        path = input_path.parent / path
    return path


def run(input_path, output_path):
    """文件契约入口：读输入 JSON → 跑机械核对 → 写输出 JSON（只读，不改数据文件）。

    输入字段：date（可选，默认系统日期）、plan_path/profile_path（可选，默认
    plan.md/profile.md，相对路径以输入文件所在目录为基准）、progress_path/
    decision_log_path（可选，文件缺失时对应校验跳过）、day（可选，`Day N` /
    编号 / 日期，指定时 plan 结构/引用只查该天）、acceptance_topics（可选，
    验收写回前清单，提供时必须同时提供 day）。
    """
    input_path = Path(input_path)
    req = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(req, dict):
        raise ValueError("输入 JSON 必须是对象")
    today = _parse_date(req.get("date"))
    plan_path = _resolve_path(req, input_path, "plan_path", "plan.md")
    profile_path = _resolve_path(req, input_path, "profile_path", "profile.md")
    progress_path = _resolve_path(req, input_path, "progress_path", "progress.md")
    decision_path = _resolve_path(req, input_path, "decision_log_path", "decision-log.md")
    if not plan_path.exists():
        raise FileNotFoundError(f"计划文件不存在：{plan_path}")
    if not profile_path.exists():
        raise FileNotFoundError(f"画像文件不存在：{profile_path}")

    days = parse_plan(plan_path.read_text(encoding="utf-8"))
    profile_data = parse_profile(profile_path.read_text(encoding="utf-8"))
    matrix = {row["topic"]: row for row in profile_data["matrix"]}

    scoped = None
    if req.get("day"):
        scoped = find_day(days, req["day"])
    acceptance_topics = req.get("acceptance_topics")
    if acceptance_topics is not None:
        if not isinstance(acceptance_topics, list):
            raise ValueError("acceptance_topics 必须是数组")
        if scoped is None:
            raise ValueError("提供 acceptance_topics 时需要 day 字段")

    problems = []
    checks_run = ["plan_structure", "plan_refs", "writeback_consistent"]
    _check_structure(days, problems, scoped)
    _check_refs(days, matrix, problems, scoped)
    _check_writeback(profile_data["log"], days, problems, acceptance_topics, scoped)

    skipped = []
    if progress_path.exists():
        checks_run.append("evidence_consistent")
        _check_evidence(parse_progress(progress_path.read_text(encoding="utf-8")), days, problems)
    else:
        skipped.append("evidence_consistent")
    if decision_path.exists():
        checks_run.append("decision_log")
        _check_decision_log(decision_path.read_text(encoding="utf-8"), problems)
    else:
        skipped.append("decision_log")

    summary = {
        "checks_run": checks_run,
        "skipped": skipped,
        "errors": sum(1 for p in problems if p["level"] == "error"),
        "warnings": sum(1 for p in problems if p["level"] == "warning"),
    }
    out = {
        "date": today,
        "ok": summary["errors"] == 0,
        "problems": problems,
        "summary": summary,
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main(argv=None):
    """CLI 入口：python check.py <input.json> <output.json>。"""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        sys.stderr.write(
            "用法：python check.py <input.json> <output.json>\n"
            "契约见 ../resources/check-contract.md\n"
        )
        return 2
    try:
        run(argv[0], argv[1])
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"核对失败：{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
