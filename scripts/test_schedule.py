#!/usr/bin/env python3
"""间隔重复调度脚本（ticket 03）测试——以样例输入文件驱动脚本，断言输出文件内容。

遵循 spec「测试 seam」与「Testing Decisions」：唯一 seam 是 scripts/ 纯函数，
测试形态为「读输入文件 → 写输出文件」契约，只测外部行为、不测实现细节。
因此本套测试全部经 run()/main() 走文件契约；涉及调度表写回的用例，
额外断言写盘后的调度表原文，锁定表格格式。

调度规则与契约见 ../resources/schedule-contract.md。
运行：python scripts/test_schedule.py
注意：沙箱下 tempfile 不可写，测试全部使用静态夹具（testdata/）与
固定输出目录（testdata/_out/）；add/record 会原地改写调度表文件，
因此这类用例先把夹具复制到 testdata/_out/schedule/ 再运行。
"""
import json
import sys
import unittest
from pathlib import Path

# 让测试直接 import 同目录的 schedule 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import schedule

TESTDATA = Path(__file__).resolve().parent / "testdata"
INPUTS = TESTDATA / "input"
SCHEDULES = TESTDATA / "schedule"
OUTDIR = TESTDATA / "_out"
SCHED_OUT = OUTDIR / "schedule"
INPUT_OUT = OUTDIR / "input"


class _ScheduleTest(unittest.TestCase):
    """共享夹具目录与输出目录（各测试独立输出文件名，互不覆盖）。"""

    def setUp(self):
        OUTDIR.mkdir(parents=True, exist_ok=True)
        SCHED_OUT.mkdir(parents=True, exist_ok=True)
        INPUT_OUT.mkdir(parents=True, exist_ok=True)
        # 清理上次运行遗留的可写副本，保证重复运行结果一致
        # （只删 _out/schedule/ 下的生成副本，不碰 testdata/schedule/ 只读夹具）
        for stale in SCHED_OUT.glob("*.md"):
            stale.unlink()

    def _out(self, name):
        return OUTDIR / name

    def _copy_schedule(self, fixture, dest_name):
        """把 testdata/schedule/ 下的只读夹具复制到 _out/schedule/（可写副本）。"""
        dst = SCHED_OUT / dest_name
        dst.write_text(
            (SCHEDULES / fixture).read_text(encoding="utf-8"), encoding="utf-8"
        )
        return dst

    def _run(self, input_name, out_name):
        """以静态输入夹具驱动 run()，断言输出文件已写出。"""
        out = self._out(out_name)
        result = schedule.run(INPUTS / input_name, out)
        self.assertTrue(out.exists())
        return result, out

    def _write_input(self, name, data):
        """把场景输入写成 _out/input/ 下的 JSON（供多步/生成式场景复用文件契约）。"""
        path = INPUT_OUT / name
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def _read_file(self, path):
        return Path(path).read_text(encoding="utf-8")


class DueTest(_ScheduleTest):
    """op=due：查到期知识点（下次复习日 ≤ today），只读。"""

    def test_due_returns_only_due_points_sorted(self):
        # today=2026-08-21：Series 明日到期（21≤21）→ 到期；DataFrame 24 日才到期 → 不出
        result, out = self._run("due-basic.json", "due-basic-out.json")
        self.assertEqual(result["op"], "due")
        self.assertEqual(result["today"], "2026-08-21")
        self.assertEqual(len(result["due"]), 1)
        row = result["due"][0]
        self.assertEqual(row["topic"], "pandas.Series")
        self.assertEqual(row["mastery"], 2.0)
        self.assertEqual(row["next_date"], "2026-08-21")
        self.assertEqual(row["interval"], 1)
        # 输出文件内容与返回值一致
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)

    def test_due_all_when_everything_due(self):
        result, _ = self._run("due-all.json", "due-all-out.json")
        self.assertEqual(
            [r["topic"] for r in result["due"]],
            ["pandas.Series", "pandas.DataFrame"],
        )

    def test_due_empty_schedule(self):
        result, _ = self._run("due-empty.json", "due-empty-out.json")
        self.assertEqual(result["due"], [])

    def test_due_missing_schedule_returns_empty(self):
        # 尚未生成调度表时视为无到期知识点，不报错
        result, _ = self._run("due-missing.json", "due-missing-out.json")
        self.assertEqual(result["due"], [])

    def test_due_skips_malformed_rows(self):
        # 掌握度无法解析的「坏行」被跳过，其余行正常返回
        result, _ = self._run("due-dirty.json", "due-dirty-out.json")
        self.assertEqual(
            [r["topic"] for r in result["due"]],
            ["pandas.Series", "pandas.DataFrame"],
        )

    def test_due_without_frontmatter(self):
        # 无 frontmatter 的调度表也能解析
        result, _ = self._run("due-nofm.json", "due-nofm-out.json")
        self.assertEqual([r["topic"] for r in result["due"]], ["pandas.Series"])

    def test_due_ignores_blank_lines_inside_table(self):
        # 表格内空行透明跳过：空行后的行仍被解析，直到真正的非表格内容才停止
        result, _ = self._run("due-spaced.json", "due-spaced-out.json")
        self.assertEqual(
            [r["topic"] for r in result["due"]],
            ["pandas.Series", "pandas.DataFrame"],
        )


class RecordTest(_ScheduleTest):
    """op=record：记录一次考察结果，推进间隔并原地写回调度表。"""

    def test_record_pass_advances_interval_and_mastery(self):
        # basic.md 副本：Series（2/5，间隔 1）通过 → 2.5/5、间隔 3、下次 = 今天+3
        self._copy_schedule("basic.md", "record-pass.md")
        result, _ = self._run("record-pass.json", "record-pass-out.json")
        self.assertEqual(result["op"], "record")
        self.assertEqual(result["result"], "pass")
        self.assertEqual(
            result["row"],
            {
                "topic": "pandas.Series",
                "mastery": 2.5,
                "next_date": "2026-08-24",
                "interval": 3,
            },
        )
        # 写盘后的调度表原文：目标行更新、其余行不动、顺序保留、frontmatter 更新
        self.assertEqual(
            self._read_file(SCHED_OUT / "record-pass.md"),
            "---\n"
            "updated: 2026-08-21\n"
            "---\n"
            "\n"
            "# 复习调度表\n"
            "\n"
            "| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |\n"
            "| --- | --- | --- | --- |\n"
            "| pandas.Series | 2.5/5 | 2026-08-24 | 3 |\n"
            "| pandas.DataFrame | 3/5 | 2026-08-24 | 3 |\n",
        )

    def test_record_fail_resets_to_one_day(self):
        # basic.md 副本：Series（间隔 1）未通过 → 1.5/5、重置回间隔 1、下次 = 明天
        self._copy_schedule("basic.md", "record-fail.md")
        result, _ = self._run("record-fail.json", "record-fail-out.json")
        self.assertEqual(result["result"], "fail")
        self.assertEqual(
            result["row"],
            {
                "topic": "pandas.Series",
                "mastery": 1.5,
                "next_date": "2026-08-22",
                "interval": 1,
            },
        )
        self.assertEqual(
            self._read_file(SCHED_OUT / "record-fail.md"),
            "---\n"
            "updated: 2026-08-21\n"
            "---\n"
            "\n"
            "# 复习调度表\n"
            "\n"
            "| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |\n"
            "| --- | --- | --- | --- |\n"
            "| pandas.Series | 1.5/5 | 2026-08-22 | 1 |\n"
            "| pandas.DataFrame | 3/5 | 2026-08-24 | 3 |\n",
        )

    def test_record_pass_at_30_day_stays_30(self):
        # 已在 30 天档通过 → 保持 30 天档，掌握度继续 +0.5
        self._copy_schedule("at-30.md", "record-at-30.md")
        result, _ = self._run("record-at-30.json", "record-at-30-out.json")
        self.assertEqual(result["row"]["interval"], 30)
        self.assertEqual(result["row"]["mastery"], 4.5)
        self.assertEqual(result["row"]["next_date"], "2026-09-20")

    def test_record_pass_caps_mastery_at_5(self):
        self._copy_schedule("cap.md", "record-cap.md")
        result, _ = self._run("record-cap.json", "record-cap-out.json")
        self.assertEqual(result["row"]["mastery"], 5.0)
        self.assertEqual(result["row"]["interval"], 15)
        self.assertEqual(result["row"]["next_date"], "2026-09-05")

    def test_record_fail_floors_mastery_at_1(self):
        self._copy_schedule("floor.md", "record-floor.md")
        result, _ = self._run("record-floor.json", "record-floor-out.json")
        self.assertEqual(result["row"]["mastery"], 1.0)
        self.assertEqual(result["row"]["interval"], 1)
        self.assertEqual(result["row"]["next_date"], "2026-08-22")

    def test_record_writes_frontmatter_when_missing(self):
        # 无 frontmatter 的调度表：record 写回时补上 updated frontmatter
        self._copy_schedule("no-frontmatter.md", "record-nofm.md")
        result, _ = self._run("record-nofm.json", "record-nofm-out.json")
        self.assertEqual(result["row"]["interval"], 3)
        self.assertTrue(
            self._read_file(SCHED_OUT / "record-nofm.md").startswith(
                "---\nupdated: 2026-08-21\n---\n"
            )
        )

    def test_record_preserves_rows_after_blank_line(self):
        # 表格内空行后的行不得在写回时被静默丢弃（容错 + 保持既有行的承诺）
        self._copy_schedule("spaced.md", "record-spaced.md")
        result, _ = self._run("record-spaced.json", "record-spaced-out.json")
        self.assertEqual(result["row"]["interval"], 3)
        self.assertEqual(
            self._read_file(SCHED_OUT / "record-spaced.md"),
            "---\n"
            "updated: 2026-08-21\n"
            "---\n"
            "\n"
            "# 复习调度表\n"
            "\n"
            "| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |\n"
            "| --- | --- | --- | --- |\n"
            "| pandas.Series | 2.5/5 | 2026-08-24 | 3 |\n"
            "| pandas.DataFrame | 3/5 | 2026-08-24 | 3 |\n",
        )

    def test_record_pass_chain_across_full_ladder(self):
        # 完整阶梯 1→3→7→15→30（30 保持）：同一副本上连续记录 5 次通过
        self._copy_schedule("ladder.md", "ladder.md")
        today = "2026-08-21"
        steps = [
            ("topic-1", 3, 1.5, "2026-08-24"),
            ("topic-3", 7, 2.5, "2026-08-28"),
            ("topic-7", 15, 3.0, "2026-09-05"),
            ("topic-15", 30, 3.5, "2026-09-20"),
            ("topic-30", 30, 4.5, "2026-09-20"),
        ]
        for i, (topic, interval, mastery, next_date) in enumerate(steps):
            inp = self._write_input(
                f"ladder-step-{i}.json",
                {
                    "today": today,
                    "schedule_path": "../schedule/ladder.md",
                    "op": "record",
                    "topic": topic,
                    "result": "pass",
                },
            )
            result = schedule.run(inp, self._out(f"ladder-step-{i}-out.json"))
            self.assertEqual(
                result["row"],
                {"topic": topic, "mastery": mastery,
                 "next_date": next_date, "interval": interval},
                f"阶梯第 {i + 1} 步（{topic}）推进错误",
            )
        self.assertEqual(
            self._read_file(SCHED_OUT / "ladder.md"),
            "---\n"
            "updated: 2026-08-21\n"
            "---\n"
            "\n"
            "# 复习调度表\n"
            "\n"
            "| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |\n"
            "| --- | --- | --- | --- |\n"
            "| topic-1 | 1.5/5 | 2026-08-24 | 3 |\n"
            "| topic-3 | 2.5/5 | 2026-08-28 | 7 |\n"
            "| topic-7 | 3/5 | 2026-09-05 | 15 |\n"
            "| topic-15 | 3.5/5 | 2026-09-20 | 30 |\n"
            "| topic-30 | 4.5/5 | 2026-09-20 | 30 |\n",
        )


class AddTest(_ScheduleTest):
    """op=add：新增知识点入调度表（间隔 1、下次复习日 = today + 1）。"""

    def test_add_new_point_appends_row(self):
        # empty.md 副本：追加新知识点，其余结构保持
        self._copy_schedule("empty.md", "add-new.md")
        result, _ = self._run("add-new.json", "add-new-out.json")
        self.assertEqual(result["op"], "add")
        self.assertEqual(
            result["row"],
            {
                "topic": "新知识点",
                "mastery": 2.5,
                "next_date": "2026-08-22",
                "interval": 1,
            },
        )
        self.assertEqual(
            self._read_file(SCHED_OUT / "add-new.md"),
            "---\n"
            "updated: 2026-08-21\n"
            "---\n"
            "\n"
            "# 复习调度表\n"
            "\n"
            "| 知识点 | 掌握度 | 下次复习日 | 当前间隔(天) |\n"
            "| --- | --- | --- | --- |\n"
            "| 新知识点 | 2.5/5 | 2026-08-22 | 1 |\n",
        )

    def test_add_first_point_creates_schedule_file(self):
        # 调度表尚不存在 → add 创建文件并写入首行
        result, _ = self._run("add-first.json", "add-first-out.json")
        self.assertEqual(result["row"]["topic"], "首条知识点")
        self.assertEqual(result["row"]["next_date"], "2026-08-21")
        self.assertTrue((SCHED_OUT / "add-first.md").exists())

    def test_add_default_mastery(self):
        # 未给 mastery → 默认 2.0
        self._copy_schedule("empty.md", "add-default.md")
        result, _ = self._run("add-default.json", "add-default-out.json")
        self.assertEqual(result["row"]["mastery"], 2.0)

    def test_add_duplicate_topic_raises(self):
        self._copy_schedule("basic.md", "add-dup.md")
        with self.assertRaises(ValueError):
            schedule.run(INPUTS / "add-dup.json", self._out("add-dup-out.json"))

    def test_add_topic_with_pipe_raises(self):
        # 知识点名含 `|` 会破坏表格格式，必须拒绝
        self._copy_schedule("empty.md", "add-bad.md")
        with self.assertRaises(ValueError):
            schedule.run(INPUTS / "add-bad-topic.json", self._out("add-bad-out.json"))


class ErrorTest(_ScheduleTest):
    """输入错误处理。"""

    def test_bad_op_raises(self):
        with self.assertRaises(ValueError):
            schedule.run(INPUTS / "bad-op.json", self._out("bad-op-out.json"))

    def test_bad_date_raises(self):
        with self.assertRaises(ValueError):
            schedule.run(INPUTS / "bad-date.json", self._out("bad-date-out.json"))

    def test_record_unknown_topic_raises(self):
        self._copy_schedule("basic.md", "record-unknown.md")
        with self.assertRaises(ValueError):
            schedule.run(
                INPUTS / "record-unknown.json", self._out("record-unknown-out.json")
            )

    def test_record_bad_result_raises(self):
        self._copy_schedule("basic.md", "record-bad-result.md")
        with self.assertRaises(ValueError):
            schedule.run(
                INPUTS / "record-bad-result.json", self._out("record-bad-result-out.json")
            )

    def test_record_missing_schedule_raises(self):
        # 调度表不存在且 op=record → 报错（不能凭空记录考察结果）
        with self.assertRaises(FileNotFoundError):
            schedule.run(
                INPUTS / "record-nosched.json", self._out("record-nosched-out.json")
            )

    def test_missing_input_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            schedule.run(INPUTS / "不存在.json", self._out("nope-out.json"))


class CliTest(_ScheduleTest):
    """命令行入口 main()。"""

    def test_main_writes_output(self):
        out = self._out("cli-due-out.json")
        code = schedule.main([str(INPUTS / "due-basic.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["op"], "due")

    def test_main_wrong_arg_count_returns_2(self):
        self.assertEqual(schedule.main([]), 2)
        self.assertEqual(schedule.main(["只有输入.json"]), 2)

    def test_main_missing_input_returns_1(self):
        out = self._out("cli-missing-out.json")
        self.assertEqual(schedule.main([str(INPUTS / "不存在.json"), str(out)]), 1)
        self.assertFalse(out.exists())

    def test_main_bad_op_returns_1(self):
        out = self._out("cli-bad-op-out.json")
        self.assertEqual(schedule.main([str(INPUTS / "bad-op.json"), str(out)]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
