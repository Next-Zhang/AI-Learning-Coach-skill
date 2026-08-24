#!/usr/bin/env python3
"""自动核对脚本（修订批次 3）测试——以样例输入文件驱动脚本，断言输出文件内容。

遵循 spec「测试 seam」与「Testing Decisions」：唯一 seam 是 scripts/ 纯函数，
测试形态为「读输入文件 → 写输出文件」契约，只测外部行为、不测实现细节。
因此本套测试全部经 run()/main() 走文件契约；核对脚本只读不改数据文件，
无需复制夹具（区别于 profile.py/schedule.py 的写回测试）。

校验范围与契约见 ../resources/check-contract.md。
运行：python scripts/test_check.py
注意：沙箱下 tempfile 不可写，测试全部使用静态夹具（testdata/check/）与
固定输出目录（testdata/_out/check/）。
"""
import json
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
import unittest
from pathlib import Path

# 让测试直接 import 同目录的 check 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check

TESTDATA = Path(__file__).resolve().parent / "testdata"
INPUTS = TESTDATA / "input"
OUTDIR = TESTDATA / "_out"
CHECK_OUT = OUTDIR / "check"


class _CheckTest(unittest.TestCase):
    """共享输出目录（各测试独立输出文件名，互不覆盖）。"""

    def setUp(self):
        OUTDIR.mkdir(parents=True, exist_ok=True)
        CHECK_OUT.mkdir(parents=True, exist_ok=True)
        for stale in CHECK_OUT.glob("*.json"):
            stale.unlink()

    def _out(self, name):
        return CHECK_OUT / name

    def _run(self, input_name, out_name):
        """以静态输入夹具驱动 run()，断言输出文件已写出并返回结果。"""
        out = self._out(out_name)
        result = check.run(INPUTS / input_name, out)
        self.assertTrue(out.exists())
        return result, out

    def _messages(self, problems, level=None):
        return [
            p["message"] for p in problems if level is None or p["level"] == level
        ]


class FullRunTest(_CheckTest):
    """全量核对：好数据全绿、坏数据逐类报错。"""

    def test_full_good_ok(self):
        result, out = self._run("check-full-good.json", "full-good-out.json")
        self.assertTrue(result["ok"])
        self.assertEqual(result["date"], "2026-08-22")
        self.assertEqual(result["summary"]["errors"], 0)
        self.assertEqual(result["summary"]["warnings"], 0)
        self.assertEqual(
            result["summary"]["checks_run"],
            [
                "plan_structure",
                "plan_refs",
                "writeback_consistent",
                "evidence_consistent",
                "decision_log",
            ],
        )
        self.assertEqual(result["summary"]["skipped"], [])
        # 输出文件内容与返回值一致
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)

    def test_full_bad_reports_every_check(self):
        result, out = self._run("check-full-bad.json", "full-bad-out.json")
        self.assertFalse(result["ok"])
        self.assertEqual(result["summary"]["errors"], 9)
        self.assertEqual(result["summary"]["warnings"], 7)
        msgs = self._messages(result["problems"])
        # plan_refs：矩阵外知识点/前置、知识点引能力行
        self.assertIn("知识点 未知知识点 不在能力矩阵中", msgs)
        self.assertIn("前置 未知前置 不在能力矩阵中", msgs)
        self.assertIn("知识点 Python 工程组织 引用了能力行（计划知识点应为知识点行）", msgs)
        # plan_structure：日期非法、来源缺失
        self.assertIn("Day 3 日期非法（应为 YYYY-MM-DD）：2026-08-XX", msgs)
        self.assertIn("Day 4 缺少来源行（必需字段）", msgs)
        self.assertIn("Day 4 目标清单项应为 `- [ ]` checkbox：- 未用 checkbox 的目标", msgs)
        # writeback_consistent：验收写回 topic 与当日计划不一致
        self.assertIn("验收写回 topic 计划外知识点 与当日计划知识点不一致（2026-08-21）", msgs)
        # evidence_consistent：证据知识点与当日计划不一致、旧自由文本格式告警
        self.assertIn("证据知识点 计划外知识点 与当日计划知识点不一致（2026-08-20）", msgs)
        self.assertIn(
            "证据摘要为旧自由文本格式（2099-02-02），批次 3 起改用条目式证据（data-formats §2）",
            msgs,
        )
        # 字段行在证据条目之后 → 结束证据列表，不误判为 malformed
        self.assertNotIn(
            "证据条目格式不符合 `- [目标] 描述 → 知识点`（2026-08-20）：- 当日总结：字段行在证据之后 → 不应被当成 malformed",
            msgs,
        )
        # decision_log：坏行报错
        self.assertIn("第 2 行不是合法记录行（YYYY-MM-DD | …）：2026-99-99 | 坏日期", msgs)
        self.assertIn("第 3 行不是合法记录行（YYYY-MM-DD | …）：没有日期的行", msgs)

    def test_structure_only_reports_structure(self):
        # 结构坏数据 + 引用全好的矩阵：只出结构类问题
        result, _ = self._run("check-structure.json", "structure-out.json")
        self.assertFalse(result["ok"])
        self.assertEqual(result["summary"]["errors"], 2)
        self.assertEqual(result["summary"]["warnings"], 4)
        errs = self._messages(result["problems"], "error")
        self.assertIn("Day 3 日期非法（应为 YYYY-MM-DD）：2026-08-XX", errs)
        self.assertIn("Day 4 缺少来源行（必需字段）", errs)
        warns = self._messages(result["problems"], "warning")
        self.assertIn("Day 3 缺少目标清单", warns)
        self.assertIn("Day 4 缺少主题", warns)
        self.assertIn("Day 4 目标清单项应为 `- [ ]` checkbox：- 未用 checkbox 的目标", warns)
        # 画像验收记录日期不在该计划中 → writeback 无法核对（warning，非 error）
        self.assertIn("画像验收记录 2026-08-20 不在计划中，无法核对知识点口径", warns)


class ScopeTest(_CheckTest):
    """day 作用域：只查指定 Day 的 plan 结构与引用。"""

    def test_day_scope_limits_plan_checks(self):
        result, _ = self._run("check-day.json", "day-out.json")
        self.assertFalse(result["ok"])
        self.assertEqual(result["summary"]["errors"], 1)
        self.assertEqual(result["summary"]["warnings"], 0)
        errs = self._messages(result["problems"], "error")
        # 只有 Day 2 的引用问题；Day 1 的矩阵外知识点/前置被作用域排除
        self.assertIn("知识点 Python 工程组织 引用了能力行（计划知识点应为知识点行）", errs)
        self.assertNotIn("知识点 未知知识点 不在能力矩阵中", errs)
        # 未传 progress/decision → 对应校验跳过
        self.assertEqual(result["summary"]["skipped"], ["evidence_consistent", "decision_log"])


class AcceptanceTest(_CheckTest):
    """验收写回前：acceptance_topics 与当日计划知识点口径一致。"""

    def test_acceptance_topics_match_day(self):
        result, _ = self._run("check-acceptance-good.json", "acc-good-out.json")
        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"]["errors"], 0)
        self.assertEqual(result["summary"]["warnings"], 0)

    def test_acceptance_topics_mismatch(self):
        result, _ = self._run("check-acceptance-mismatch.json", "acc-bad-out.json")
        self.assertFalse(result["ok"])
        self.assertEqual(result["summary"]["errors"], 1)
        self.assertEqual(result["summary"]["warnings"], 1)
        errs = self._messages(result["problems"], "error")
        self.assertIn("写回 topic 未知知识点 不在当日计划知识点中", errs)
        warns = self._messages(result["problems"], "warning")
        self.assertIn("写回清单未覆盖当日知识点 pandas.DataFrame（如为有意遗漏可忽略）", warns)


class CliTest(_CheckTest):
    """CLI 退出码与操作级错误。"""

    def test_wrong_arg_count_returns_2(self):
        self.assertEqual(check.main([]), 2)
        self.assertEqual(check.main(["只有输入.json"]), 2)

    def test_missing_plan_returns_1(self):
        out = self._out("cli-missing-plan-out.json")
        self.assertEqual(check.main([str(INPUTS / "check-missing-plan.json"), str(out)]), 1)
        self.assertFalse(out.exists())

    def test_bad_day_returns_1(self):
        out = self._out("cli-bad-day-out.json")
        self.assertEqual(check.main([str(INPUTS / "check-bad-day.json"), str(out)]), 1)
        self.assertFalse(out.exists())

    def test_acceptance_without_day_returns_1(self):
        out = self._out("cli-acc-no-day-out.json")
        self.assertEqual(
            check.main([str(INPUTS / "check-acceptance-no-day.json"), str(out)]), 1
        )
        self.assertFalse(out.exists())

    def test_main_writes_output(self):
        out = self._out("cli-good-out.json")
        code = check.main([str(INPUTS / "check-full-good.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertTrue(json.loads(out.read_text(encoding="utf-8"))["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
