#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_cleaning_summary import build_summary


class TestBuildCleaningSummary(unittest.TestCase):
    def test_build_summary_contains_enriched_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir)

            (report_dir / "summary.json").write_text(
                json.dumps({"book": "demo.epub", "strictness": "balanced"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (report_dir / "chap_1.xhtml.cleaned.txt").write_text("第一章\n这是正文。", encoding="utf-8")
            (report_dir / "chap_1.xhtml.cleaning_report.json").write_text(
                json.dumps(
                    {
                        "strictness": "balanced",
                        "total_blocks": 3,
                        "kept_blocks": 2,
                        "removed_blocks": 1,
                        "raw_chars": 10,
                        "kept_chars": 7,
                        "removed_chars": 3,
                        "removed_samples": [],
                        "removed_reason_counts": {"noise_pattern": 1},
                        "reason_counts": {"content_like": 2, "noise_pattern": 1},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            summary = build_summary(report_dir)

            self.assertEqual(summary["book"], "demo.epub")
            self.assertEqual(summary["document_count"], 1)
            self.assertIn("content_effectiveness", summary)
            self.assertIn("readability", summary)
            self.assertIn("chapter_integrity", summary)
            self.assertEqual(summary["content_effectiveness"]["total_removed_chars"], 3)
            self.assertEqual(summary["documents"][0]["retention_ratio"], 0.7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
