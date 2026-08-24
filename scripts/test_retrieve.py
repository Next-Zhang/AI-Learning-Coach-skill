#!/usr/bin/env python3
"""检索层（ticket 02）测试——以样例输入文件驱动脚本，断言输出文件内容。

遵循 spec「测试 seam」与「Testing Decisions」：唯一 seam 是 scripts/ 纯函数，
测试形态为「读输入文件 → 写输出文件」契约，只测外部行为、不测实现细节。
因此本套测试全部经 run()/main() 走文件契约，不断言引擎相关细节（如精确分值）。

契约与用法见 ../resources/retrieval-contract.md。
运行：python scripts/test_retrieve.py
注意：沙箱下 tempfile 不可写，测试全部使用静态夹具（testdata/）与
固定输出目录（testdata/_out/）。
"""
import json
import sys

sys.dont_write_bytecode = True  # 运行期不写 __pycache__（等价 PYTHONDONTWRITEBYTECODE=1）
import unittest
from pathlib import Path

# 让测试直接 import 同目录的 retrieve 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

import retrieve

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
        result = retrieve.run(INPUTS / input_name, out)
        self.assertTrue(out.exists())
        return result, out

    # --- 关键词检索行为 ---

    def test_basic_query_returns_matching_source(self):
        result, out = self._run("basic.json", "basic-out.json")
        self.assertEqual(result["query"], "groupby")
        self.assertEqual(len(result["results"]), 1)
        r0 = result["results"][0]
        self.assertEqual(r0["title"], "pandas groupby 分组聚合")
        self.assertEqual(r0["origin"], "local")
        self.assertTrue(r0["link"].endswith("pandas-groupby.md"))
        # 输出文件内容与返回值一致
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)

    def test_ranked_order_and_exclusion(self):
        # "pandas"：三份 pandas 资料按相关度排序，无关资料（python-basics）不出现
        result, _ = self._run("ranked.json", "ranked-out.json")
        titles = [r["title"] for r in result["results"]]
        self.assertEqual(
            titles,
            ["pandas Series 基础", "pandas groupby 分组聚合", "数据分析小技巧"],
        )
        self.assertNotIn("Python 基础语法速览", titles)

    def test_chinese_query(self):
        result, _ = self._run("chinese.json", "chinese-out.json")
        self.assertEqual([r["title"] for r in result["results"]],
                         ["pandas groupby 分组聚合"])

    def test_limit_from_input(self):
        result, _ = self._run("limit.json", "limit-out.json")
        self.assertEqual(len(result["results"]), 2)

    def test_no_match_returns_empty_results(self):
        result, _ = self._run("empty.json", "empty-out.json")
        self.assertEqual(result["results"], [])

    def test_every_result_carries_required_fields(self):
        # 契约四必需字段（标题/来源/摘要/链接）每条结果都必须非空
        result, _ = self._run("web.json", "fields-out.json")
        self.assertEqual(len(result["results"]), 4)
        for r in result["results"]:
            for field in ("title", "source", "summary", "link"):
                self.assertTrue(r[field], f"{field} 为空: {r}")

    # --- web 检索补充 ---

    def test_web_results_merged_after_local_and_deduped(self):
        # web.json：3 条本地 + 1 条 web（与本地同 URL 的重复项被去重）
        result, _ = self._run("web.json", "web-out.json")
        self.assertEqual([r["origin"] for r in result["results"]],
                         ["local", "local", "local", "web"])
        last = result["results"][3]
        self.assertEqual(last["title"], "Pandas Documentation")
        # web 结果无本地文件，link 即来源 URL
        self.assertEqual(last["link"], last["source"])

    def test_web_only_results_when_local_empty(self):
        # 本地无结果时仅靠 web 补充；web 内部同 URL 去重
        result, _ = self._run("web-only.json", "web-only-out.json")
        self.assertEqual(len(result["results"]), 1)
        r0 = result["results"][0]
        self.assertEqual(r0["origin"], "web")
        self.assertEqual(r0["link"], r0["source"])
        self.assertEqual(r0["title"], "量子计算入门")

    # --- frontmatter 解析（经契约暴露的行为） ---

    def test_quoted_topics_parsed_through_contract(self):
        # 引号/空格主题标签正确解析，并出现在结果 topics 字段
        result, _ = self._run("parse-quoted.json", "parse-quoted-out.json")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["topics"],
                         ["pandas", "groupby", "聚合"])

    def test_body_only_source_matches_and_defaults(self):
        # 无 frontmatter 的资料按正文匹配，缺省字段为空
        result, _ = self._run("parse-plain.json", "parse-plain-out.json")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["title"], "")

    def test_sparse_frontmatter_fields_defaulted(self):
        # 仅 title 的 frontmatter：其余字段输出为空/空列表
        result, _ = self._run("parse-sparse.json", "parse-sparse-out.json")
        self.assertEqual(len(result["results"]), 1)
        r0 = result["results"][0]
        self.assertEqual(r0["title"], "缺字段")
        self.assertEqual(r0["source"], "")
        self.assertEqual(r0["topics"], [])

    # --- 错误处理 ---

    def test_missing_query_raises(self):
        with self.assertRaises(ValueError):
            retrieve.run(INPUTS / "bad-no-query.json", self._out("bad-out.json"))

    def test_missing_sources_dir_raises(self):
        with self.assertRaises(FileNotFoundError):
            retrieve.run(INPUTS / "bad-sources-dir.json", self._out("bad-dir-out.json"))

    def test_missing_input_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            retrieve.run(INPUTS / "不存在.json", self._out("nope-out.json"))


class CliTest(_OutDirTest):
    """命令行入口 main()。"""

    def test_main_writes_output(self):
        out = self._out("cli-out.json")
        code = retrieve.main([str(INPUTS / "basic.json"), str(out)])
        self.assertEqual(code, 0)
        self.assertTrue(out.exists())
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["query"],
                         "groupby")

    def test_main_wrong_arg_count_returns_2(self):
        self.assertEqual(retrieve.main([]), 2)
        self.assertEqual(retrieve.main(["只有输入.json"]), 2)

    def test_main_missing_input_returns_1(self):
        out = self._out("cli-missing.json")
        self.assertEqual(
            retrieve.main([str(INPUTS / "不存在.json"), str(out)]), 1
        )
        self.assertFalse(out.exists())

    def test_main_bad_sources_dir_returns_1(self):
        out = self._out("cli-bad-dir.json")
        self.assertEqual(
            retrieve.main([str(INPUTS / "bad-sources-dir.json"), str(out)]), 1
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
