#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "epub2speech" / "text_normalizer.py"
SPEC = importlib.util.spec_from_file_location("text_normalizer_module_for_test", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

normalize_text_for_tts = module.normalize_text_for_tts


class TestTextNormalizer(unittest.TestCase):
    def test_off_level_keeps_original_text(self):
        source = "今天是2026-02-26，增长12.5%。"
        self.assertEqual(source, normalize_text_for_tts(source, level="off"))

    def test_basic_normalizes_date_percent_and_chapter_numbers(self):
        source = "今天是2026-02-26，第12章增长12.5%。"
        normalized = normalize_text_for_tts(source, level="basic")
        self.assertIn("二零二六年二月二十六日", normalized)
        self.assertIn("第十二章", normalized)
        self.assertIn("百分之十二点五", normalized)

    def test_basic_normalizes_cjk_context_numbers_and_time(self):
        source = "他有3个苹果，会议在09:30开始。"
        normalized = normalize_text_for_tts(source, level="basic")
        self.assertIn("他有三个苹果", normalized)
        self.assertIn("九点三十分", normalized)


if __name__ == "__main__":
    unittest.main(verbosity=2)
