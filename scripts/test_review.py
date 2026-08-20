#!/usr/bin/env python3
"""复习快查文档脚本（ticket 13）测试——以样例输入文件驱动脚本，断言输出文件内容。

遵循 spec「测试 seam」与「Testing Decisions」：唯一 seam 是 scripts/ 纯函数，
测试形态为「读输入文件 → 写输出文件」契约，只测外部行为、不测实现细节。
生成文档的用例额外断言写盘后的 `review/*.md` 原文，锁定快查文档行格式；
调度联动用例把 generate 输出的 `schedule_add` 接到 `scripts/schedule.py`
（op=add），实测「知识点 → 掌握度 → 下次复习日」写入调度表（ticket 13
「调度表更新」清单项）。

格式与契约见 ../resources/review-contract.md 与 ../resources/data-formats.md §5。
运行：python scripts/test_review.py
注意：沙箱下 tempfile 不可写，测试全部使用静态夹具（testdata/）与固定
输出目录（testdata/_out/）。generate 写盘目标一律指向 testdata/_out/review/；
query 读 testdata/review/ 下的只读夹具（含一份 schedule.md 以验证不参与查阅）。
"""
import json
import sys
import unittest
from pathlib import Path

# 让测试直接 import 同目录的 review / schedule 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import review
import schedule

TESTDATA = Path(__file__).resolve().parent / "testdata"
INPUTS = TESTDATA / "input"
REVIEWS = TESTDATA / "review"
OUTDIR = TESTDATA / "_out"
REVIEW_OUT = OUTDIR / "review"
SCHED_OUT = OUTDIR / "schedule"
INPUT_OUT = OUTDIR / "input"

# 常用期望原文（generate 生成的最小/基本文档）
DOC03_HEAD = (
    "---\n"
    "course: 03\n"
    "date: 2026-08-23\n"
    "topics: [pandas.Series, pandas.DataFrame]\n"
    "---\n"
    "\n"
    "# 03 — pandas Series 与 DataFrame\n"
    "\n"
)


class _ReviewTest(unittest.TestCase):
    """共享夹具目录与输出目录（各测试独立输出文件名，互不覆盖）。"""

    def setUp(self):
        OUTDIR.mkdir(parents=True, exist_ok=True)
        REVIEW_OUT.mkdir(parents=True, exist_ok=True)
        SCHED_OUT.mkdir(parents=True, exist_ok=True)
        INPUT_OUT.mkdir(parents=True, exist_ok=True)
        # 清理上次运行遗留的生成文件，保证重复运行结果一致
        # （只删 _out/review/ 与 _out/input/review/ 下的生成副本，不碰只读夹具）
        for stale in REVIEW_OUT.glob("*.md"):
            stale.unlink()
        default_dir = INPUT_OUT / "review"
        if default_dir.exists():
            for stale in default_dir.glob("*.md"):
                stale.unlink()

    def _out(self, name):
        return OUTDIR / name

    def _run(self, input_name, out_name):
        """以静态输入夹具驱动 run()，断言输出文件已写出。"""
        out = self._out(out_name)
        result = review.run(INPUTS / input_name, out)
        self.assertTrue(out.exists())
        return result, out

    def _write_input(self, name, data):
        """把场景输入写成 _out/input/ 下的 JSON（供多步/生成式场景复用文件契约）。"""
        path = INPUT_OUT / name
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def _copy_schedule(self, fixture, dest_name):
        """把 testdata/schedule/ 下的只读夹具复制到 _out/schedule/（可写副本）。"""
        dst = SCHED_OUT / dest_name
        dst.write_text(
            (TESTDATA / "schedule" / fixture).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        return dst

    def _read_file(self, path):
        return Path(path).read_text(encoding="utf-8")


class GenerateTest(_ReviewTest):
    """op=generate：按课程一份生成快查文档。"""

    def test_generate_creates_doc_with_row_format(self):
        result, out = self._run("gen-basic.json", "gen-basic-out.json")
        self.assertEqual(result["op"], "generate")
        self.assertEqual(result["course"], 3)
        self.assertEqual(result["course_label"], "03")
        self.assertEqual(result["title"], "pandas Series 与 DataFrame")
        self.assertEqual(result["date"], "2026-08-23")
        self.assertEqual(
            result["topics"], ["pandas.Series", "pandas.DataFrame"]
        )
        self.assertEqual(result["filename"], "03-pandas-series-与-dataframe.md")
        self.assertEqual(result["line_count"], 2)
        self.assertEqual(
            result["points"],
            [
                {
                    "topic": "Series",
                    "concept": "一维带标签数组",
                    "example": "s = pd.Series([1, 2, 3])",
                    "pitfall": "索引不连续时 s[0] 按位置取，标签恰为 0 时按标签取，易混；优先用 s.iloc[0] / s.loc[0]",
                    "source": "sources/pandas-series.md",
                },
                {
                    "topic": "DataFrame",
                    "concept": "二维表，由 Series 组成",
                    "example": "pd.DataFrame({'a': [1, 2], 'b': [3, 4]})",
                    "pitfall": "列名大小写敏感；df['缺列'] 报 KeyError",
                    "source": "sources/pandas-series.md",
                },
            ],
        )
        # 调度新增建议：未给 mastery 的知识点默认 2.0，给了的按输入
        self.assertEqual(
            result["schedule_add"],
            [
                {"topic": "Series", "mastery": 2.0},
                {"topic": "DataFrame", "mastery": 3.0},
            ],
        )
        # 输出文件内容与返回值一致
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)
        # 写盘后的快查文档原文：frontmatter + H1 + 每知识点一行
        self.assertEqual(
            self._read_file(REVIEW_OUT / result["filename"]),
            DOC03_HEAD
            + "- **Series**：一维带标签数组。`s = pd.Series([1, 2, 3])`；"
            "常见坑：索引不连续时 s[0] 按位置取，标签恰为 0 时按标签取，易混；"
            "优先用 s.iloc[0] / s.loc[0]；来源：sources/pandas-series.md。\n"
            "- **DataFrame**：二维表，由 Series 组成。"
            "`pd.DataFrame({'a': [1, 2], 'b': [3, 4]})`；"
            "常见坑：列名大小写敏感；df['缺列'] 报 KeyError；"
            "来源：sources/pandas-series.md。\n",
        )

    def test_generate_with_optional_fields_only(self):
        # 无示例 / 无常见坑的知识点：对应段省略，concept → 来源 直连
        result, _ = self._run("gen-plain.json", "gen-plain-out.json")
        self.assertEqual(result["filename"], "04-数据读取与筛选.md")
        self.assertEqual(result["line_count"], 1)
        self.assertEqual(
            self._read_file(REVIEW_OUT / result["filename"]),
            "---\n"
            "course: 04\n"
            "date: 2026-08-24\n"
            "topics: [数据读取与筛选]\n"
            "---\n"
            "\n"
            "# 04 — 数据读取与筛选\n"
            "\n"
            "- **布尔筛选**：按布尔掩码取行。`df[df['列'] > 100]`；"
            "常见坑：链式索引赋值不生效，改用 loc；"
            "来源：https://pandas.pydata.org/docs/user_guide/indexing.html。\n",
        )

    def test_generate_default_mastery_for_schedule_add(self):
        result, _ = self._run("gen-no-mastery.json", "gen-no-mastery-out.json")
        self.assertEqual(
            result["schedule_add"],
            [{"topic": "读取 Excel", "mastery": 2.0}],
        )

    def test_generate_mastery_rounds_to_half_step(self):
        # mastery 规范到 0.5 档（半向上舍入），与能力矩阵/调度表展示一致
        inp = self._write_input(
            "gen-round.json",
            {
                "op": "generate",
                "review_path": "../review",
                "course": 8,
                "title": "掌握度取整课程",
                "date": "2026-08-26",
                "points": [
                    {
                        "topic": "取整知识点",
                        "concept": "掌握度 2.7 → 2.5",
                        "source": "sources/python-basics.md",
                        "mastery": 2.7,
                    },
                    {
                        "topic": "封顶知识点",
                        "concept": "掌握度 9 → 5.0",
                        "source": "sources/python-basics.md",
                        "mastery": 9,
                    },
                ],
            },
        )
        result = review.run(inp, self._out("gen-round-out.json"))
        self.assertEqual(
            result["schedule_add"],
            [
                {"topic": "取整知识点", "mastery": 2.5},
                {"topic": "封顶知识点", "mastery": 5.0},
            ],
        )

    def test_generate_refuses_overwrite_by_default(self):
        # 同一课程已沉淀 → 默认拒绝覆盖（按课程一份）
        self._run("gen-basic.json", "gen-overwrite-refuse-out.json")
        with self.assertRaises(ValueError) as ctx:
            review.run(INPUTS / "gen-basic.json", self._out("gen-overwrite-refuse2-out.json"))
        self.assertIn("已存在", str(ctx.exception))

    def test_generate_overwrite_flag_replaces(self):
        self._run("gen-basic.json", "gen-overwrite-flag-out.json")
        result, _ = self._run("gen-overwrite.json", "gen-overwrite-out.json")
        self.assertEqual(result["line_count"], 1)
        self.assertEqual(
            self._read_file(REVIEW_OUT / "03-pandas-series-与-dataframe.md"),
            "---\n"
            "course: 03\n"
            "date: 2026-08-24\n"
            "topics: [pandas.Series, pandas.DataFrame]\n"
            "---\n"
            "\n"
            "# 03 — pandas Series 与 DataFrame\n"
            "\n"
            "- **Series**：一维带标签数组（重写版）；来源：sources/pandas-series.md。\n",
        )

    def test_generate_creates_parent_dir(self):
        # review 目录不存在时自动创建（与调度表写回同一策略）
        result, _ = self._run("gen-plain.json", "gen-plain-dir-out.json")
        self.assertTrue((REVIEW_OUT / result["filename"]).exists())

    def test_generate_default_review_dir_resolves_next_to_input(self):
        # 未给 review_path → 以输入文件所在目录为基准解析到 ./review
        inp = self._write_input(
            "gen-default-dir.json",
            {
                "op": "generate",
                "course": 6,
                "title": "默认目录",
                "date": "2026-08-26",
                "points": [
                    {
                        "topic": "知识点",
                        "concept": "默认目录测试",
                        "source": "sources/python-basics.md",
                    }
                ],
            },
        )
        result = review.run(inp, self._out("gen-default-dir-out.json"))
        self.assertEqual(result["filename"], "06-默认目录.md")
        self.assertTrue((INPUT_OUT / "review" / "06-默认目录.md").exists())
        self.assertEqual(result["review_path"], str((INPUT_OUT / "review").resolve()))


class GenerateErrorTest(_ReviewTest):
    """op=generate 输入错误处理。"""

    def test_missing_source_raises(self):
        # 知识点缺来源：无依据的断言禁止落盘（护栏「引用规范」）
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-no-source.json", self._out("gen-no-source-out.json"))

    def test_empty_points_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-empty-points.json", self._out("gen-empty-out.json"))

    def test_missing_title_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-no-title.json", self._out("gen-no-title-out.json"))

    def test_topic_with_pipe_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-bad-topic.json", self._out("gen-bad-topic-out.json"))

    def test_source_with_pipe_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-bad-source.json", self._out("gen-bad-source-out.json"))

    def test_course_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-course-high.json", self._out("gen-course-high-out.json"))

    def test_bad_date_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-bad-date.json", self._out("gen-bad-date-out.json"))

    def test_points_not_list_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-points-not-list.json", self._out("gen-pnl-out.json"))

    def test_point_not_object_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-point-not-object.json", self._out("gen-pno-out.json"))

    def test_topics_not_list_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "gen-bad-topics.json", self._out("gen-btopics-out.json"))


class QueryTest(_ReviewTest):
    """op=query：按知识点关键词 / 日期查阅快查文档（只读）。"""

    def test_query_by_topic(self):
        result, out = self._run("q-topic.json", "q-topic-out.json")
        self.assertEqual(result["op"], "query")
        self.assertEqual(result["query"], "Series")
        self.assertIsNone(result["date"])
        self.assertEqual(result["total_docs"], 1)
        match = result["matches"][0]
        self.assertEqual(match["file"], "03-pandas-series.md")
        self.assertEqual(match["course"], 3)
        self.assertEqual(match["date"], "2026-08-23")
        self.assertEqual(
            match["topics"], ["pandas.Series", "pandas.DataFrame"]
        )
        self.assertEqual(match["title"], "03 — pandas Series 与 DataFrame")
        self.assertEqual(len(match["points"]), 2)
        self.assertEqual(match["points"][0]["topic"], "Series")
        self.assertEqual(match["points"][0]["source"], "sources/pandas-series.md")
        self.assertTrue(match["points"][0]["text"].startswith("- **Series**："))
        # 输出文件内容与返回值一致
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)

    def test_query_by_topic_chinese(self):
        # 中文关键词：命中 topics 与行文本（数据读取与筛选）
        result, _ = self._run("q-topic-cn.json", "q-topic-cn-out.json")
        self.assertEqual(result["total_docs"], 1)
        self.assertEqual(result["matches"][0]["file"], "04-reading-filtering.md")

    def test_query_by_date(self):
        # 2026-08-23 → 03（规范日期）；05 frontmatter 手写 `2026-8-23` 也被
        # 规范后命中（查询层日期归一）
        result, _ = self._run("q-date.json", "q-date-out.json")
        self.assertEqual(result["date"], "2026-08-23")
        self.assertEqual(result["total_docs"], 2)
        files = [m["file"] for m in result["matches"]]
        self.assertEqual(files, ["03-pandas-series.md", "05-raw-date.md"])

    def test_query_by_topic_and_date(self):
        result, _ = self._run("q-both.json", "q-both-out.json")
        self.assertEqual(result["query"], "pandas")
        self.assertEqual(result["date"], "2026-08-23")
        self.assertEqual(result["total_docs"], 1)
        self.assertEqual(result["matches"][0]["file"], "03-pandas-series.md")

    def test_query_all_lists_docs_and_excludes_schedule(self):
        # 无关键词/日期 → 列出全部快查文档；schedule.md 不参与查阅
        result, _ = self._run("q-all.json", "q-all-out.json")
        self.assertEqual(result["total_docs"], 4)
        files = [m["file"] for m in result["matches"]]
        self.assertEqual(
            files,
            [
                "01-variables-conditions.md",
                "03-pandas-series.md",
                "04-reading-filtering.md",
                "05-raw-date.md",
            ],
        )
        self.assertNotIn("schedule.md", files)

    def test_query_no_hit_returns_empty(self):
        result, _ = self._run("q-no-hit.json", "q-no-hit-out.json")
        self.assertEqual(result["total_docs"], 0)
        self.assertEqual(result["matches"], [])

    def test_query_missing_dir_returns_empty(self):
        # 复习目录尚不存在 → 空结果，不报错（与调度表 due 缺文件同一策略）
        result, _ = self._run("q-missing-dir.json", "q-missing-dir-out.json")
        self.assertEqual(result["total_docs"], 0)


class QueryErrorTest(_ReviewTest):
    """op=query 输入错误处理。"""

    def test_bad_date_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "q-bad-date.json", self._out("q-bad-date-out.json"))

    def test_bad_query_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "q-bad-query.json", self._out("q-bad-query-out.json"))


class CommonErrorTest(_ReviewTest):
    """两操作共用的输入错误处理。"""

    def test_bad_op_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "rev-bad-op.json", self._out("rev-bad-op-out.json"))

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            review.run(INPUTS / "not-json.json", self._out("not-json-out.json"))

    def test_missing_input_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            review.run(INPUTS / "无此输入.json", self._out("nope-out.json"))


class ScheduleIntegrationTest(_ReviewTest):
    """ticket 13「调度表更新」：generate 的 schedule_add → schedule.py add 联动。"""

    def test_generate_then_register_points_into_schedule(self):
        # 1) 生成快查文档，拿到 schedule_add（新知识点 + 掌握度）
        result, _ = self._run("gen-basic.json", "gen-integ-out.json")
        self.assertEqual(
            result["schedule_add"],
            [
                {"topic": "Series", "mastery": 2.0},
                {"topic": "DataFrame", "mastery": 3.0},
            ],
        )
        # 2) 对每个新知识点调 schedule.py op=add（today 与课程同日）
        self._copy_schedule("empty.md", "gen-integ.md")
        for add in result["schedule_add"]:
            inp = self._write_input(
                f"gen-integ-{add['topic']}.json",
                {
                    "today": "2026-08-23",
                    "schedule_path": "../schedule/gen-integ.md",
                    "op": "add",
                    "topic": add["topic"],
                    "mastery": add["mastery"],
                },
            )
            row = schedule.run(inp, self._out(f"gen-integ-{add['topic']}-out.json"))["row"]
            self.assertEqual(row["next_date"], "2026-08-24")
            self.assertEqual(row["interval"], 1)
        # 3) 调度表原文：两个新知识点 → 掌握度 / 下次复习日 / 间隔 落盘
        self.assertEqual(
            self._read_file(SCHED_OUT / "gen-integ.md"),
            "---\n"
            "updated: 2026-08-23\n"
            "---\n"
            "\n"
            "# 复习调度表\n"
            "\n"
            "| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |\n"
            "| --- | --- | --- | --- |\n"
            "| Series | 2/5 | 2026-08-24 | 1 |\n"
            "| DataFrame | 3/5 | 2026-08-24 | 1 |\n",
        )


class CliTest(_ReviewTest):
    """命令行入口 main()。"""

    def test_main_generate_writes_output(self):
        out = self._out("cli-gen-out.json")
        code = review.main([str(INPUTS / "gen-plain.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["op"], "generate")

    def test_main_query_writes_output(self):
        out = self._out("cli-query-out.json")
        code = review.main([str(INPUTS / "q-topic.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["total_docs"], 1)

    def test_main_wrong_arg_count_returns_2(self):
        self.assertEqual(review.main([]), 2)
        self.assertEqual(review.main(["只有输入.json"]), 2)

    def test_main_missing_input_returns_1(self):
        out = self._out("cli-missing-out.json")
        self.assertEqual(
            review.main([str(INPUTS / "无此输入.json"), str(out)]), 1
        )
        self.assertFalse(out.exists())

    def test_main_bad_op_returns_1(self):
        out = self._out("cli-bad-op-out.json")
        self.assertEqual(review.main([str(INPUTS / "rev-bad-op.json"), str(out)]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
