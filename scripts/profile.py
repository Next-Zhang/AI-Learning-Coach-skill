#!/usr/bin/env python3
"""画像更新脚本（ticket 05）——用户画像（profile.md）的增量更新逻辑。

用法：
    python profile.py <input.json> <output.json>

输入输出格式、更新规则与用法见 ../resources/profile-contract.md。

四种操作（输入文件 op 字段）：
- onboarding：onboarding 问卷结果（8 题）写入画像初值；画像文件不存在时创建；
- placement：摸底测试结果初始化能力矩阵（来源「摸底测试」）——知识点行写
  水平分（[{topic, score}] 或 [{topic, type: "知识点", score, domain?, subdomain?}]），
  能力行写前置状态（[{topic, type: "能力", pre_status: "具备"|"未具备", domain?, subdomain?}]）；
  画像文件不存在时创建；results 内行整体覆盖，其余行保留；
- acceptance：记录一次验收结果（完成度 + 难度反馈）→ 能力矩阵知识点行增量修正
  （完成度 ≥ 4 → 该知识点 +0.5，上限 5；难度反馈独立记录，不改变矩阵数值；
  能力行无水平分，不接受验收/复习增量）；
- review：记录一次复习考察结果 → 能力矩阵知识点行写回（通过 +0.5 上限 5；
  未通过 -0.5 下限 1），与 scripts/schedule.py 的掌握度推进同一规则。

显式新增通道（批次 4，决策 5）：acceptance/review 的 topic 不在能力矩阵时，
默认仍报错（矩阵由摸底测试初始化）；经学习者确认后由输入 `add_new: true`
放行新建矩阵行（知识点评分初值见下方规则；来源默认「验收新增」/「复习新增」，
agent 通常显式传「验收新增 Day N」）。该通道与调度表 `schedule.py op=add`、
快查文档 `review.py op=append` 构成三同步（见 ../resources/acceptance-contract.md
§6 与 ../resources/review-contract.md）。

本脚本原地读写 profile.md（能力矩阵 + 增量记录 + frontmatter updated）；
难度反馈只在增量记录中留痕，不写入矩阵数值（spec「完成度评分」：
难度反馈只影响后续计划难度档位）。
"""
import json
import math
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
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
MATRIX_HEADER = "## 能力矩阵（领域 → 子领域 → 知识点/能力）"
LOG_HEADER = "## 增量记录"
MATRIX_HEADER_ROW = "| 领域 | 子领域 | 知识点 | 类型 | 水平分 | 前置状态 | 更新时间 | 来源 |"
MATRIX_SEPARATOR = "| --- | --- | --- | --- | --- | --- | --- | --- |"
# 矩阵行类型：知识点（水平分 1–5，前置状态 = —）| 能力（水平分 = —，前置状态 = 具备|未具备）
TYPE_KNOWLEDGE = "知识点"
TYPE_ABILITY = "能力"
PRE_STATUS_READY = "具备"
PRE_STATUS_GAP = "未具备"
DASH = "—"
# 显式新增通道（批次 4）：新增行默认来源（agent 通常显式传「验收新增 Day N」）
NEW_ACCEPTANCE_SOURCE = "验收新增"
NEW_REVIEW_SOURCE = "复习新增"
# review 新增知识点的初值：通过 → 2.0（与 scripts/schedule.py 的 add 默认掌握度一致），
# 未通过 → 1.0（下限，仍需补学）
NEW_PASS_LEVEL = 2.0
NEW_FAIL_LEVEL = 1.0

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
    """解析一行矩阵行 → dict；失败返回 None。

    新 schema（8 列）：`| 领域 | 子领域 | 知识点 | 类型 | 水平分 | 前置状态 | 更新时间 | 来源 |`；
    旧 schema（4 列，容错）：`| 知识点 | 水平分 | 更新时间 | 来源 |`（视为知识点行，领域/子领域为空、
    前置状态 = —）。类型 = 知识点（水平分数字，前置状态 = —）| 能力（水平分 = —，前置状态 = 具备|未具备）。

    容错：单元格个数不对、类型非法、水平分/日期无法解析的行一律跳过（与调度表解析同一策略）；
    表头行与分隔行的水平分不是数字，自然被跳过。
    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 8:
        domain, subdomain, topic, row_type, level_text, pre_status, updated, source = cells
    elif len(cells) == 4:
        # 旧 4 列 schema 容错：知识点行（领域/子领域缺省为空、类型=知识点、前置状态 = —）
        topic, level_text, updated, source = cells
        domain = subdomain = ""
        row_type = TYPE_KNOWLEDGE
        pre_status = DASH
    else:
        return None
    if not topic:
        return None
    if row_type == TYPE_KNOWLEDGE:
        level = _parse_level(level_text)
        if level is None:
            return None
        pre_status = DASH
    elif row_type == TYPE_ABILITY:
        if pre_status not in (PRE_STATUS_READY, PRE_STATUS_GAP):
            return None
        level = None  # 能力行无水平分（前置状态为二值）
    else:
        return None
    try:
        # 统一规范为 YYYY-MM-DD，保证字符串比较与写入格式一致
        updated = datetime.strptime(updated, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None
    return {
        "domain": domain,
        "subdomain": subdomain,
        "topic": topic,
        "type": row_type,
        "level": level,
        "pre_status": pre_status,
        "date": updated,
        "source": source,
    }


def parse_profile(text):
    """解析画像文本 → {created, updated, onboarding, matrix, log}。

    - onboarding：Onboarding 问卷区块下的逐行原文（非空行）；
    - matrix：能力矩阵表格行 [{domain, subdomain, topic, type, level, pre_status,
      date, source}]，坏行跳过；
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
        elif stripped.startswith("## 能力矩阵"):
            # 兼容新旧表头（新「领域 → 子领域 → 知识点/能力」/ 旧「知识点 × 水平分 1–5」）
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
        # 知识点行：水平分 + 前置状态 = —；能力行：水平分 = — + 前置状态（具备|未具备）
        if row["type"] == TYPE_ABILITY:
            level_text = DASH
            pre_status = row["pre_status"]
        else:
            level_text = _number_text(row["level"])
            pre_status = DASH
        lines.append(
            f"| {row['domain']} | {row['subdomain']} | {row['topic']} | {row['type']} | "
            f"{level_text} | {pre_status} | {row['date']} | {row['source']} |"
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


def _find_topic_or_none(data, topic):
    """查矩阵行下标；不在矩阵返回 None（供显式新增通道判定，批次 4）。"""
    return next((i for i, r in enumerate(data["matrix"]) if r["topic"] == topic), None)


def _new_row_fields(req, topic):
    """显式新增通道的行字段：type（知识点|能力）、domain/subdomain、pre_status（能力行必填）。

    知识点行：pre_status 忽略（初值由调用方按 op 给出）；能力行：pre_status 必填
    （二值），水平分恒为 None。type 非法报错。
    """
    row_type = req.get("type", TYPE_KNOWLEDGE)
    if row_type not in (TYPE_KNOWLEDGE, TYPE_ABILITY):
        raise ValueError(
            f'type 必须是 "{TYPE_KNOWLEDGE}" / "{TYPE_ABILITY}"：{row_type!r}'
        )
    domain = (req.get("domain") or "").strip()
    subdomain = (req.get("subdomain") or "").strip()
    pre_status = None
    if row_type == TYPE_ABILITY:
        pre_status = req.get("pre_status")
        if pre_status not in (PRE_STATUS_READY, PRE_STATUS_GAP):
            raise ValueError(
                '能力行需要 pre_status 字段（"具备" / "未具备"）：' + topic
            )
    return row_type, domain, subdomain, pre_status


def _apply_new_row(data, topic, day, source, detail, row_type, level, pre_status,
                   domain, subdomain):
    """显式新增通道：为矩阵外知识点新建矩阵行并追加增量记录（acceptance/review 共用）。

    仅适用于 topic 不在矩阵（调用方已确认并经 add_new 放行）：知识点行写水平分
    （acceptance 取完成度、review 取 pass 2.0 / fail 1.0），能力行写前置状态；
    来源为「验收新增」/「复习新增」类文本（调用方传入）。返回输出片段：
    added=true、old_score/delta=None（新行无旧值）、new_score（能力行为 None）。
    """
    if row_type == TYPE_ABILITY:
        row = {
            "domain": domain,
            "subdomain": subdomain,
            "topic": topic,
            "type": TYPE_ABILITY,
            "level": None,
            "pre_status": pre_status,
            "date": day,
            "source": source,
        }
        entry = (
            f"- {day}：{source}（{detail}）→ 新增能力 {topic}（前置状态 {pre_status}）"
        )
        new_score = None
    else:
        row = {
            "domain": domain,
            "subdomain": subdomain,
            "topic": topic,
            "type": TYPE_KNOWLEDGE,
            "level": level,
            "pre_status": DASH,
            "date": day,
            "source": source,
        }
        entry = (
            f"- {day}：{source}（{detail}）→ 新增知识点 {topic}（水平 {_number_text(level)}）"
        )
        new_score = level
    data["matrix"].append(row)
    data["log"].append(entry)
    return {
        "topic": topic,
        "source": source,
        "old_score": None,
        "new_score": new_score,
        "delta": None,
        "updated": True,
        "added": True,
        "log_entry": entry,
    }


def _apply_delta(data, topic, delta, day, source, detail, idx=None):
    """对能力矩阵某知识点应用增量并追加增量记录（acceptance/review 共用）。

    delta：期望增量（0 表示不变化，如验收未达阈值）；detail：括号内详情文本；
    source：矩阵「来源」列与日志事件名。数值实际截断在 [1, 5]，因此已达
    上限/下限时 updated=False、日志记「矩阵不变」。仅适用于知识点行
    （能力行无水平分，前置状态为二值，不接受验收/复习增量）。
    """
    if idx is None:
        idx = _find_topic(data, topic)
    row = data["matrix"][idx]
    if row["type"] != TYPE_KNOWLEDGE:
        raise ValueError(
            f"能力行不接受验收/复习增量（前置状态为二值）：{topic}"
        )
    old = row["level"]
    new = min(LEVEL_MAX, max(LEVEL_MIN, old + delta))
    updated = new != old
    if updated:
        data["matrix"][idx] = {
            **row,
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
    """placement：摸底测试结果初始化能力矩阵。

    results = [{topic, score}]（知识点行，向后兼容）或带类型/分层字段：
    - 知识点行：{topic, score, type?: "知识点", domain?, subdomain?}；
      level 按 score 0.5 档舍入并截断 [1, 5]，前置状态 = —；
    - 能力行（前置能力评估）：{topic, type: "能力", pre_status: "具备"|"未具备",
      domain?, subdomain?}；水平分 = —，前置状态二值。
    topic 须非空且不重复。results 内行整体按新值覆盖（来源「摸底测试」、
    日期 = day），其余行保留；日志追加一条「摸底测试 → 初始矩阵」。
    """
    results = req.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("placement 需要非空 results 数组（[{topic, score}] 或带 type 的能力行）")
    entries = []
    seen = set()
    for item in results:
        if not isinstance(item, dict):
            raise ValueError("placement 的 results 元素必须是对象（{topic, score}）")
        topic = _require_topic(item)
        if topic in seen:
            raise ValueError(f"placement 的 results 含重复知识点：{topic}")
        seen.add(topic)
        row_type = item.get("type", TYPE_KNOWLEDGE)
        domain = item.get("domain") or ""
        subdomain = item.get("subdomain") or ""
        if row_type == TYPE_KNOWLEDGE:
            entries.append(
                {
                    "domain": domain,
                    "subdomain": subdomain,
                    "topic": topic,
                    "type": TYPE_KNOWLEDGE,
                    "level": _round_half(_clamp_level(item.get("score"), "score")),
                    "pre_status": DASH,
                    "date": day,
                    "source": PLACEMENT_SOURCE,
                }
            )
        elif row_type == TYPE_ABILITY:
            pre_status = item.get("pre_status")
            if pre_status not in (PRE_STATUS_READY, PRE_STATUS_GAP):
                raise ValueError(
                    '能力行需要 pre_status 字段（"具备" / "未具备"）：' + topic
                )
            if "score" in item:
                raise ValueError(
                    f"能力行不需要 score（前置状态为二值）：{topic}"
                )
            entries.append(
                {
                    "domain": domain,
                    "subdomain": subdomain,
                    "topic": topic,
                    "type": TYPE_ABILITY,
                    "level": None,
                    "pre_status": pre_status,
                    "date": day,
                    "source": PLACEMENT_SOURCE,
                }
            )
        else:
            raise ValueError(
                f'placement 的 type 必须是 "{TYPE_KNOWLEDGE}" / "{TYPE_ABILITY}"：{row_type!r}'
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
    # 输出视图与矩阵行同源（矩阵行键为 level，输出契约键为 score；能力行 score = None）
    matrix = [
        {
            "topic": entry["topic"],
            "type": entry["type"],
            "score": entry["level"],
            "pre_status": entry["pre_status"],
            "domain": entry["domain"],
            "subdomain": entry["subdomain"],
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
    """acceptance：验收完成度 ≥ 4 → 知识点 +0.5（上限 5）；难度反馈入日志不改矩阵。

    矩阵外 topic：默认报错；输入 add_new: true（学习者已确认）→ 显式新增通道
    新建矩阵行——知识点行初值 = 完成度（0.5 档截断），能力行写前置状态。
    """
    topic = _require_topic(req)
    score = _clamp_level(req.get("score"), "score")
    difficulty = req.get("difficulty")
    if difficulty is not None and difficulty not in DIFFICULTY_LEVELS:
        raise ValueError(
            f"difficulty 必须是 {'/'.join(DIFFICULTY_LEVELS)} 之一：{difficulty!r}"
        )
    source = _source_text(req.get("source"), "验收")
    detail = f"完成度 {_number_text(score)}"
    if difficulty is not None:
        detail += f"，难度 {difficulty}"
    idx = _find_topic_or_none(data, topic)
    if idx is None:
        if not req.get("add_new"):
            raise ValueError(f"知识点不在能力矩阵中（先经摸底测试初始化）：{topic}")
        row_type, domain, subdomain, pre_status = _new_row_fields(req, topic)
        level = _round_half(score) if row_type == TYPE_KNOWLEDGE else None
        out = _apply_new_row(
            data, topic, day, source, detail, row_type, level, pre_status,
            domain, subdomain,
        )
        out.update({"score": score, "difficulty": difficulty})
        return out
    delta = PASS_DELTA if score >= ACCEPT_THRESHOLD else 0.0
    out = _apply_delta(data, topic, delta, day, source, detail, idx=idx)
    out.update({"score": score, "difficulty": difficulty})
    return out


def _run_review(req, data, day):
    """review：复习考察通过 +0.5（上限 5）/ 未通过 -0.5（下限 1），写回能力矩阵。

    矩阵外 topic：默认报错；输入 add_new: true（学习者已确认）→ 显式新增通道
    新建矩阵行——知识点行初值 通过 2.0 / 未通过 1.0（与 schedule.py add 默认
    掌握度一致），能力行写前置状态。
    """
    topic = _require_topic(req)
    result = req.get("result")
    if result not in ("pass", "fail"):
        raise ValueError('review 需要 result 字段（"pass" / "fail"）')
    source = _source_text(req.get("source"), "复习考察")
    detail = "通过" if result == "pass" else "未通过"
    idx = _find_topic_or_none(data, topic)
    if idx is None:
        if not req.get("add_new"):
            raise ValueError(f"知识点不在能力矩阵中（先经摸底测试初始化）：{topic}")
        row_type, domain, subdomain, pre_status = _new_row_fields(req, topic)
        if row_type == TYPE_KNOWLEDGE:
            level = NEW_PASS_LEVEL if result == "pass" else NEW_FAIL_LEVEL
        else:
            level = None
        out = _apply_new_row(
            data, topic, day, source, detail, row_type, level, pre_status,
            domain, subdomain,
        )
        out.update({"result": result})
        return out
    delta = PASS_DELTA if result == "pass" else -FAIL_DELTA
    out = _apply_delta(data, topic, delta, day, source, detail, idx=idx)
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
    results（[{topic, score}] 知识点行，或带 type/domain/subdomain/pre_status 的
    知识点/能力行），acceptance 另需 topic/score（difficulty/source 可选），
    review 另需 topic/result。acceptance/review 的矩阵外新增通道（批次 4）：
    topic 不在矩阵时置 add_new: true（学习者已确认）→ 新建矩阵行，可选
    type/domain/subdomain（能力行另需 pre_status）。
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
