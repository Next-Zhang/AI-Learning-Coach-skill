#!/usr/bin/env python3
"""当日执行网页生成脚本（ticket 06）测试——以样例输入文件驱动脚本，断言输出文件内容。

遵循 spec「测试 seam」与「Testing Decisions」：唯一 seam 是 scripts/ 纯函数，
测试形态为「读输入文件 → 写输出文件」契约，只测外部行为、不测实现细节。
因此本套测试全部经 run()/main() 走文件契约；HTML 与输出 JSON 的断言以
生成文件内容为准（契约见 ../resources/page-contract.md）。

运行：python scripts/test_page.py
注意：沙箱下 tempfile 不可写，测试全部显式指定 output_dir 到 testdata/_out/page/；
「默认输出到系统临时目录」通过 mock 替换 tempfile.gettempdir 验证缺省路径逻辑。
"""
import html as html_mod
import json
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
import unittest
from pathlib import Path
from unittest import mock

# 让测试直接 import 同目录的 page 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import page

TESTDATA = Path(__file__).resolve().parent / "testdata"
INPUTS = TESTDATA / "input"
PLANS = TESTDATA / "plan"
OUTDIR = TESTDATA / "_out"
PAGE_OUT = OUTDIR / "page"
INPUT_OUT = OUTDIR / "input"


class _PageTest(unittest.TestCase):
    """共享夹具目录与输出目录（各测试独立输出文件名，互不覆盖）。"""

    def setUp(self):
        PAGE_OUT.mkdir(parents=True, exist_ok=True)
        INPUT_OUT.mkdir(parents=True, exist_ok=True)
        # 清理上次运行遗留的生成物，保证重复运行结果一致
        for stale in PAGE_OUT.glob("*.html"):
            stale.unlink()
        for stale in PAGE_OUT.glob("*.json"):
            stale.unlink()

    def _out(self, name):
        return OUTDIR / name

    def _run(self, input_name, out_name):
        """以静态输入夹具驱动 run()，断言输出文件已写出，返回 (result, out_json_path)。"""
        out = self._out(out_name)
        result = page.run(INPUTS / input_name, out)
        self.assertTrue(out.exists())
        return result, out

    def _write_input(self, name, data):
        """把场景输入写成 _out/input/ 下的 JSON（供生成式场景复用文件契约）。"""
        path = INPUT_OUT / name
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def _write_plan(self, name, text):
        """把场景 plan 写成 _out/plan/ 下的 .md（供生成式场景复用文件契约）。"""
        path = OUTDIR / "plan" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _read_file(self, path):
        return Path(path).read_text(encoding="utf-8")


class BasicRenderTest(_PageTest):
    """基础渲染：四区块 + 输出 JSON 字段 + 知识内容兜底（来源正文）。"""

    def test_basic_output_json_fields(self):
        # page-basic.json：Day 1，无 knowledge → 知识区块读取来源正文兜底
        result, out = self._run("page-basic.json", "page-basic-out.json")
        self.assertEqual(result["day"], "Day 1")
        self.assertEqual(result["day_number"], 1)
        self.assertEqual(result["total_days"], 3)
        self.assertEqual(result["date"], "2026-08-20")
        self.assertEqual(result["topic"], "pandas 入门")
        self.assertEqual(result["goal"], "用 Python 做数据分析")
        self.assertEqual(result["scope_covered"], ["数据分析", "pandas", "数据可视化"])
        self.assertEqual(result["scope_excluded"], ["Web 框架", "网络爬虫"])
        self.assertEqual(result["objectives"], ["读懂 Series 与 DataFrame 的创建", "完成 3 个练习"])
        self.assertEqual(result["knowledge_points"], ["pandas.Series", "pandas.DataFrame"])
        self.assertEqual(
            result["sources"],
            ["../sources/pandas-series.md", "https://pandas.pydata.org/docs/user_guide/10min.html"],
        )
        # 知识来源正文兜底 → 读到了 1 个来源条目
        self.assertGreaterEqual(result["knowledge_count"], 1)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)
        # HTML 文件存在且路径正确（文件名 day-{n}-{date}.html）
        self.assertTrue(Path(result["html_path"]).exists())
        self.assertTrue(result["html_path"].endswith("day-1-2026-08-20.html"))

    def test_html_four_sections(self):
        result, _ = self._run("page-basic.json", "page-sections-out.json")
        html_content = self._read_file(Path(result["html_path"]))
        for heading in ["今日知识", "完整链路", "今日目标", "参考来源"]:
            self.assertIn(heading, html_content)
        # 区块锚点
        for anchor in ['id="knowledge"', 'id="journey"', 'id="objectives"', 'id="sources"']:
            self.assertIn(anchor, html_content)

    def test_objectives_and_scope(self):
        _, out = self._run("page-basic.json", "page-obj-out.json")
        html = self._read_file(Path(json.loads(self._read_file(out))["html_path"]))
        for objective in ["读懂 Series 与 DataFrame 的创建", "完成 3 个练习"]:
            self.assertIn(objective, html)
        # 目标清单渲染为 checkbox
        self.assertEqual(html.count('<input type="checkbox"'), 2)
        # 范围声明对照（覆盖 / 不涉及）
        self.assertIn("范围声明 · 覆盖", html)
        self.assertIn("数据分析、pandas、数据可视化", html)
        self.assertIn("范围声明 · 不涉及", html)
        self.assertIn("Web 框架、网络爬虫", html)

    def test_objective_checked_state_preserved(self):
        # plan.md 中 `- [x]` 的目标渲染为已勾选（checkbox checked）
        plan = self._write_plan(
            "checked.md",
            "---\ngoal: 目标\nscope_covered: []\nscope_excluded: []\n---\n\n"
            "# 学习计划\n\n## 每日任务\n\n### Day 1 — 2026-08-20\n"
            "- 主题：回顾\n- 目标清单：\n"
            "  - [x] 已复习的知识点\n  - [ ] 未完成的目标\n"
            "- 知识点：pandas\n- 来源：../sources/pandas-series.md\n",
        )
        inp = self._write_input(
            "page-checked.json",
            {"plan_path": str(plan), "day": "Day 1", "output_dir": "../_out/page"},
        )
        out = self._out("page-checked-out.json")
        result = page.run(inp, out)
        html = self._read_file(Path(result["html_path"]))
        self.assertIn('<input type="checkbox" checked>已复习的知识点', html)
        self.assertIn('<input type="checkbox">未完成的目标', html)

    def test_journey_goal_and_current_highlight(self):
        result, out = self._run("page-basic.json", "page-journey-out.json")
        html = self._read_file(Path(result["html_path"]))
        self.assertIn("学习目标：</strong>用 Python 做数据分析", html)
        self.assertIn("今日位置：第 1 / 3 天", html)
        # 三个 Day 步骤，Day 1 高亮为 current
        self.assertEqual(html.count('<li class="current"'), 1)
        self.assertIn("Day 1 · 2026-08-20", html)
        self.assertIn("Day 2 · 2026-08-21", html)
        self.assertIn("Day 3 · 2026-08-22", html)
        self.assertIn("pandas groupby", html)  # Day 2 主题出现在链路

    def test_sources_links(self):
        result, out = self._run("page-basic.json", "page-src-out.json")
        html = self._read_file(Path(result["html_path"]))
        # 本地来源 → file:// 链接（路径以 file:// 开头、含文件名）
        self.assertIn("file://", html)
        self.assertIn("pandas-series.md", html)
        # URL 来源 → 外链
        self.assertIn('href="https://pandas.pydata.org/docs/user_guide/10min.html"', html)

    def test_knowledge_fallback_reads_source_body(self):
        # 无 knowledge 输入 → 读取来源文件正文（概念 + 代码示例）作为知识内容
        result, _ = self._run("page-basic.json", "page-kb-fallback-out.json")
        html = self._read_file(Path(result["html_path"]))
        self.assertIn("Series 是一维带标签数组", html)          # 来源正文概念
        self.assertIn("s = pd.Series([1, 2, 3])", html)         # 来源正文代码示例
        self.assertIn("pandas Series 基础", html)               # 来源 frontmatter title 作小标题

    def test_self_contained_offline(self):
        # 静态单文件：内联 CSS、无外部资源（无外链样式/脚本/图片/字体）
        result, _ = self._run("page-basic.json", "page-offline-out.json")
        html = self._read_file(Path(result["html_path"]))
        self.assertTrue(html.lstrip().startswith("<!DOCTYPE html>"))
        self.assertIn("<style>", html)
        self.assertNotIn('<link rel="stylesheet"', html)
        self.assertNotIn("<script", html)
        self.assertNotIn('src="http', html)
        self.assertNotIn("url(http", html)
        self.assertNotIn("@import", html)


class KnowledgeInputTest(_PageTest):
    """knowledge 输入优先：概念 + 示例渲染进知识区块。"""

    def test_knowledge_field_rendered(self):
        result, out = self._run("page-knowledge.json", "page-kb-out.json")
        self.assertEqual(result["knowledge_count"], 2)
        html = self._read_file(Path(result["html_path"]))
        self.assertIn("pandas.Series", html)
        self.assertIn("Series 是一维带标签数组，概念来自检索层提炼。", html)
        self.assertIn("s = pd.Series([1, 2, 3])", html)
        self.assertIn("print(s.sum())", html)
        self.assertIn("pandas.DataFrame", html)
        # 示例代码经 HTML 转义（单引号 → &#x27;）
        self.assertIn(html_mod.escape("df = pd.DataFrame({'a': [1, 2]})"), html)

    def test_example_html_escaped(self):
        # 示例代码含 <script> 等 → 必须转义，不得注入可执行标签
        inp = self._write_input(
            "page-escape.json",
            {
                "plan_path": str(PLANS / "basic.md"),
                "day": "Day 1",
                "output_dir": "../_out/page",
                "knowledge": [
                    {
                        "topic": "注入测试",
                        "concept": "概念 <b>加粗</b> & 符号",
                        "example": "x = 1 < 2\n<script>alert(1)</script>",
                    }
                ],
            },
        )
        out = self._out("page-escape-out.json")
        result = page.run(inp, out)
        html = self._read_file(Path(result["html_path"]))
        self.assertNotIn("<script>alert", html)
        self.assertIn(html_mod.escape("x = 1 < 2"), html)
        self.assertIn(html_mod.escape("<script>alert(1)</script>"), html)
        self.assertIn(html_mod.escape("概念 <b>加粗</b> & 符号"), html)


class DayMatchTest(_PageTest):
    """day 匹配：编号 / 日期 / 找不到报错。"""

    def test_day_by_number_word(self):
        result, _ = self._run("page-basic.json", "page-day1-out.json")
        self.assertEqual(result["day_number"], 1)
        self.assertEqual(result["topic"], "pandas 入门")

    def test_day_by_number_plain(self):
        inp = self._write_input(
            "page-day1plain.json",
            {"plan_path": str(PLANS / "basic.md"), "day": "1", "output_dir": "../_out/page"},
        )
        out = self._out("page-day1plain-out.json")
        result = page.run(inp, out)
        self.assertEqual(result["day_number"], 1)

    def test_day_by_date(self):
        result, _ = self._run("page-by-date.json", "page-by-date-out.json")
        self.assertEqual(result["day_number"], 1)
        self.assertEqual(result["date"], "2026-08-20")

    def test_day2_current_highlight_moves(self):
        result, _ = self._run("page-day2.json", "page-day2-out.json")
        self.assertEqual(result["topic"], "pandas groupby")
        html = self._read_file(Path(result["html_path"]))
        # 高亮落在 Day 2；知识来源正文兜底读 groupby 资料
        self.assertEqual(html.count('<li class="current"'), 1)
        self.assertIn("今日位置：第 2 / 3 天", html)
        self.assertIn("groupby 分组聚合", html)

    def test_missing_day_raises(self):
        with self.assertRaises(ValueError):
            page.run(INPUTS / "page-missing-day.json", self._out("page-missing-out.json"))

    def test_empty_day_raises(self):
        inp = self._write_input(
            "page-emptyday.json",
            {"plan_path": str(PLANS / "basic.md"), "day": "", "output_dir": "../_out/page"},
        )
        with self.assertRaises(ValueError):
            page.run(inp, self._out("page-emptyday-out.json"))

    def test_missing_day_field_raises(self):
        inp = self._write_input(
            "page-nodey.json",
            {"plan_path": str(PLANS / "basic.md"), "output_dir": "../_out/page"},
        )
        with self.assertRaises(ValueError):
            page.run(inp, self._out("page-nodey-out.json"))


class FallbackTextTest(_PageTest):
    """无目标 / 无来源 / 无知识点的兜底文案。"""

    MINIMAL_PLAN = """---
goal: 简单目标
scope_covered: []
scope_excluded: []
---

# 学习计划

## 每日任务

### Day 1 — 2026-08-20
- 主题：空任务
"""

    def test_minimal_plan_fallbacks(self):
        plan = self._write_plan("minimal.md", self.MINIMAL_PLAN)
        inp = self._write_input(
            "page-minimal.json",
            {"plan_path": str(plan), "day": "Day 1", "output_dir": "../_out/page"},
        )
        out = self._out("page-minimal-out.json")
        result = page.run(inp, out)
        html = self._read_file(Path(result["html_path"]))
        self.assertIn("（当日任务未声明目标）", html)
        self.assertIn("（当日任务未声明来源）", html)
        self.assertIn("（当日任务未声明知识点）", html)
        self.assertIn("范围声明 · 覆盖：</strong>（未声明）", html)
        self.assertIn("范围声明 · 不涉及：</strong>（未声明）", html)
        self.assertEqual(result["total_days"], 1)


class OutputDirTest(_PageTest):
    """输出目录：显式覆盖 + 缺省走系统临时目录。"""

    def test_explicit_output_dir(self):
        result, _ = self._run("page-basic.json", "page-dir-out.json")
        self.assertEqual(Path(result["output_dir"]).resolve(), PAGE_OUT.resolve())
        self.assertEqual(Path(result["html_path"]).parent.resolve(), PAGE_OUT.resolve())

    def test_default_output_dir_is_tempdir(self):
        # 缺省 output_dir → 落到 tempfile.gettempdir()（mock 替换，避免真写系统临时目录）
        inp = self._write_input(
            "page-notemp.json",
            {"plan_path": str(PLANS / "basic.md"), "day": "Day 1"},
        )
        out = self._out("page-notemp-out.json")
        fake_temp = str(PAGE_OUT / "temp")
        with mock.patch("page.tempfile.gettempdir", return_value=fake_temp):
            result = page.run(inp, out)
        self.assertEqual(Path(result["output_dir"]).resolve(), Path(fake_temp).resolve())


class ErrorTest(_PageTest):
    """输入错误处理。"""

    def test_missing_plan_raises(self):
        with self.assertRaises(FileNotFoundError):
            page.run(INPUTS / "page-no-plan.json", self._out("page-noplan-out.json"))

    def test_plan_without_days_raises(self):
        plan = self._write_plan("nodays.md", "---\ngoal: x\n---\n\n# 学习计划\n\n（没有 Day 区块）\n")
        inp = self._write_input(
            "page-nodays.json",
            {"plan_path": str(plan), "day": "Day 1", "output_dir": "../_out/page"},
        )
        with self.assertRaises(ValueError):
            page.run(inp, self._out("page-nodays-out.json"))

    def test_bad_knowledge_type_raises(self):
        with self.assertRaises(ValueError):
            page.run(
                INPUTS / "page-bad-knowledge.json", self._out("page-badkb-out.json")
            )

    def test_bad_knowledge_element_raises(self):
        # knowledge 元素非对象（如字符串）→ 报错而非 AttributeError
        inp = self._write_input(
            "page-badkbelem.json",
            {
                "plan_path": str(PLANS / "basic.md"),
                "day": "Day 1",
                "output_dir": "../_out/page",
                "knowledge": ["不是对象"],
            },
        )
        with self.assertRaises(ValueError):
            page.run(inp, self._out("page-badkbelem-out.json"))

    def test_knowledge_null_fields_ignored(self):
        # knowledge 元素字段为 null → 视为空，整条被忽略（不渲染 "None"）
        inp = self._write_input(
            "page-kbnull.json",
            {
                "plan_path": str(PLANS / "basic.md"),
                "day": "Day 1",
                "output_dir": "../_out/page",
                "knowledge": [
                    {"topic": None, "concept": None, "example": None},
                    {"topic": "有效知识点", "concept": "有效概念", "example": "print(1)"},
                ],
            },
        )
        out = self._out("page-kbnull-out.json")
        result = page.run(inp, out)
        self.assertEqual(result["knowledge_count"], 1)
        html = self._read_file(Path(result["html_path"]))
        self.assertIn("有效知识点", html)
        self.assertNotIn(">None<", html)

    def test_non_object_input_raises(self):
        inp = INPUT_OUT / "page-notobj.json"
        inp.parent.mkdir(parents=True, exist_ok=True)
        inp.write_text('["数组"]', encoding="utf-8")
        with self.assertRaises(ValueError):
            page.run(inp, self._out("page-notobj-out.json"))

    def test_missing_input_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            page.run(INPUTS / "不存在.json", self._out("page-nofile-out.json"))


class CliTest(_PageTest):
    """命令行入口 main()。"""

    def test_main_writes_output(self):
        out = self._out("cli-page-out.json")
        code = page.main([str(INPUTS / "page-basic.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(
            json.loads(out.read_text(encoding="utf-8"))["day_number"], 1
        )

    def test_main_wrong_arg_count_returns_2(self):
        self.assertEqual(page.main([]), 2)
        self.assertEqual(page.main(["只有输入.json"]), 2)

    def test_main_missing_input_returns_1(self):
        out = self._out("cli-page-missing-out.json")
        self.assertEqual(page.main([str(INPUTS / "不存在.json"), str(out)]), 1)
        self.assertFalse(out.exists())

    def test_main_bad_day_returns_1(self):
        out = self._out("cli-page-badday-out.json")
        self.assertEqual(
            page.main([str(INPUTS / "page-missing-day.json"), str(out)]), 1
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
