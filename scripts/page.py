#!/usr/bin/env python3
"""当日执行网页生成脚本（ticket 06）——输入 plan.md + 当日任务 → 输出单文件静态 HTML。

用法：
    python page.py <input.json> <output.json>

输入输出格式、字段约定与用法见 ../resources/page-contract.md。

HTML 四区块（ticket 06 与 spec「当日执行网页」）：
1. 知识：当日知识内容（概念+示例）——优先取输入 knowledge 字段（agent 从
   检索层提炼），否则读取当日任务来源引用的本地 sources/ 文件正文渲染；
2. 链路：学习目标（frontmatter goal）→ 今日位置（第 N 天 / 共 M 天 → 今日主题），
   步骤条展示目标 → Day 1 … Day M，当前天高亮；
3. 目标：今日目标清单（对照范围声明：覆盖 / 不涉及）；
4. 来源：当日任务来源链接（sources/ 本地文件或 URL）。

输出：单文件自包含 HTML（内联 CSS、无外部资源、可离线打开），默认写到系统
临时目录（ticket 06「输出到系统临时目录」），可用 output_dir 覆盖；输出 JSON
报告 html_path 与解析出的当日任务各字段。本脚本只读 plan.md 与来源文件，不
改写任何持久层数据文件。
"""
import html
import json
import re
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
import tempfile
from pathlib import Path

# --- plan.md 解析 ---

_DAY_HEAD_RE = re.compile(r"^###\s+Day\s+(\d+)(?:\s*[-—]\s*(\S+))?")
_TOPIC_RE = re.compile(r"^-\s*主题\s*[:：]\s*(.*)$")
_OBJECTIVES_HEAD_RE = re.compile(r"^-\s*目标清单\s*[:：]\s*$")
_OBJECTIVE_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")
_KNOWLEDGE_RE = re.compile(r"^-\s*知识点\s*[:：]\s*(.*)$")
_SOURCES_RE = re.compile(r"^-\s*来源\s*[:：]\s*(.*)$")
_FIELD_LINE_RE = re.compile(r"^-\s*[^:：]*[:：]")  # 任一 `- 字段：` 行，用于终止目标子列表
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# 来源分隔符：中文分号/英文分号/中文逗号/英文逗号
_SOURCE_SEP_RE = re.compile(r"[；;，,]")


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
    """解析 frontmatter 块，返回 (frontmatter dict, body)。无 frontmatter 返回 ({}, 全文)。"""
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
        if key in ("scope_covered", "scope_excluded", "topics"):
            fm[key] = _parse_list(value)
        else:
            fm[key] = _strip_quotes(value)
    return fm, text[m.end():]


def parse_plan(text):
    """解析 plan.md → {goal, scope_covered, scope_excluded, days}。

    days：按 `### Day N — YYYY-MM-DD` 区块解析，每项含
    {number, date, topic, objectives, objective_checked, knowledge_points, sources}；
    缺字段/无 frontmatter 均容错（空串/空数组），来源与知识点按分隔符拆分。
    objective_checked 与 objectives 同下标，记录 `- [x]` 勾选状态。
    """
    fm, body = parse_frontmatter(text)
    goal = fm.get("goal", "")
    scope_covered = fm.get("scope_covered", [])
    scope_excluded = fm.get("scope_excluded", [])

    days = []
    current = None
    in_objectives = False
    for line in body.splitlines():
        stripped = line.strip()
        m = _DAY_HEAD_RE.match(stripped)
        if m:
            current = {
                "number": int(m.group(1)),
                "date": m.group(2) or "",
                "topic": "",
                "objectives": [],
                "objective_checked": [],
                "knowledge_points": [],
                "sources": [],
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
                current["objective_checked"].append(om.group(1).strip().lower() == "x")
                continue
            if stripped and _FIELD_LINE_RE.match(stripped):
                in_objectives = False  # 进入下一个字段行，停止收集目标子项
        tm = _TOPIC_RE.match(stripped)
        if tm:
            current["topic"] = tm.group(1).strip()
            in_objectives = False
            continue
        km = _KNOWLEDGE_RE.match(stripped)
        if km:
            # 知识点：逗号分隔，剥离反引号与空白
            current["knowledge_points"] = [
                _strip_quotes(p).strip("`").strip()
                for p in re.split(r"[，,]", km.group(1))
                if p.strip()
            ]
            in_objectives = False
            continue
        sm = _SOURCES_RE.match(stripped)
        if sm:
            current["sources"] = [
                p.strip() for p in _SOURCE_SEP_RE.split(sm.group(1)) if p.strip()
            ]
            in_objectives = False
    return {
        "goal": goal,
        "scope_covered": scope_covered,
        "scope_excluded": scope_excluded,
        "days": days,
    }


def find_day(plan, day):
    """按输入 day 标识定位当日任务：`Day 1` / `1`（编号）或 `YYYY-MM-DD`（日期）。

    找不到时抛 ValueError（含可用编号/日期提示）。
    """
    day = str(day).strip() if day is not None else ""
    if not day:
        raise ValueError("day 字段不能为空")
    m = re.match(r"(?:day\s*)?(\d+)$", day, re.IGNORECASE)
    if m:
        number = int(m.group(1))
        for info in plan["days"]:
            if info["number"] == number:
                return info
        raise ValueError(f"计划中找不到 Day {number}")
    for info in plan["days"]:
        if info["date"] == day:
            return info
    raise ValueError(f"计划中找不到当日任务：{day}")


# --- 极简 Markdown → HTML（渲染来源正文的知识内容） ---

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline(text):
    """行内语法：行内代码 → 加粗 → 链接（顺序处理，互不嵌套解析）。"""
    text = _INLINE_CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    return text


def render_markdown(text):
    """极简 Markdown → HTML：代码块、标题、列表、段落（含行内语法）。

    覆盖 sources/ 资料正文的常见结构（概念散文 + Python 代码示例）；
    未覆盖的语法按纯文本保留（不报错、不丢内容）。所有文本先转义。
    """
    lines = html.escape(text).splitlines()
    out = []
    buf = []
    i = 0

    def flush():
        """冲刷行缓冲：连续 `- ` 列表项 → <ul>，否则 → <p>。"""
        nonlocal buf
        if not buf:
            return
        items = [ln for ln in buf if re.match(r"^-\s+", ln)]
        if items and len(items) == len(buf):
            lis = "".join(f"<li>{_inline(re.sub(r'^-\\s+', '', ln))}</li>" for ln in buf)
            out.append(f"<ul>{lis}</ul>")
        else:
            out.append("<p>" + _inline(" ".join(buf)) + "</p>")
        buf = []

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # 跳过闭合 ```（不存在则已到文件尾）
            out.append("<pre><code>" + "\n".join(code) + "</code></pre>")
            continue
        hm = re.match(r"^(#{1,6})\s+(.*)$", line)
        if hm:
            flush()
            level = len(hm.group(1))
            out.append(f"<h{level}>{_inline(hm.group(2))}</h{level}>")
            i += 1
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        buf.append(line)
        i += 1
    flush()
    return "\n".join(out)


# --- 知识内容获取 ---


def _is_url(source):
    """来源是否为外链 URL（脚本不联网，仅展示链接）。"""
    return source.startswith("http://") or source.startswith("https://")


def _local_source_path(source, plan_dir):
    """本地来源（如 sources/pandas-series.md）→ 相对 plan.md 目录的绝对路径。"""
    path = Path(source)
    if not path.is_absolute():
        path = plan_dir / path
    return path.resolve()


def load_knowledge(day, plan_dir, knowledge):
    """当日知识内容（概念+示例）→ [{topic, concept_html, example_html}]。

    优先用输入 knowledge（agent 从检索层提炼）；未提供时读取当日任务来源
    引用的本地 sources/ 文件正文（正文即「概念散文 + 代码示例」），URL 来源
    不读取（脚本不联网，仅来源区块展示）。字段缺省/null 视为空。
    """
    items = []
    if knowledge:
        for item in knowledge:
            topic = str(item.get("topic") or "").strip()
            concept = str(item.get("concept") or "").strip()
            example = str(item.get("example") or "").strip()
            if not (topic or concept or example):
                continue
            items.append(
                {
                    "topic": topic,
                    "concept_html": render_markdown(concept) if concept else "",
                    "example_html": (
                        "<pre><code>" + html.escape(example) + "</code></pre>"
                        if example
                        else ""
                    ),
                }
            )
        return items
    for source in day["sources"]:
        if _is_url(source):
            continue
        path = _local_source_path(source, plan_dir)
        if not path.exists():
            continue
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        items.append(
            {
                "topic": fm.get("title", path.stem),
                "concept_html": render_markdown(body) if body.strip() else "",
                "example_html": "",
            }
        )
    return items


# --- HTML 渲染 ---

CSS = """
:root {
  --bg: #fafafa; --card: #ffffff; --ink: #222; --muted: #666;
  --line: #e3e3e3; --accent: #2f6f4f; --accent-bg: #eef6f1;
  --code-bg: #f4f4f4;
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 32px 16px; background: var(--bg); color: var(--ink);
  font-family: -apple-system, "Segoe UI", "Microsoft YaHei", "PingFang SC",
               "Noto Sans CJK SC", sans-serif;
  line-height: 1.7;
}
main { max-width: 760px; margin: 0 auto; }
header.page-head { margin-bottom: 28px; }
header.page-head h1 { margin: 0 0 6px; font-size: 26px; }
.meta { color: var(--muted); font-size: 14px; }
section.card {
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 20px 22px; margin-bottom: 18px;
}
section.card h2 {
  margin: 0 0 12px; font-size: 18px; padding-bottom: 8px;
  border-bottom: 2px solid var(--accent);
}
.knowledge-item { margin-bottom: 16px; }
.knowledge-item:last-child { margin-bottom: 0; }
.knowledge-item h3 { margin: 0 0 6px; font-size: 16px; }
pre {
  background: var(--code-bg); border: 1px solid var(--line); border-radius: 6px;
  padding: 12px 14px; overflow-x: auto; font-size: 13px;
}
code {
  font-family: Consolas, "Courier New", monospace;
  background: var(--code-bg); padding: 1px 5px; border-radius: 4px; font-size: 13px;
}
pre code { background: none; padding: 0; }
ol.journey { list-style: none; padding: 0; margin: 0; counter-reset: step; }
ol.journey li {
  counter-increment: step; position: relative; padding: 8px 10px 8px 44px;
  margin-bottom: 8px; border: 1px solid var(--line); border-radius: 8px;
  background: var(--card);
}
ol.journey li::before {
  content: counter(step); position: absolute; left: 12px; top: 50%;
  transform: translateY(-50%); width: 22px; height: 22px; border-radius: 50%;
  background: var(--accent-bg); color: var(--accent); text-align: center;
  line-height: 22px; font-size: 12px; font-weight: 700;
}
ol.journey li.current {
  border-color: var(--accent); background: var(--accent-bg); font-weight: 600;
}
ol.journey li.current::before { background: var(--accent); color: #fff; }
ul.objectives { list-style: none; padding: 0; margin: 0 0 16px; }
ul.objectives li { padding: 6px 0; }
ul.objectives input[type="checkbox"] { margin-right: 8px; }
.scope {
  border-top: 1px dashed var(--line); padding-top: 12px; font-size: 14px;
  color: var(--muted);
}
.scope strong { color: var(--ink); }
ul.sources { margin: 0; padding-left: 20px; }
ul.sources a { color: var(--accent); word-break: break-all; }
footer { color: var(--muted); font-size: 12px; text-align: center; margin-top: 24px; }
"""


def _objective_item(text, checked):
    """目标清单行：checkbox + 文本（checked 渲染已勾选状态）。"""
    mark = " checked" if checked else ""
    return (
        f"<li><label><input type=\"checkbox\"{mark}>{html.escape(text)}</label></li>"
    )


def _render_knowledge(day, knowledge_items):
    """知识区块：知识条目（概念 + 示例）；无任何条目时兜底显示当日知识点列表。"""
    if knowledge_items:
        parts = []
        for item in knowledge_items:
            title = f"<h3>{html.escape(item['topic'])}</h3>" if item["topic"] else ""
            concept = f"<div class=\"concept\">{item['concept_html']}</div>" if item["concept_html"] else ""
            example = item["example_html"]
            parts.append(f"<div class=\"knowledge-item\">{title}{concept}{example}</div>")
        return "".join(parts)
    if day["knowledge_points"]:
        lis = "".join(
            f"<li>{html.escape(p)}</li>" for p in day["knowledge_points"]
        )
        return (
            f"<p>今日知识点（具体概念与示例由教练在会话中讲解）：</p><ul>{lis}</ul>"
        )
    return "<p>（当日任务未声明知识点）</p>"


def _render_journey(plan, day):
    """链路区块：目标 → 第 1 天 … 第 M 天步骤条，当前天高亮。"""
    total = len(plan["days"])
    steps = []
    for info in plan["days"]:
        cls_attr = ' class="current"' if info["number"] == day["number"] else ""
        label = f"Day {info['number']}"
        if info["date"]:
            label += f" · {info['date']}"
        steps.append(
            f"<li{cls_attr}>{html.escape(label)}"
            f"<br><span style=\"font-weight:400;font-size:13px\">"
            f"{html.escape(info['topic'])}</span></li>"
        )
    steps_html = "\n".join(steps)
    goal_html = html.escape(plan["goal"]) if plan["goal"] else "（计划未声明学习目标）"
    return (
        "<p><strong>学习目标：</strong>"
        + goal_html
        + "</p>"
        + f"<p style=\"color:var(--muted);font-size:14px\">今日位置：第 "
        + f"{day['number']} / {total} 天</p>"
        + f"<ol class=\"journey\">{steps_html}</ol>"
    )


def _render_objectives(day, plan):
    """目标区块：今日目标清单（保留 plan.md 中的勾选状态）+ 范围声明对照。"""
    if day["objectives"]:
        lis = "".join(
            _objective_item(text, day["objective_checked"][i] if i < len(day["objective_checked"]) else False)
            for i, text in enumerate(day["objectives"])
        )
    else:
        lis = "<li>（当日任务未声明目标）</li>"
    covered = "、".join(plan["scope_covered"]) if plan["scope_covered"] else "（未声明）"
    excluded = "、".join(plan["scope_excluded"]) if plan["scope_excluded"] else "（未声明）"
    return (
        f"<ul class=\"objectives\">{lis}</ul>"
        "<div class=\"scope\">"
        f"<p><strong>范围声明 · 覆盖：</strong>{html.escape(covered)}</p>"
        f"<p><strong>范围声明 · 不涉及：</strong>{html.escape(excluded)}</p>"
        "</div>"
    )


def _render_sources(day, plan_dir):
    """来源区块：当日任务来源链接（本地文件 → file:// 链接；URL → 外链）。"""
    if not day["sources"]:
        return "<p>（当日任务未声明来源）</p>"
    lis = []
    for source in day["sources"]:
        if _is_url(source):
            href = source
        else:
            href = _local_source_path(source, plan_dir).as_uri()
        lis.append(
            f"<li><a href=\"{html.escape(href, quote=True)}\">"
            f"{html.escape(source)}</a></li>"
        )
    return "<ul class=\"sources\">" + "".join(lis) + "</ul>"


def render_html(plan, day, knowledge_items, plan_dir):
    """组装完整 HTML 页面（自包含：内联 CSS、无外部资源、可离线打开）。"""
    if day["topic"]:
        title = f"Day {day['number']} — {day['topic']}"
    else:
        title = f"Day {day['number']}"
    if day["date"]:
        title += f"（{day['date']}）"
    meta = day["date"] if day["date"] else f"第 {day['number']} 天"
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)} · 当日执行视图</title>\n"
        f"<style>{CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        "<header class=\"page-head\">\n"
        f"<h1>{html.escape(title)}</h1>\n"
        f"<p class=\"meta\">{html.escape(meta)} · 当日执行视图（临时文件，验收后删除）</p>\n"
        "</header>\n"
        '<section class="card" id="knowledge">\n'
        "<h2>今日知识</h2>\n"
        + _render_knowledge(day, knowledge_items)
        + "\n</section>\n"
        '<section class="card" id="journey">\n'
        "<h2>完整链路</h2>\n"
        + _render_journey(plan, day)
        + "\n</section>\n"
        '<section class="card" id="objectives">\n'
        "<h2>今日目标</h2>\n"
        + _render_objectives(day, plan)
        + "\n</section>\n"
        '<section class="card" id="sources">\n'
        "<h2>参考来源</h2>\n"
        + _render_sources(day, plan_dir)
        + "\n</section>\n"
        "</main>\n"
        "<footer>python-coach 当日执行视图 · 生成后仅供本日学习使用，验收完成经确认后删除</footer>\n"
        "</body>\n"
        "</html>\n"
    )


# --- 文件契约入口 ---


def _resolve_path(req, input_path, key, default):
    """路径字段：缺省用默认值；相对路径以输入文件所在目录为基准解析。"""
    value = req.get(key, default)
    path = Path(value)
    if not path.is_absolute():
        path = input_path.parent / path
    return path


def run(input_path, output_path):
    """文件契约入口：读输入 JSON → 生成当日执行 HTML → 写输出 JSON。

    输入字段：plan_path（必填，相对路径以输入文件所在目录为基准）、day（必填，
    "Day 1" / "1" / 日期）、output_dir（可选，默认系统临时目录）、knowledge（可选，
    agent 从检索层提炼的当日知识内容数组 [{topic, concept, example}]）。
    输出：单文件 HTML 写到 output_dir（文件名 day-{n}-{date}.html），
    输出 JSON 报告 html_path 与当日任务解析结果。
    """
    input_path = Path(input_path)
    req = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(req, dict):
        raise ValueError("输入 JSON 必须是对象")
    plan_path = _resolve_path(req, input_path, "plan_path", "plan.md")
    if not plan_path.exists():
        raise FileNotFoundError(f"plan.md 不存在：{plan_path}")
    plan = parse_plan(plan_path.read_text(encoding="utf-8"))
    if not plan["days"]:
        raise ValueError("plan.md 中没有解析到任何 Day 区块")
    day = find_day(plan, req.get("day"))

    output_dir = _resolve_path(req, input_path, "output_dir", tempfile.gettempdir())
    output_dir.mkdir(parents=True, exist_ok=True)

    knowledge = req.get("knowledge")
    if knowledge is not None:
        if not isinstance(knowledge, list):
            raise ValueError("knowledge 必须是数组")
        for idx, item in enumerate(knowledge):
            if not isinstance(item, dict):
                raise ValueError(f"knowledge[{idx}] 必须是对象")
    knowledge_items = load_knowledge(day, plan_path.parent, knowledge)

    date_part = f"-{day['date']}" if day["date"] else ""
    html_path = output_dir / f"day-{day['number']}{date_part}.html"
    html_path.write_text(render_html(plan, day, knowledge_items, plan_path.parent), encoding="utf-8")

    out = {
        "html_path": str(html_path.resolve()),
        "output_dir": str(output_dir.resolve()),
        "day": f"Day {day['number']}",
        "day_number": day["number"],
        "total_days": len(plan["days"]),
        "date": day["date"],
        "topic": day["topic"],
        "goal": plan["goal"],
        "scope_covered": plan["scope_covered"],
        "scope_excluded": plan["scope_excluded"],
        "objectives": day["objectives"],
        "knowledge_points": day["knowledge_points"],
        "sources": day["sources"],
        "knowledge_count": len(knowledge_items),
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def main(argv=None):
    """CLI 入口：python page.py <input.json> <output.json>。"""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        sys.stderr.write(
            "用法：python page.py <input.json> <output.json>\n"
            "契约见 ../resources/page-contract.md\n"
        )
        return 2
    try:
        run(argv[0], argv[1])
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"网页生成失败：{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
