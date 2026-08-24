#!/usr/bin/env python3
"""画像更新脚本（ticket 05）测试——以样例输入文件驱动脚本，断言输出文件内容。

遵循 spec「测试 seam」与「Testing Decisions」：唯一 seam 是 scripts/ 纯函数，
测试形态为「读输入文件 → 写输出文件」契约，只测外部行为、不测实现细节。
因此本套测试全部经 run()/main() 走文件契约；涉及画像写回的用例，
额外断言写盘后的 profile.md 原文，锁定画像格式。

更新规则与契约见 ../resources/profile-contract.md。
运行：python scripts/test_profile.py
注意：沙箱下 tempfile 不可写，测试全部使用静态夹具（testdata/）与
固定输出目录（testdata/_out/）；四种操作都会原地改写画像文件，
因此涉及写回的用例先把夹具复制到 testdata/_out/profile/ 再运行。
"""
import json
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
import unittest
from pathlib import Path

# 让测试直接 import 同目录的 profile 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import profile

TESTDATA = Path(__file__).resolve().parent / "testdata"
INPUTS = TESTDATA / "input"
PROFILES = TESTDATA / "profile"
OUTDIR = TESTDATA / "_out"
PROFILE_OUT = OUTDIR / "profile"
INPUT_OUT = OUTDIR / "input"

# 常用画像区块（期望原文复用）
ONBOARDING_BASIC = (
    "## Onboarding 问卷（8 题）\n"
    "- 学习目标：用 Python 做数据分析\n"
    "- Python 水平自评（1–5）：2\n"
    "- 每日时间预算：1 小时\n"
    "- 学习风格偏好：视频 + 动手练习\n"
    "- 压力承受自评（1–5）：3\n"
    "- 期望节奏：平缓\n"
    "- 过往经历：无编程经验\n"
    "- 复习意愿：愿意每天 10 分钟"
)
MATRIX_HEAD = (
    "## 能力矩阵（领域 → 子领域 → 知识点/能力）\n"
    "| 领域 | 子领域 | 知识点 | 类型 | 水平分 | 前置状态 | 更新时间 | 来源 |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
)


class _ProfileTest(unittest.TestCase):
    """共享夹具目录与输出目录（各测试独立输出文件名，互不覆盖）。"""

    def setUp(self):
        OUTDIR.mkdir(parents=True, exist_ok=True)
        PROFILE_OUT.mkdir(parents=True, exist_ok=True)
        INPUT_OUT.mkdir(parents=True, exist_ok=True)
        # 清理上次运行遗留的可写副本，保证重复运行结果一致
        # （只删 _out/profile/ 下的生成副本，不碰 testdata/profile/ 只读夹具）
        for stale in PROFILE_OUT.glob("*.md"):
            stale.unlink()

    def _out(self, name):
        return OUTDIR / name

    def _copy_profile(self, fixture, dest_name):
        """把 testdata/profile/ 下的只读夹具复制到 _out/profile/（可写副本）。"""
        dst = PROFILE_OUT / dest_name
        dst.write_text(
            (PROFILES / fixture).read_text(encoding="utf-8"), encoding="utf-8"
        )
        return dst

    def _run(self, input_name, out_name):
        """以静态输入夹具驱动 run()，断言输出文件已写出。"""
        out = self._out(out_name)
        result = profile.run(INPUTS / input_name, out)
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


class OnboardingTest(_ProfileTest):
    """op=onboarding：问卷 8 题写入画像初值。"""

    def test_onboarding_creates_profile_file(self):
        # 画像文件尚不存在 → onboarding 创建完整画像（初值 + 空矩阵 + 日志）
        result, out = self._run("onboard-first.json", "onboard-first-out.json")
        self.assertEqual(result["op"], "onboarding")
        self.assertEqual(result["date"], "2026-08-19")
        self.assertEqual(result["created"], "2026-08-19")
        self.assertEqual(result["updated"], "2026-08-19")
        self.assertEqual(result["answers"]["学习目标"], "用 Python 做数据分析")
        self.assertEqual(result["answers"]["Python 水平自评（1–5）"], "2")
        self.assertEqual(result["answers"]["压力承受自评（1–5）"], "3")
        # 输出文件内容与返回值一致
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)
        # 写盘后的画像原文：8 题初值、空矩阵、onboarding 日志
        self.assertEqual(
            self._read_file(PROFILE_OUT / "onboard-first.md"),
            "---\n"
            "created: 2026-08-19\n"
            "updated: 2026-08-19\n"
            "---\n"
            "\n"
            "# 用户画像\n"
            "\n"
            + ONBOARDING_BASIC
            + "\n"
            "\n"
            + MATRIX_HEAD
            + "\n"
            "## 增量记录\n"
            "- 2026-08-19：onboarding 问卷 → 画像初值\n",
        )

    def test_onboarding_overwrite_preserves_matrix(self):
        # basic.md 副本：替换问卷初值，矩阵与既有日志保留，日志追加 onboarding 事件
        self._copy_profile("basic.md", "onboard-overwrite.md")
        result, _ = self._run("onboard-overwrite.json", "onboard-overwrite-out.json")
        self.assertEqual(result["answers"]["学习目标"], "用 Python 做自动化脚本")
        self.assertEqual(result["answers"]["Python 水平自评（1–5）"], "3")
        text = self._read_file(PROFILE_OUT / "onboard-overwrite.md")
        self.assertIn("## Onboarding 问卷（8 题）\n- 学习目标：用 Python 做自动化脚本", text)
        self.assertNotIn("视频 + 动手练习", text)
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 1.5 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertIn(
            "| 数据分析 | pandas | pandas.DataFrame | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        # 既有日志保留、新事件追加在末尾、updated 更新
        self.assertTrue(
            text.endswith(
                "## 增量记录\n"
                "- 2026-08-20：摸底测试 → 初始矩阵\n"
                "- 2026-08-20：onboarding 问卷 → 画像初值\n"
            )
        )
        self.assertIn("updated: 2026-08-20", text)

    def test_onboarding_over_empty_fills_placeholders(self):
        # empty.md 副本：占位问卷被真实答案替换，模板注释行被清除，矩阵仍为空
        self._copy_profile("empty.md", "onboard-empty.md")
        inp = self._write_input(
            "onboard-empty.json",
            {
                "date": "2026-08-19",
                "profile_path": "../profile/onboard-empty.md",
                "op": "onboarding",
                "answers": {
                    "学习目标": "用 Python 做数据分析",
                    "Python 水平自评（1–5）": 2,
                    "每日时间预算": "1 小时",
                    "学习风格偏好": "视频 + 动手练习",
                    "压力承受自评（1–5）": 3,
                    "期望节奏": "平缓",
                    "过往经历": "无编程经验",
                    "复习意愿": "愿意每天 10 分钟",
                },
            },
        )
        profile.run(inp, self._out("onboard-empty-out.json"))
        text = self._read_file(PROFILE_OUT / "onboard-empty.md")
        self.assertNotIn("<!--", text)
        self.assertIn("## 增量记录\n- 2026-08-19：onboarding 问卷 → 画像初值\n", text)
        self.assertIn(MATRIX_HEAD, text)

    def test_onboarding_clamps_numeric_self_assessments(self):
        # 两项 1–5 自评超出范围自动截断：7 → 5，-1 → 1
        result, _ = self._run("onboard-clamp.json", "onboard-clamp-out.json")
        self.assertEqual(result["answers"]["Python 水平自评（1–5）"], "5")
        self.assertEqual(result["answers"]["压力承受自评（1–5）"], "1")
        text = self._read_file(PROFILE_OUT / "onboard-clamp.md")
        self.assertIn("- Python 水平自评（1–5）：5\n", text)
        self.assertIn("- 压力承受自评（1–5）：1\n", text)

    def test_onboarding_missing_field_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "onboard-missing-field.json",
                self._out("onboard-missing-out.json"),
            )

    def test_onboarding_extra_field_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "onboard-extra-field.json", self._out("onboard-extra-out.json")
            )

    def test_onboarding_bad_numeric_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "onboard-bad-numeric.json", self._out("onboard-num-out.json")
            )

    def test_onboarding_empty_value_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "onboard-empty-value.json", self._out("onboard-val-out.json")
            )

    def test_onboarding_answers_not_object_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "onboard-not-object.json", self._out("onboard-obj-out.json")
            )


class AcceptanceTest(_ProfileTest):
    """op=acceptance：验收完成度写回能力矩阵，难度反馈独立记录。"""

    def test_acceptance_high_score_increments_half(self):
        # basic.md 副本：完成度 4 ≥ 4 → pandas.Series 1.5→2，难度「刚好」入日志
        self._copy_profile("basic.md", "acc-up.md")
        result, out = self._run("acc-up.json", "acc-up-out.json")
        self.assertEqual(result["op"], "acceptance")
        self.assertEqual(result["topic"], "pandas.Series")
        self.assertEqual(result["score"], 4.0)
        self.assertEqual(result["difficulty"], "刚好")
        self.assertEqual(result["source"], "验收 Day 1")
        self.assertEqual(result["old_score"], 1.5)
        self.assertEqual(result["new_score"], 2.0)
        self.assertEqual(result["delta"], 0.5)
        self.assertTrue(result["updated"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：验收 Day 1（完成度 4，难度 刚好）→ pandas.Series +0.5（1.5→2）",
        )
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)
        # 写盘原文：矩阵行更新（时间/来源）、未涉及行不动、日志追加、问卷保留
        self.assertEqual(
            self._read_file(PROFILE_OUT / "acc-up.md"),
            "---\n"
            "created: 2026-08-19\n"
            "updated: 2026-08-21\n"
            "---\n"
            "\n"
            "# 用户画像\n"
            "\n"
            + ONBOARDING_BASIC
            + "\n"
            "\n"
            + MATRIX_HEAD
            + "| 数据分析 | pandas | pandas.Series | 知识点 | 2 | — | 2026-08-21 | 验收 Day 1 |\n"
            + "| 数据分析 | pandas | pandas.DataFrame | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |\n"
            + "\n"
            + "## 增量记录\n"
            + "- 2026-08-20：摸底测试 → 初始矩阵\n"
            + "- 2026-08-21：验收 Day 1（完成度 4，难度 刚好）→ pandas.Series +0.5（1.5→2）\n",
        )

    def test_acceptance_without_difficulty(self):
        # 未提供难度反馈 → 日志不含难度段；4.5 同样触发 +0.5
        self._copy_profile("basic.md", "acc-up-no-diff.md")
        result, _ = self._run("acc-up-no-diff.json", "acc-up-no-diff-out.json")
        self.assertIsNone(result["difficulty"])
        self.assertEqual(result["score"], 4.5)
        self.assertEqual(result["new_score"], 2.0)
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：验收 Day 1（完成度 4.5）→ pandas.Series +0.5（1.5→2）",
        )

    def test_acceptance_low_score_no_change(self):
        # 完成度 2 < 4 → 矩阵不变（日志记录事件与难度），原行时间/来源保持
        self._copy_profile("basic.md", "acc-low.md")
        result, _ = self._run("acc-low.json", "acc-low-out.json")
        self.assertEqual(result["old_score"], 1.5)
        self.assertEqual(result["new_score"], 1.5)
        self.assertEqual(result["delta"], 0.0)
        self.assertFalse(result["updated"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：验收 Day 1（完成度 2，难度 太难）→ pandas.Series 矩阵不变",
        )
        text = self._read_file(PROFILE_OUT / "acc-low.md")
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 1.5 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertIn("- 2026-08-21：验收 Day 1（完成度 2，难度 太难）→ pandas.Series 矩阵不变\n", text)

    def test_acceptance_caps_at_five(self):
        # cap.md 副本：Series 已 5 分，再验收高分 → 保持 5（updated=false）
        self._copy_profile("cap.md", "acc-cap.md")
        result, _ = self._run("acc-cap.json", "acc-cap-out.json")
        self.assertEqual(result["old_score"], 5.0)
        self.assertEqual(result["new_score"], 5.0)
        self.assertFalse(result["updated"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-22：验收 Day 2（完成度 5，难度 刚好）→ pandas.Series 矩阵不变",
        )

    def test_acceptance_default_source(self):
        # 未提供 source → 默认「验收」
        self._copy_profile("basic.md", "acc-no-source.md")
        result, _ = self._run("acc-no-source.json", "acc-no-source-out.json")
        self.assertEqual(result["source"], "验收")
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 2 | — | 2026-08-21 | 验收 |",
            self._read_file(PROFILE_OUT / "acc-no-source.md"),
        )

    def test_acceptance_writes_frontmatter_when_missing(self):
        # 无 frontmatter 的画像：写回时补 created/updated
        self._copy_profile("no-frontmatter.md", "acc-nofm.md")
        inp = self._write_input(
            "acc-nofm.json",
            {
                "date": "2026-08-21",
                "profile_path": "../profile/acc-nofm.md",
                "op": "acceptance",
                "topic": "pandas.Series",
                "score": 4,
                "source": "验收 Day 1",
            },
        )
        profile.run(inp, self._out("acc-nofm-out.json"))
        self.assertTrue(
            self._read_file(PROFILE_OUT / "acc-nofm.md").startswith(
                "---\ncreated: 2026-08-21\nupdated: 2026-08-21\n---\n"
            )
        )

    def test_acceptance_skips_malformed_rows(self):
        # dirty.md 副本：无法解析的「坏行」被跳过，其余行正常更新并写回
        self._copy_profile("dirty.md", "acc-dirty.md")
        inp = self._write_input(
            "acc-dirty.json",
            {
                "date": "2026-08-21",
                "profile_path": "../profile/acc-dirty.md",
                "op": "acceptance",
                "topic": "pandas.Series",
                "score": 4,
                "source": "验收 Day 1",
            },
        )
        profile.run(inp, self._out("acc-dirty-out.json"))
        text = self._read_file(PROFILE_OUT / "acc-dirty.md")
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 2.5 | — | 2026-08-21 | 验收 Day 1 |",
            text,
        )
        self.assertIn(
            "| 数据分析 | pandas | pandas.DataFrame | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertNotIn("坏行", text)

    def test_acceptance_preserves_missing_onboarding_as_placeholder(self):
        # no-onboarding.md 副本：无问卷区块时写回补空占位（结构完整）
        self._copy_profile("no-onboarding.md", "acc-noonb.md")
        inp = self._write_input(
            "acc-noonb.json",
            {
                "date": "2026-08-21",
                "profile_path": "../profile/acc-noonb.md",
                "op": "acceptance",
                "topic": "pandas.Series",
                "score": 4,
                "source": "验收 Day 1",
            },
        )
        profile.run(inp, self._out("acc-noonb-out.json"))
        text = self._read_file(PROFILE_OUT / "acc-noonb.md")
        self.assertIn("## Onboarding 问卷（8 题）\n- 学习目标：\n", text)
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 2.5 | — | 2026-08-21 | 验收 Day 1 |",
            text,
        )

    def test_acceptance_missing_topic_raises(self):
        self._copy_profile("basic.md", "acc-missing.md")
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "acc-missing-topic.json", self._out("acc-missing-out.json")
            )

    def test_acceptance_bad_score_raises(self):
        self._copy_profile("basic.md", "acc-bad.md")
        with self.assertRaises(ValueError):
            profile.run(INPUTS / "acc-bad-score.json", self._out("acc-badscore-out.json"))

    def test_acceptance_missing_score_raises(self):
        self._copy_profile("basic.md", "acc-noscore.md")
        with self.assertRaises(ValueError):
            profile.run(INPUTS / "acc-no-score.json", self._out("acc-noscore-out.json"))

    def test_acceptance_bad_difficulty_raises(self):
        self._copy_profile("basic.md", "acc-baddiff.md")
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "acc-bad-difficulty.json", self._out("acc-baddiff-out.json")
            )

    def test_acceptance_bad_topic_raises(self):
        self._copy_profile("basic.md", "acc-badtopic.md")
        with self.assertRaises(ValueError):
            profile.run(INPUTS / "acc-bad-topic.json", self._out("acc-badtopic-out.json"))

    def test_acceptance_on_capability_row_raises(self):
        # 能力行无水平分（前置状态二值）→ 不接受验收增量
        self._copy_profile("capability.md", "acc-caprow.md")
        inp = self._write_input(
            "acc-caprow.json",
            {
                "date": "2026-08-21",
                "profile_path": "../profile/acc-caprow.md",
                "op": "acceptance",
                "topic": "Python 工程组织",
                "score": 4,
                "source": "验收 Day 1",
            },
        )
        with self.assertRaises(ValueError):
            profile.run(inp, self._out("acc-caprow-out.json"))

    def test_legacy_four_column_matrix_tolerated(self):
        # 旧 4 列画像（无 领域/子领域/类型/前置状态）解析容错：
        # 视作知识点行（前置状态 = —），验收增量写回后仍按新 8 列 schema 落盘
        self._copy_profile("legacy.md", "acc-legacy.md")
        inp = self._write_input(
            "acc-legacy.json",
            {
                "date": "2026-08-21",
                "profile_path": "../profile/acc-legacy.md",
                "op": "acceptance",
                "topic": "pandas.Series",
                "score": 4,
                "source": "验收 Day 1",
            },
        )
        profile.run(inp, self._out("acc-legacy-out.json"))
        text = self._read_file(PROFILE_OUT / "acc-legacy.md")
        self.assertIn(
            "|  |  | pandas.Series | 知识点 | 2.5 | — | 2026-08-21 | 验收 Day 1 |",
            text,
        )
        self.assertIn(
            "|  |  | pandas.DataFrame | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |",
            text,
        )


class ReviewTest(_ProfileTest):
    """op=review：复习考察得分写回能力矩阵（与调度表同一规则）。"""

    def test_review_pass_increments(self):
        self._copy_profile("basic.md", "rev-pass.md")
        result, _ = self._run("rev-pass.json", "rev-pass-out.json")
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["source"], "复习考察")
        self.assertEqual(result["old_score"], 1.5)
        self.assertEqual(result["new_score"], 2.0)
        self.assertEqual(result["delta"], 0.5)
        self.assertTrue(result["updated"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：复习考察（通过）→ pandas.Series +0.5（1.5→2）",
        )
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 2 | — | 2026-08-21 | 复习考察 |",
            self._read_file(PROFILE_OUT / "rev-pass.md"),
        )

    def test_review_fail_decrements(self):
        self._copy_profile("basic.md", "rev-fail.md")
        result, _ = self._run("rev-fail.json", "rev-fail-out.json")
        self.assertEqual(result["old_score"], 1.5)
        self.assertEqual(result["new_score"], 1.0)
        self.assertEqual(result["delta"], -0.5)
        self.assertTrue(result["updated"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：复习考察（未通过）→ pandas.Series -0.5（1.5→1）",
        )

    def test_review_fail_floors_at_one(self):
        # floor.md 副本：Series 已 1 分，未通过 → 保持 1（updated=false）
        self._copy_profile("floor.md", "rev-floor.md")
        result, _ = self._run("rev-floor.json", "rev-floor-out.json")
        self.assertEqual(result["old_score"], 1.0)
        self.assertEqual(result["new_score"], 1.0)
        self.assertFalse(result["updated"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：复习考察（未通过）→ pandas.Series 矩阵不变",
        )

    def test_review_bad_result_raises(self):
        self._copy_profile("basic.md", "rev-bad.md")
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "rev-bad-result.json", self._out("rev-bad-out.json")
            )

    def test_review_missing_topic_raises(self):
        self._copy_profile("basic.md", "rev-missing.md")
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "rev-missing-topic.json", self._out("rev-missing-out.json")
            )


class NewTopicChannelTest(_ProfileTest):
    """批次 4 显式新增通道：acceptance/review 的矩阵外 topic 经 add_new 放行新建行。"""

    def _new_input(self, name, data):
        return self._write_input(name, {"date": "2026-08-21", **data})

    def test_acceptance_add_new_knowledge_row(self):
        # 矩阵外知识点 + add_new → 新建知识点行：初值 = 完成度（0.5 档截断），
        # 来源「验收新增 Day 3」；原有行与问卷保留、日志追加
        self._copy_profile("basic.md", "acc-new.md")
        inp = self._new_input(
            "acc-new.json",
            {
                "profile_path": "../profile/acc-new.md",
                "op": "acceptance",
                "topic": "pandas.merge",
                "score": 4,
                "difficulty": "刚好",
                "source": "验收新增 Day 3",
                "add_new": True,
                "domain": "数据分析",
                "subdomain": "pandas",
            },
        )
        result = profile.run(inp, self._out("acc-new-out.json"))
        self.assertTrue(result["added"])
        self.assertEqual(result["old_score"], None)
        self.assertEqual(result["new_score"], 4.0)
        self.assertEqual(result["delta"], None)
        self.assertTrue(result["updated"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：验收新增 Day 3（完成度 4，难度 刚好）→ 新增知识点 pandas.merge（水平 4）",
        )
        text = self._read_file(PROFILE_OUT / "acc-new.md")
        self.assertIn(
            "| 数据分析 | pandas | pandas.merge | 知识点 | 4 | — | 2026-08-21 | 验收新增 Day 3 |",
            text,
        )
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 1.5 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertTrue(
            text.endswith(
                "## 增量记录\n"
                "- 2026-08-20：摸底测试 → 初始矩阵\n"
                "- 2026-08-21：验收新增 Day 3（完成度 4，难度 刚好）→ 新增知识点 pandas.merge（水平 4）\n"
            )
        )

    def test_acceptance_add_new_low_score_still_creates_row(self):
        # 完成度 2 < 4：既有行不变，但新增行照常创建（初值 = 完成度 2）
        self._copy_profile("basic.md", "acc-new-low.md")
        inp = self._new_input(
            "acc-new-low.json",
            {
                "profile_path": "../profile/acc-new-low.md",
                "op": "acceptance",
                "topic": "pandas.merge",
                "score": 2,
                "source": "验收新增 Day 3",
                "add_new": True,
            },
        )
        result = profile.run(inp, self._out("acc-new-low-out.json"))
        self.assertTrue(result["added"])
        self.assertEqual(result["new_score"], 2.0)
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：验收新增 Day 3（完成度 2）→ 新增知识点 pandas.merge（水平 2）",
        )

    def test_acceptance_add_new_ability_row(self):
        # 类型 = 能力 → 新建能力行：水平分 = —、前置状态二值（pre_status 必填）；
        # score 仍为当日完成度（记录进日志详情），不写入矩阵数值
        self._copy_profile("basic.md", "acc-new-ability.md")
        inp = self._new_input(
            "acc-new-ability.json",
            {
                "profile_path": "../profile/acc-new-ability.md",
                "op": "acceptance",
                "topic": "数据工程组织",
                "type": "能力",
                "pre_status": "未具备",
                "score": 4,
                "source": "验收新增 Day 3",
                "add_new": True,
            },
        )
        result = profile.run(inp, self._out("acc-new-ability-out.json"))
        self.assertTrue(result["added"])
        self.assertIsNone(result["new_score"])
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：验收新增 Day 3（完成度 4）→ 新增能力 数据工程组织（前置状态 未具备）",
        )
        text = self._read_file(PROFILE_OUT / "acc-new-ability.md")
        self.assertIn(
            "|  |  | 数据工程组织 | 能力 | — | 未具备 | 2026-08-21 | 验收新增 Day 3 |",
            text,
        )

    def test_acceptance_add_new_requires_flag(self):
        # 未带 add_new → 维持原行为：矩阵外 topic 报错
        self._copy_profile("basic.md", "acc-new-noflag.md")
        inp = self._new_input(
            "acc-new-noflag.json",
            {
                "profile_path": "../profile/acc-new-noflag.md",
                "op": "acceptance",
                "topic": "pandas.merge",
                "score": 4,
            },
        )
        with self.assertRaises(ValueError):
            profile.run(inp, self._out("acc-new-noflag-out.json"))

    def test_acceptance_add_new_bad_type_raises(self):
        self._copy_profile("basic.md", "acc-new-badtype.md")
        inp = self._new_input(
            "acc-new-badtype.json",
            {
                "profile_path": "../profile/acc-new-badtype.md",
                "op": "acceptance",
                "topic": "pandas.merge",
                "score": 4,
                "type": "技能",
                "add_new": True,
            },
        )
        with self.assertRaises(ValueError):
            profile.run(inp, self._out("acc-new-badtype-out.json"))

    def test_acceptance_add_new_ability_missing_pre_status_raises(self):
        # 能力行缺 pre_status → 报错（不能写半成品能力行）
        self._copy_profile("basic.md", "acc-new-nostatus.md")
        inp = self._new_input(
            "acc-new-nostatus.json",
            {
                "profile_path": "../profile/acc-new-nostatus.md",
                "op": "acceptance",
                "topic": "数据工程组织",
                "type": "能力",
                "add_new": True,
            },
        )
        with self.assertRaises(ValueError):
            profile.run(inp, self._out("acc-new-nostatus-out.json"))

    def test_add_new_ignored_for_existing_topic(self):
        # 矩阵内 topic 带 add_new → 走正常增量路径（新增通道只对矩阵外生效）
        self._copy_profile("basic.md", "acc-new-existing.md")
        inp = self._new_input(
            "acc-new-existing.json",
            {
                "profile_path": "../profile/acc-new-existing.md",
                "op": "acceptance",
                "topic": "pandas.Series",
                "score": 4,
                "source": "验收 Day 1",
                "add_new": True,
            },
        )
        result = profile.run(inp, self._out("acc-new-existing-out.json"))
        self.assertNotIn("added", result)
        self.assertEqual(result["old_score"], 1.5)
        self.assertEqual(result["new_score"], 2.0)
        self.assertEqual(result["delta"], 0.5)

    def test_review_add_new_pass_creates_row(self):
        # 复习新增：通过 → 初值 2.0（与 schedule.py add 默认掌握度一致）
        self._copy_profile("basic.md", "rev-new-pass.md")
        inp = self._new_input(
            "rev-new-pass.json",
            {
                "profile_path": "../profile/rev-new-pass.md",
                "op": "review",
                "topic": "pandas.merge",
                "result": "pass",
                "source": "复习新增",
                "add_new": True,
            },
        )
        result = profile.run(inp, self._out("rev-new-pass-out.json"))
        self.assertTrue(result["added"])
        self.assertEqual(result["new_score"], 2.0)
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：复习新增（通过）→ 新增知识点 pandas.merge（水平 2）",
        )
        self.assertIn(
            "|  |  | pandas.merge | 知识点 | 2 | — | 2026-08-21 | 复习新增 |",
            self._read_file(PROFILE_OUT / "rev-new-pass.md"),
        )

    def test_review_add_new_fail_creates_row(self):
        # 复习新增：未通过 → 初值 1.0（下限）
        self._copy_profile("basic.md", "rev-new-fail.md")
        inp = self._new_input(
            "rev-new-fail.json",
            {
                "profile_path": "../profile/rev-new-fail.md",
                "op": "review",
                "topic": "pandas.merge",
                "result": "fail",
                "source": "复习新增",
                "add_new": True,
            },
        )
        result = profile.run(inp, self._out("rev-new-fail-out.json"))
        self.assertTrue(result["added"])
        self.assertEqual(result["new_score"], 1.0)
        self.assertEqual(
            result["log_entry"],
            "- 2026-08-21：复习新增（未通过）→ 新增知识点 pandas.merge（水平 1）",
        )

    def test_review_add_new_requires_flag(self):
        self._copy_profile("basic.md", "rev-new-noflag.md")
        inp = self._new_input(
            "rev-new-noflag.json",
            {
                "profile_path": "../profile/rev-new-noflag.md",
                "op": "review",
                "topic": "pandas.merge",
                "result": "pass",
            },
        )
        with self.assertRaises(ValueError):
            profile.run(inp, self._out("rev-new-noflag-out.json"))


class PlacementTest(_ProfileTest):
    """op=placement：摸底测试结果初始化能力矩阵。"""

    def test_placement_creates_profile_and_matrix(self):
        # 画像尚不存在 → placement 创建画像：初始矩阵行（来源「摸底测试」）+ 日志一条
        result, out = self._run("placement-first.json", "placement-first-out.json")
        self.assertEqual(result["op"], "placement")
        self.assertEqual(result["date"], "2026-08-20")
        self.assertEqual(result["count"], 4)
        self.assertEqual(
            result["matrix"][0],
            {
                "topic": "变量与数据类型",
                "type": "知识点",
                "score": 1.5,
                "pre_status": "—",
                "domain": "",
                "subdomain": "",
                "date": "2026-08-20",
                "source": "摸底测试",
            },
        )
        self.assertEqual(result["log_entry"], "- 2026-08-20：摸底测试 → 初始矩阵")
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)
        # 写盘原文：4 行矩阵、空问卷占位、日志一条、frontmatter 补齐
        text = self._read_file(PROFILE_OUT / "placement-first.md")
        self.assertTrue(
            text.startswith("---\ncreated: 2026-08-20\nupdated: 2026-08-20\n---\n")
        )
        self.assertIn("## Onboarding 问卷（8 题）\n- 学习目标：\n", text)
        self.assertIn(
            MATRIX_HEAD
            + "|  |  | 变量与数据类型 | 知识点 | 1.5 | — | 2026-08-20 | 摸底测试 |\n"
            + "|  |  | 条件与循环 | 知识点 | 1 | — | 2026-08-20 | 摸底测试 |\n"
            + "|  |  | pandas.Series | 知识点 | 1.5 | — | 2026-08-20 | 摸底测试 |\n"
            + "|  |  | 数据读取与筛选 | 知识点 | 2.5 | — | 2026-08-20 | 摸底测试 |\n",
            text,
        )
        self.assertTrue(
            text.endswith("## 增量记录\n- 2026-08-20：摸底测试 → 初始矩阵\n")
        )


    def test_placement_upserts_existing_rows(self):
        # basic.md 副本：results 内知识点行按新值覆盖（来源改「摸底测试」、日期更新），
        # 其余行保留，问卷保留，日志追加一条
        self._copy_profile("basic.md", "placement-up.md")
        result, _ = self._run("placement-up.json", "placement-up-out.json")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["matrix"][0]["score"], 2.5)
        self.assertEqual(result["matrix"][1]["score"], 3.0)
        text = self._read_file(PROFILE_OUT / "placement-up.md")
        self.assertIn("- 学习目标：用 Python 做数据分析\n", text)
        # placement 行整体覆盖：输入未带领域/子领域 → 新行为空（来源/日期更新）
        self.assertIn(
            "|  |  | pandas.Series | 知识点 | 2.5 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertIn(
            "|  |  | pandas.DataFrame | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertTrue(
            text.endswith(
                "## 增量记录\n"
                "- 2026-08-20：摸底测试 → 初始矩阵\n"
                "- 2026-08-20：摸底测试 → 初始矩阵\n"
            )
        )
        self.assertIn("updated: 2026-08-20", text)

    def test_placement_rounds_and_clamps(self):
        # 水平分兜底规范化：0.2 → 1（下限截断）、5.3 → 5（上限截断）、
        # 2.75 → 3（半向上）、2.25 → 2.5
        result, _ = self._run("placement-clamp.json", "placement-clamp-out.json")
        by_topic = {row["topic"]: row["score"] for row in result["matrix"]}
        self.assertEqual(by_topic["变量与数据类型"], 1.0)
        self.assertEqual(by_topic["pandas.Series"], 5.0)
        self.assertEqual(by_topic["函数"], 3.0)
        self.assertEqual(by_topic["Excel 读写"], 2.5)
        text = self._read_file(PROFILE_OUT / "placement-clamp.md")
        self.assertIn("|  |  | 变量与数据类型 | 知识点 | 1 | — | 2026-08-20 | 摸底测试 |", text)
        self.assertIn("|  |  | pandas.Series | 知识点 | 5 | — | 2026-08-20 | 摸底测试 |", text)
        self.assertIn("|  |  | 函数 | 知识点 | 3 | — | 2026-08-20 | 摸底测试 |", text)
        self.assertIn("|  |  | Excel 读写 | 知识点 | 2.5 | — | 2026-08-20 | 摸底测试 |", text)

    def test_placement_duplicate_topic_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-dup.json", self._out("placement-dup-out.json")
            )

    def test_placement_no_results_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-no-results.json",
                self._out("placement-nores-out.json"),
            )

    def test_placement_empty_results_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-empty-results.json",
                self._out("placement-empty-out.json"),
            )

    def test_placement_not_list_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-not-list.json",
                self._out("placement-notlist-out.json"),
            )

    def test_placement_bad_element_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-bad-element.json",
                self._out("placement-badelem-out.json"),
            )

    def test_placement_missing_topic_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-bad-topic.json",
                self._out("placement-badtopic-out.json"),
            )

    def test_placement_bad_score_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-bad-score.json",
                self._out("placement-badscore-out.json"),
            )

    def test_placement_with_capability_rows(self):
        # 能力行（type=能力 + pre_status）与知识点行（可带领域/子领域）混合写入；
        # 能力行水平分 = —、前置状态二值；知识点行前置状态 = —
        result, _ = self._run("placement-cap.json", "placement-cap-out.json")
        self.assertEqual(result["count"], 3)
        by_topic = {row["topic"]: row for row in result["matrix"]}
        self.assertEqual(
            by_topic["pandas.Series"],
            {
                "topic": "pandas.Series",
                "type": "知识点",
                "score": 1.5,
                "pre_status": "—",
                "domain": "数据分析",
                "subdomain": "pandas",
                "date": "2026-08-20",
                "source": "摸底测试",
            },
        )
        self.assertEqual(
            by_topic["Python 工程组织"],
            {
                "topic": "Python 工程组织",
                "type": "能力",
                "score": None,
                "pre_status": "未具备",
                "domain": "工程",
                "subdomain": "工程素养",
                "date": "2026-08-20",
                "source": "摸底测试",
            },
        )
        text = self._read_file(PROFILE_OUT / "placement-cap.md")
        self.assertIn(
            "| 数据分析 | pandas | pandas.Series | 知识点 | 1.5 | — | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertIn(
            "| 工程 | 工程素养 | Python 工程组织 | 能力 | — | 未具备 | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertIn(
            "| 编程基础 | 面向对象 | OOP 类与对象 | 知识点 | 2 | — | 2026-08-20 | 摸底测试 |",
            text,
        )

    def test_placement_capability_missing_pre_status_raises(self):
        # 能力行缺 pre_status → 报错（不能写半成品能力行）
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-cap-bad-status.json",
                self._out("placement-capbad-out.json"),
            )

    def test_placement_capability_with_score_raises(self):
        # 能力行带 score → 报错（前置状态二值，无水平分）
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-cap-with-score.json",
                self._out("placement-capscore-out.json"),
            )

    def test_placement_bad_type_raises(self):
        # type 不是 知识点|能力 → 报错
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "placement-bad-type.json",
                self._out("placement-badtype-out.json"),
            )

    def test_placement_preserves_capability_row_on_upsert(self):
        # capability.md 副本：只 upsert 知识点行，能力行保持不动
        self._copy_profile("capability.md", "placement-cap-up.md")
        inp = self._write_input(
            "placement-cap-up.json",
            {
                "date": "2026-08-20",
                "profile_path": "../profile/placement-cap-up.md",
                "op": "placement",
                "results": [
                    {"topic": "pandas.Series", "score": 2.5},
                ],
            },
        )
        profile.run(inp, self._out("placement-cap-up-out.json"))
        text = self._read_file(PROFILE_OUT / "placement-cap-up.md")
        self.assertIn(
            "| 工程 | 工程素养 | Python 工程组织 | 能力 | — | 未具备 | 2026-08-20 | 摸底测试 |",
            text,
        )
        self.assertIn(
            "|  |  | pandas.Series | 知识点 | 2.5 | — | 2026-08-20 | 摸底测试 |",
            text,
        )


class ErrorTest(_ProfileTest):
    """输入错误处理。"""

    def test_bad_op_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "profile-bad-op.json", self._out("bad-op-out.json")
            )

    def test_bad_date_raises(self):
        with self.assertRaises(ValueError):
            profile.run(
                INPUTS / "profile-bad-date.json", self._out("bad-date-out.json")
            )

    def test_acceptance_missing_profile_raises(self):
        # 画像文件不存在且 op=acceptance → 报错（不能凭空更新矩阵）
        inp = self._write_input(
            "acc-missing-file.json",
            {
                "date": "2026-08-21",
                "profile_path": "../profile/never-created.md",
                "op": "acceptance",
                "topic": "pandas.Series",
                "score": 4,
            },
        )
        with self.assertRaises(FileNotFoundError):
            profile.run(inp, self._out("acc-missing-file-out.json"))

    def test_non_object_input_raises(self):
        with self.assertRaises(ValueError):
            profile.run(INPUTS / "not-object.json", self._out("not-object-out.json"))

    def test_missing_input_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            profile.run(INPUTS / "不存在.json", self._out("nope-out.json"))


class CliTest(_ProfileTest):
    """命令行入口 main()。"""

    def test_main_writes_output(self):
        self._copy_profile("basic.md", "acc-up.md")
        out = self._out("cli-acc-out.json")
        code = profile.main([str(INPUTS / "acc-up.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(
            json.loads(out.read_text(encoding="utf-8"))["new_score"], 2.0
        )

    def test_main_placement_writes_output(self):
        out = self._out("cli-placement-out.json")
        code = profile.main(
            [str(INPUTS / "placement-first.json"), str(out)]
        )
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(
            json.loads(out.read_text(encoding="utf-8"))["count"], 4
        )

    def test_main_wrong_arg_count_returns_2(self):
        self.assertEqual(profile.main([]), 2)
        self.assertEqual(profile.main(["只有输入.json"]), 2)

    def test_main_missing_input_returns_1(self):
        out = self._out("cli-missing-out.json")
        self.assertEqual(profile.main([str(INPUTS / "不存在.json"), str(out)]), 1)
        self.assertFalse(out.exists())

    def test_main_bad_op_returns_1(self):
        out = self._out("cli-bad-op-out.json")
        self.assertEqual(
            profile.main([str(INPUTS / "profile-bad-op.json"), str(out)]), 1
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
