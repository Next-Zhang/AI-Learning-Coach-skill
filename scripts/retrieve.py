#!/usr/bin/env python3
"""检索层 v0（ticket 02）——统一契约：输入查询 → 输出资料列表。

用法：
    python retrieve.py <input.json> <output.json>

输入输出格式、评分规则与用法见 ../resources/retrieval-contract.md。

v0 检索策略（ADR-0002，数据格式先行、引擎后置）：
- 关键词检索：glob 扫描 sources/ 下全部 .md，解析 frontmatter（五字段），
  对查询分词后按 标题/主题/摘要/正文 加权子串匹配并排序；
- web 补充：web_search/web_fetch 是 agent 侧工具，脚本自身不联网；
  agent 检索到的 web 结果经输入文件 web_results 字段传入，
  由本脚本与本地结果合并、按 URL 去重，输出统一资料列表。
"""
import json
import re
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
from pathlib import Path

# frontmatter 五字段（ADR-0002 契约字段，勿改名/删减）
FIELDS = ("title", "source", "topics", "date", "summary")

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _strip_quotes(value):
    """去掉标量值首尾成对的引号，并清理引号内外的空白。"""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def _parse_topics(value):
    """解析 topics 字段：`[a, b]`、`["a", 'b']` 或裸字符串 → 字符串列表。"""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        parts = [p.strip() for p in value[1:-1].split(",")]
    elif value:
        parts = [value]
    else:
        parts = []
    return [_strip_quotes(p) for p in parts if p]


def parse_frontmatter(text):
    """解析资料文本的 frontmatter 块，返回 (frontmatter dict, body)。

    无 frontmatter 或格式不完整时，返回 ({}, 全文) 作为正文兜底。
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
            fm[key] = _parse_topics(value)
        else:
            fm[key] = _strip_quotes(value)
    return fm, text[m.end():]


def load_source(path):
    """读取一份资料文件 → 五字段 + body + link（link 为绝对路径）。"""
    path = Path(path)
    fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    src = {"link": str(path.resolve())}
    for field in FIELDS:
        src[field] = fm[field] if field in fm else ([] if field == "topics" else "")
    src["body"] = body
    return src


# 评分权重（契约见 retrieval-contract.md）
W_TITLE = 3.0
W_TOPICS = 2.0
W_SUMMARY = 1.5
W_BODY = 1.0


def tokenize(query):
    r"""查询分词：小写化，按非单词字符切分（\w 含中文与数字）。"""
    return re.findall(r"\w+", query.lower())


def _score(source, terms):
    """按 标题/主题/摘要/正文 加权子串匹配；返回 (score, matched_terms)。"""
    score = 0.0
    matched = []
    for term in terms:
        hit = False
        if term in source["title"]:
            score += W_TITLE
            hit = True
        if any(term in t for t in source["topics"]):
            score += W_TOPICS
            hit = True
        if term in source["summary"]:
            score += W_SUMMARY
            hit = True
        if term in source["body"]:
            score += W_BODY
            hit = True
        if hit:
            matched.append(term)
    return score, matched


def _date_key(date):
    """ISO 日期 → 数值（倒序用：越新越小）。空值排最后。"""
    digits = date.replace("-", "")
    return -int(digits) if digits.isdigit() else 0


def _make_result(title, source, summary, link, topics, date, score, matched_terms, origin):
    """统一的结果记录构造器（本地与 web 共用，保证字段一致）。"""
    return {
        "title": title,
        "source": source,
        "summary": summary,
        "link": link,
        "topics": topics,
        "date": date,
        "score": score,
        "matched_terms": matched_terms,
        "origin": origin,
    }


def search_sources(sources_dir, query, limit=10):
    """在 sources/ 内做关键词检索，返回按相关度排序的资料列表。

    每个结果：title / source / summary / link / topics / date /
    score（加权和，保留 2 位）/ matched_terms / origin="local"。
    排序：score 降序 → date 新者优先 → link 字典序。
    """
    terms = tokenize(query)
    if not terms:
        return []
    sources_dir = Path(sources_dir)
    if not sources_dir.is_dir():
        raise FileNotFoundError(f"资料目录不存在: {sources_dir}")
    results = []
    for path in sorted(sources_dir.glob("*.md")):
        src = load_source(path)
        score, matched = _score(src, terms)
        if score <= 0:
            continue
        results.append(_make_result(
            title=src["title"],
            source=src["source"],
            summary=src["summary"],
            link=src["link"],
            topics=src["topics"],
            date=src["date"],
            score=round(score, 2),
            matched_terms=matched,
            origin="local",
        ))
    results.sort(key=lambda r: (-r["score"], _date_key(r["date"]), r["link"]))
    return results[:limit]


def _norm_url(url):
    """URL 归一化用于去重：去首尾空白与结尾斜杠、转小写。"""
    return (url or "").strip().rstrip("/").lower()


def merge_web(results, web_results, limit=10):
    """把 web 检索补充结果并入统一资料列表。

    - 本地结果在前（已按相关度排序），web 结果按给定顺序追加；
    - 按归一化 URL 去重：与本地重复、web 内部重复的都跳过；
    - 合并后的列表统一受 limit 截断（web 只补充剩余名额）。
    """
    if not web_results:
        return results[:limit]
    seen = {_norm_url(r["source"]) for r in results if r.get("source")}
    merged = list(results)
    for item in web_results:
        if len(merged) >= limit:
            break
        norm = _norm_url(item.get("source", ""))
        if not norm or norm in seen:
            continue
        seen.add(norm)
        merged.append(_make_result(
            title=item.get("title", ""),
            source=item.get("source", ""),
            summary=item.get("summary", ""),
            link=item.get("source", ""),  # web 结果无本地文件，link 即来源 URL
            topics=[],
            date="",
            score=None,
            matched_terms=[],
            origin="web",
        ))
    return merged[:limit]


def run(input_path, output_path):
    """文件契约入口：读输入 JSON → 检索 → 写输出 JSON。

    输入字段：query（必填）、sources_dir（可选，默认 "sources"，
    相对路径以输入文件所在目录为基准）、limit（可选，默认 10）、
    web_results（可选，agent 侧 web 检索结果数组）。
    输出：{"query": ..., "results": [资料列表]}。
    """
    input_path = Path(input_path)
    req = json.loads(input_path.read_text(encoding="utf-8"))
    query = req.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("输入缺少非空 query 字段")
    sources_dir = Path(req.get("sources_dir", "sources"))
    if not sources_dir.is_absolute():
        sources_dir = input_path.parent / sources_dir
    limit = int(req.get("limit", 10))
    results = search_sources(sources_dir, query, limit=limit)
    results = merge_web(results, req.get("web_results") or [], limit=limit)
    out = {"query": query, "results": results}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def main(argv=None):
    """CLI 入口：python retrieve.py <input.json> <output.json>。"""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        sys.stderr.write(
            "用法：python retrieve.py <input.json> <output.json>\n"
            "契约见 ../resources/retrieval-contract.md\n"
        )
        return 2
    try:
        run(argv[0], argv[1])
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"检索失败：{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
