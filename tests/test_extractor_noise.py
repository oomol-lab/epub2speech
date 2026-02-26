#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

EXTRACTOR_PATH = Path(__file__).parent.parent / "epub2speech" / "extractor.py"
SPEC = importlib.util.spec_from_file_location("extractor_module_for_test", EXTRACTOR_PATH)
assert SPEC and SPEC.loader
extractor_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor_module)

extract_text_from_html = extractor_module.extract_text_from_html
extract_text_from_html_with_report = extractor_module.extract_text_from_html_with_report


class TestExtractorNoiseCleaning(unittest.TestCase):
    def test_removes_toc_entries_and_decorations(self):
        html = """
        <html><body>
          <h1>目录</h1>
          <p>第一章 童年 ........ 12</p>
          <p>Chapter II ____ 21</p>
          <p>___________</p>
          <p>这里是正文。</p>
        </body></html>
        """

        text = extract_text_from_html(html)

        self.assertNotIn("目录", text)
        self.assertNotIn("第一章 童年", text)
        self.assertNotIn("Chapter II", text)
        self.assertIn("这里是正文。", text)

    def test_keeps_regular_chapter_title(self):
        html = """
        <html><body>
          <h1>Chapter I</h1>
          <p>This is the real content of the chapter.</p>
        </body></html>
        """

        text = extract_text_from_html(html)

        self.assertIn("Chapter I", text)
        self.assertIn("This is the real content of the chapter.", text)

    def test_drops_pure_page_number_line(self):
        html = """
        <html><body>
          <p>42</p>
          <p>真正内容在这里。</p>
        </body></html>
        """

        text = extract_text_from_html(html)

        self.assertNotIn("42", text)
        self.assertIn("真正内容在这里。", text)

    def test_strictness_controls_short_block_behavior(self):
        html = """
        <html><body>
          <p>Quick recap</p>
        </body></html>
        """

        conservative = extract_text_from_html(html, cleaning_strictness="conservative")
        aggressive = extract_text_from_html(html, cleaning_strictness="aggressive")

        self.assertIn("Quick recap", conservative)
        self.assertEqual("", aggressive)

    def test_report_contains_removed_noise_block(self):
        html = """
        <html><body>
          <p>目录</p>
          <p>第一章 童年 ........ 12</p>
          <p>这里是正文。</p>
        </body></html>
        """

        text, report = extract_text_from_html_with_report(html, cleaning_strictness="balanced")

        self.assertIn("这里是正文。", text)
        self.assertGreaterEqual(report["removed_blocks"], 1)
        self.assertGreaterEqual(len(report["removed_samples"]), 1)
        self.assertIn("raw_chars", report)
        self.assertIn("kept_chars", report)
        self.assertIn("removed_chars", report)
        self.assertIn("retention_ratio", report)
        self.assertIn("kept_samples", report)
        self.assertIn("reason_counts", report)
        self.assertIn("removed_reason_counts", report)
        reasons = {sample["reason"] for sample in report["removed_samples"]}
        self.assertIn("noise_pattern", reasons)

    def test_preserves_block_boundaries_as_paragraph_breaks(self):
        html = """
        <html><body>
          <h1>第一章 童年</h1>
          <p>我们从一份档案开始。</p>
          <p>姓名：朱元璋。</p>
        </body></html>
        """

        text = extract_text_from_html(html, cleaning_strictness="balanced")

        self.assertIn("第一章 童年\n我们从一份档案开始。\n姓名：朱元璋。", text)

    def test_balanced_keeps_short_english_content_sentence(self):
        html = """
        <html><body>
          <p>To Leon Werth when he was a little boy</p>
          <p>Chapter I</p>
        </body></html>
        """

        text = extract_text_from_html(html, cleaning_strictness="balanced")

        self.assertIn("To Leon Werth when he was a little boy", text)
        self.assertNotIn("Chapter I", text)

    def test_invalid_strictness_raises_value_error(self):
        with self.assertRaises(ValueError):
            extract_text_from_html("<p>hello</p>", cleaning_strictness="invalid")

    def test_removes_wrapped_generic_marker(self):
        html = """
        <html><body>
          <p>========正文========</p>
          <p>这里是第一段真实正文。</p>
        </body></html>
        """

        text = extract_text_from_html(html, cleaning_strictness="balanced")

        self.assertNotIn("========正文========", text)
        self.assertIn("这里是第一段真实正文。", text)

    def test_unwraps_wrapped_chapter_heading(self):
        html = """
        <html><body>
          <p>========第一章 童年========</p>
          <p>我们从一份档案开始。</p>
        </body></html>
        """

        text = extract_text_from_html(html, cleaning_strictness="balanced")

        self.assertIn("第一章 童年", text)
        self.assertNotIn("========", text)
        self.assertIn("我们从一份档案开始。", text)

    def test_removes_inline_wrapped_marker_inside_long_block(self):
        html = """
        <html><body>
          <p>声明：本书来自互联网。 ========简介======== 书名：明朝那些事儿。 ========正文======== 第一章开始。</p>
        </body></html>
        """

        text = extract_text_from_html(html, cleaning_strictness="balanced")

        self.assertIn("声明：本书来自互联网。", text)
        self.assertIn("书名：明朝那些事儿。", text)
        self.assertIn("第一章开始。", text)
        self.assertNotIn("========简介========", text)
        self.assertNotIn("========正文========", text)

    def test_normalizes_parenthesized_book_title_for_tts(self):
        html = """
        <html><body>
          <p>这是引文（《明实录》）。</p>
        </body></html>
        """

        text = extract_text_from_html(html, cleaning_strictness="balanced")

        self.assertIn("这是引文《明实录》。", text)
        self.assertNotIn("（《明实录》）", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
