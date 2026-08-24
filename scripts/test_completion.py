#!/usr/bin/env python3
"""完成度合成脚本（ticket 04）测试——以样例输入文件驱动脚本，断言输出文件内容。

遵循 spec「测试 seam」与「Testing Decisions」：唯一 seam 是 scripts/ 纯函数，
测试形态为「读输入文件 → 写输出文件」契约，只测外部行为、不测实现细节。
因此本套测试全部经 run()/main() 走文件契约。

合成规则（spec「混合式验收与完成度」+ SKILL.md「反馈与验收」）：
- 完成度分 = agent 评分 × 0.7 + 学习者自评 × 0.3，四舍五入到 0.5 档，截断在 [1, 5]；
- 难度反馈（太难 / 刚好 / 太简单）独立记录，不参与完成度分。
期望值全部手工计算（7×agent + 3×self 取十分位，再取整到 0.5 档），
不重算实现逻辑，保证断言独立。

契约与用法见 ../resources/completion-contract.md。
运行：python scripts/test_completion.py
注意：沙箱下 tempfile 不可写，测试全部使用静态夹具（testdata/）与
固定输出目录（testdata/_out/）。
"""
import json
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
import unittest
from pathlib import Path

# 让测试直接 import 同目录的 completion 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import completion

TESTDATA = Path(__file__).resolve().parent / "testdata"
INPUTS = TESTDATA / "input"
OUTDIR = TESTDATA / "_out"


class _OutDirTest(unittest.TestCase):
    """输出目录共享 setUp（各测试独立输出文件名，互不覆盖）。"""

    def setUp(self):
        OUTDIR.mkdir(parents=True, exist_ok=True)

    def _out(self, name):
        return OUTDIR / name


class ContractTest(_OutDirTest):
    """文件契约测试：样例输入文件 → 断言输出文件内容。"""

    def _run(self, input_name, out_name):
        out = self._out(out_name)
        result = completion.run(INPUTS / input_name, out)
        self.assertTrue(out.exists())
        return result, out

    # --- 7:3 合成规则 ---

    def test_basic_synthesis_7_3(self):
        # agent 4、自评 4：0.7×4 + 0.3×4 = 4 → 4.0
        result, out = self._run("comp-basic.json", "comp-basic-out.json")
        self.assertEqual(result["agent_score"], 4)
        self.assertEqual(result["self_score"], 4)
        self.assertEqual(result["raw"], 4.0)
        self.assertEqual(result["score"], 4.0)
        self.assertEqual(result["score_display"], "4/5")
        self.assertEqual(result["synthesis"], "0.7 × 4 + 0.3 × 4 = 4")
        self.assertEqual(result["difficulty"], "刚好")
        # 输出文件内容与返回值一致
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)

    def test_agent_high_self_low_rounds_to_half(self):
        # agent 5、自评 3：0.7×5 + 0.3×3 = 4.4 → 四舍五入到 4.5
        result, _ = self._run("comp-agent-high.json", "comp-agent-high-out.json")
        self.assertEqual(result["raw"], 4.4)
        self.assertEqual(result["score"], 4.5)
        self.assertEqual(result["score_display"], "4.5/5")
        self.assertEqual(result["synthesis"], "0.7 × 5 + 0.3 × 3 ≈ 4.5")

    def test_agent_low_self_high(self):
        # agent 3、自评 5：0.7×3 + 0.3×5 = 3.6 → 3.5
        result, _ = self._run("comp-agent-low.json", "comp-agent-low-out.json")
        self.assertEqual(result["raw"], 3.6)
        self.assertEqual(result["score"], 3.5)
        self.assertEqual(result["score_display"], "3.5/5")

    def test_round_half_up_from_43(self):
        # agent 4、自评 5：4.3 → 4.5（向 0.5 档取整，取大）
        result, _ = self._run("comp-round-43.json", "comp-round-43-out.json")
        self.assertEqual(result["raw"], 4.3)
        self.assertEqual(result["score"], 4.5)

    def test_round_half_up_from_47(self):
        # agent 5、自评 4：4.7 → 4.5（向最近 0.5 档）
        result, _ = self._run("comp-round-47.json", "comp-round-47-out.json")
        self.assertEqual(result["raw"], 4.7)
        self.assertEqual(result["score"], 4.5)

    def test_perfect_scores(self):
        result, _ = self._run("comp-perfect.json", "comp-perfect-out.json")
        self.assertEqual(result["raw"], 5.0)
        self.assertEqual(result["score"], 5.0)
        self.assertEqual(result["score_display"], "5/5")

    def test_min_scores(self):
        result, _ = self._run("comp-min.json", "comp-min-out.json")
        self.assertEqual(result["raw"], 1.0)
        self.assertEqual(result["score"], 1.0)
        self.assertEqual(result["score_display"], "1/5")

    # --- 截断 ---

    def test_scores_clamped_to_5(self):
        # 7/6 超出 1–5 → 按 5/5 合成
        result, _ = self._run("comp-clamp-high.json", "comp-clamp-high-out.json")
        self.assertEqual(result["agent_score"], 5)
        self.assertEqual(result["self_score"], 5)
        self.assertEqual(result["score"], 5.0)

    def test_scores_clamped_to_1(self):
        # -2/0 低于 1 → 按 1/1 合成
        result, _ = self._run("comp-clamp-low.json", "comp-clamp-low-out.json")
        self.assertEqual(result["agent_score"], 1)
        self.assertEqual(result["self_score"], 1)
        self.assertEqual(result["score"], 1.0)

    # --- 分数型输入的 0.5 档取整边界 ---

    def test_fractional_quarter_rounds_half_up(self):
        # 4.4/3.9：0.7×4.4 + 0.3×3.9 = 4.25 → 四舍五入到 4.5（x.25 进到 x.5）
        result, _ = self._run("comp-quarter.json", "comp-quarter-out.json")
        self.assertEqual(result["raw"], 4.25)
        self.assertEqual(result["score"], 4.5)
        self.assertEqual(result["score_display"], "4.5/5")
        self.assertEqual(result["synthesis"], "0.7 × 4.4 + 0.3 × 3.9 ≈ 4.5")

    def test_fractional_below_quarter_rounds_down(self):
        # 4.3/3.9：0.7×4.3 + 0.3×3.9 = 4.18 → 4.0（低于 4.25 档界）
        result, _ = self._run(
            "comp-quarter-down.json", "comp-quarter-down-out.json"
        )
        self.assertEqual(result["raw"], 4.18)
        self.assertEqual(result["score"], 4.0)
        self.assertEqual(result["score_display"], "4/5")


class DifficultyTest(_OutDirTest):
    """难度反馈：独立记录、不混入完成度分。"""

    def _run(self, input_name, out_name):
        out = self._out(out_name)
        result = completion.run(INPUTS / input_name, out)
        self.assertTrue(out.exists())
        return result, out

    def test_difficulty_too_hard_recorded_separately(self):
        result, _ = self._run("comp-difficulty-hard.json", "comp-diff-hard-out.json")
        self.assertEqual(result["difficulty"], "太难")
        # 难度不参与合成：2/2 仍是 2.0
        self.assertEqual(result["score"], 2.0)

    def test_difficulty_too_easy_recorded_separately(self):
        result, _ = self._run("comp-difficulty-easy.json", "comp-diff-easy-out.json")
        self.assertEqual(result["difficulty"], "太简单")
        self.assertEqual(result["score"], 2.0)

    def test_difficulty_absent_is_null(self):
        result, _ = self._run("comp-no-difficulty.json", "comp-no-diff-out.json")
        self.assertEqual(result["difficulty"], None)
        self.assertEqual(result["score"], 4.0)

    def test_same_scores_different_difficulty_same_score(self):
        # 同样分数配不同难度反馈 → 完成度分不变（反馈只单独记录）
        hard, _ = self._run("comp-difficulty-hard.json", "comp-diff-hard2-out.json")
        easy, _ = self._run("comp-difficulty-easy.json", "comp-diff-easy2-out.json")
        self.assertEqual(hard["score"], easy["score"])

    def test_invalid_difficulty_raises(self):
        # 难度反馈是封闭集合：非法值报错，防止脏数据入 progress.md
        with self.assertRaises(ValueError):
            completion.run(
                INPUTS / "comp-bad-difficulty.json",
                self._out("comp-bad-diff-out.json"),
            )


class ErrorTest(_OutDirTest):
    """输入错误处理。"""

    def test_missing_agent_score_raises(self):
        with self.assertRaises(ValueError):
            completion.run(
                INPUTS / "comp-missing-agent.json", self._out("comp-ma-out.json")
            )

    def test_missing_self_score_raises(self):
        with self.assertRaises(ValueError):
            completion.run(
                INPUTS / "comp-missing-self.json", self._out("comp-ms-out.json")
            )

    def test_nonnumeric_score_raises(self):
        with self.assertRaises(ValueError):
            completion.run(
                INPUTS / "comp-nonnumeric.json", self._out("comp-nn-out.json")
            )

    def test_non_object_input_raises(self):
        with self.assertRaises(ValueError):
            completion.run(
                INPUTS / "comp-not-object.json", self._out("comp-no-out.json")
            )

    def test_missing_input_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            completion.run(INPUTS / "不存在.json", self._out("nope-out.json"))


class CliTest(_OutDirTest):
    """命令行入口 main()。"""

    def test_main_writes_output(self):
        out = self._out("cli-comp-out.json")
        code = completion.main([str(INPUTS / "comp-basic.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(
            json.loads(out.read_text(encoding="utf-8"))["score"], 4.0
        )

    def test_main_wrong_arg_count_returns_2(self):
        self.assertEqual(completion.main([]), 2)
        self.assertEqual(completion.main(["只有输入.json"]), 2)

    def test_main_missing_input_returns_1(self):
        out = self._out("cli-comp-missing.json")
        self.assertEqual(
            completion.main([str(INPUTS / "不存在.json"), str(out)]), 1
        )
        self.assertFalse(out.exists())

    def test_main_bad_difficulty_returns_1(self):
        out = self._out("cli-comp-bad-diff.json")
        self.assertEqual(
            completion.main(
                [str(INPUTS / "comp-bad-difficulty.json"), str(out)]
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
