#!/usr/bin/env python3
import argparse
import json
import math
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

_SENTENCE_RE = re.compile(r"[^\n。！？!?；;]+[。！？!?；;]?")
_ABNORMAL_SYMBOL_RE = re.compile(r"[*#=_~]{3,}|�")
_NUMERIC_TOKEN_RE = re.compile(r"\d[\d,.:/\-]*")


def _percentile(values: list[int], percent: float) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    position = int(math.ceil((percent / 100.0) * len(sorted_values))) - 1
    clamped = min(max(position, 0), len(sorted_values) - 1)
    return sorted_values[clamped]


def _readability(text: str) -> dict:
    compact = text.strip()
    paragraphs = [line.strip() for line in compact.splitlines() if line.strip()]
    sentence_lengths: list[int] = []
    for sentence in _SENTENCE_RE.findall(compact):
        normalized = sentence.strip()
        if normalized:
            sentence_lengths.append(len(normalized))
    if not sentence_lengths and compact:
        sentence_lengths = [len(compact)]

    sentence_count = len(sentence_lengths)
    overlong_threshold = 120
    overlong_sentence_count = sum(1 for value in sentence_lengths if value > overlong_threshold)
    abnormal_char_count = sum(len(match.group(0)) for match in _ABNORMAL_SYMBOL_RE.finditer(compact))
    numeric_tokens = _NUMERIC_TOKEN_RE.findall(compact)
    numeric_char_count = sum(1 for char in compact if char.isdigit())

    return {
        "paragraph_count": len(paragraphs),
        "sentence_count": sentence_count,
        "avg_sentence_length": round((sum(sentence_lengths) / max(sentence_count, 1)), 3),
        "p95_sentence_length": _percentile(sentence_lengths, 95),
        "max_sentence_length": max(sentence_lengths) if sentence_lengths else 0,
        "overlong_threshold": overlong_threshold,
        "overlong_sentence_count": overlong_sentence_count,
        "overlong_sentence_ratio": round((overlong_sentence_count / max(sentence_count, 1)), 6),
        "abnormal_symbol_count": abnormal_char_count,
        "abnormal_symbol_ratio": round((abnormal_char_count / max(len(compact), 1)), 6),
        "numeric_token_count": len(numeric_tokens),
        "numeric_char_count": numeric_char_count,
        "numeric_char_ratio": round((numeric_char_count / max(len(compact), 1)), 6),
    }


def build_summary(report_dir: Path) -> dict:
    existing_summary_path = report_dir / "summary.json"
    existing_summary: dict = {}
    if existing_summary_path.exists():
        try:
            existing_summary = json.loads(existing_summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_summary = {}

    report_files = sorted(report_dir.glob("*.cleaning_report.json"))
    documents: list[dict] = []

    for report_file in report_files:
        chapter_name = report_file.name[: -len(".cleaning_report.json")]
        cleaned_file = report_dir / f"{chapter_name}.cleaned.txt"

        with open(report_file, "r", encoding="utf-8") as f:
            cleaning_report = json.load(f)
        text = cleaned_file.read_text(encoding="utf-8") if cleaned_file.exists() else ""

        cleaned_chars = len(text)
        char_metrics_estimated = "raw_chars" not in cleaning_report or "kept_chars" not in cleaning_report
        raw_chars = int(cleaning_report.get("raw_chars", cleaned_chars))
        kept_chars = int(cleaning_report.get("kept_chars", cleaned_chars))
        removed_chars = int(cleaning_report.get("removed_chars", max(raw_chars - kept_chars, 0)))
        retention_ratio = round((kept_chars / max(raw_chars, 1)), 6)
        removed_reason_counts = dict(cleaning_report.get("removed_reason_counts", {}))
        if not removed_reason_counts:
            fallback_counter: Counter[str] = Counter()
            for sample in cleaning_report.get("removed_samples", []):
                reason = sample.get("reason") or "unspecified"
                fallback_counter[reason] += 1
            removed_reason_counts = dict(fallback_counter)
        reason_counts = dict(cleaning_report.get("reason_counts", {}))
        if not reason_counts:
            reason_counts = dict(removed_reason_counts)

        documents.append(
            {
                "name": chapter_name,
                "cleaned_chars": cleaned_chars,
                "raw_chars": raw_chars,
                "kept_chars": kept_chars,
                "removed_chars": removed_chars,
                "retention_ratio": retention_ratio,
                "char_metrics_estimated": char_metrics_estimated,
                "total_blocks": int(cleaning_report.get("total_blocks", 0)),
                "kept_blocks": int(cleaning_report.get("kept_blocks", 0)),
                "removed_blocks": int(cleaning_report.get("removed_blocks", 0)),
                "removed_samples": list(cleaning_report.get("removed_samples", [])),
                "removed_reason_counts": removed_reason_counts,
                "reason_counts": reason_counts,
                "readability": _readability(text),
            }
        )

    removed_reason_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    total_cleaned_chars = 0
    total_raw_chars = 0
    total_kept_chars = 0
    total_removed_chars = 0
    total_blocks = 0
    total_removed_blocks = 0
    total_sentences = 0
    total_sentence_chars = 0
    total_overlong_sentences = 0
    total_abnormal_symbols = 0
    total_numeric_chars = 0
    max_sentence_length = 0

    for document in documents:
        total_cleaned_chars += int(document.get("cleaned_chars", 0))
        total_raw_chars += int(document.get("raw_chars", 0))
        total_kept_chars += int(document.get("kept_chars", 0))
        total_removed_chars += int(document.get("removed_chars", 0))
        total_blocks += int(document.get("total_blocks", 0))
        total_removed_blocks += int(document.get("removed_blocks", 0))

        removed_reason_counts.update(document.get("removed_reason_counts", {}))
        reason_counts.update(document.get("reason_counts", {}))

        readability = document.get("readability", {})
        sentence_count = int(readability.get("sentence_count", 0))
        total_sentences += sentence_count
        total_sentence_chars += sentence_count * float(readability.get("avg_sentence_length", 0.0))
        total_overlong_sentences += int(readability.get("overlong_sentence_count", 0))
        total_abnormal_symbols += int(readability.get("abnormal_symbol_count", 0))
        total_numeric_chars += int(readability.get("numeric_char_count", 0))
        max_sentence_length = max(max_sentence_length, int(readability.get("max_sentence_length", 0)))

    empty_chapter_count = sum(1 for document in documents if int(document.get("cleaned_chars", 0)) == 0)
    ultra_short_threshold = 120
    ultra_short_chapter_count = sum(
        1 for document in documents if 0 < int(document.get("cleaned_chars", 0)) < ultra_short_threshold
    )
    duplicate_name_count = max(len(documents) - len({str(document.get("name")) for document in documents}), 0)
    char_metrics_estimated_documents = sum(
        1 for document in documents if bool(document.get("char_metrics_estimated", False))
    )

    possible_false_drop = [
        {
            "name": document.get("name"),
            "retention_ratio": document.get("retention_ratio"),
            "removed_chars": document.get("removed_chars"),
            "removed_reason_counts": document.get("removed_reason_counts", {}),
        }
        for document in documents
        if float(document.get("retention_ratio", 1.0)) < 0.6 and int(document.get("removed_chars", 0)) > 120
    ][:20]
    possible_false_keep = [
        {
            "name": document.get("name"),
            "abnormal_symbol_ratio": document.get("readability", {}).get("abnormal_symbol_ratio", 0.0),
            "numeric_char_ratio": document.get("readability", {}).get("numeric_char_ratio", 0.0),
        }
        for document in documents
        if float(document.get("readability", {}).get("abnormal_symbol_ratio", 0.0)) > 0.003
        or float(document.get("readability", {}).get("numeric_char_ratio", 0.0)) > 0.05
    ][:20]

    strictness = ""
    if documents:
        first_report = report_dir / f"{documents[0]['name']}.cleaning_report.json"
        with open(first_report, "r", encoding="utf-8") as f:
            strictness = json.load(f).get("strictness", "")

    return {
        "book": existing_summary.get("book", report_dir.name),
        "strictness": strictness,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "documents": documents,
        "document_count": len(documents),
        "total_cleaned_chars": total_cleaned_chars,
        "total_blocks": total_blocks,
        "total_removed_blocks": total_removed_blocks,
        "removed_ratio": round((total_removed_blocks / max(total_blocks, 1)), 6),
        "content_effectiveness": {
            "total_raw_chars": total_raw_chars,
            "total_kept_chars": total_kept_chars,
            "total_removed_chars": total_removed_chars,
            "retention_ratio": round((total_kept_chars / max(total_raw_chars, 1)), 6),
            "removed_char_ratio": round((total_removed_chars / max(total_raw_chars, 1)), 6),
            "char_metrics_estimated_documents": char_metrics_estimated_documents,
            "removed_reason_counts": dict(removed_reason_counts),
            "reason_counts": dict(reason_counts),
        },
        "readability": {
            "total_sentence_count": total_sentences,
            "avg_sentence_length": round((total_sentence_chars / max(total_sentences, 1)), 3),
            "overlong_sentence_count": total_overlong_sentences,
            "overlong_sentence_ratio": round((total_overlong_sentences / max(total_sentences, 1)), 6),
            "abnormal_symbol_ratio": round((total_abnormal_symbols / max(total_cleaned_chars, 1)), 6),
            "numeric_char_ratio": round((total_numeric_chars / max(total_cleaned_chars, 1)), 6),
            "max_sentence_length": max_sentence_length,
        },
        "chapter_integrity": {
            "empty_chapter_count": empty_chapter_count,
            "empty_chapter_ratio": round((empty_chapter_count / max(len(documents), 1)), 6),
            "ultra_short_threshold": ultra_short_threshold,
            "ultra_short_chapter_count": ultra_short_chapter_count,
            "ultra_short_chapter_ratio": round((ultra_short_chapter_count / max(len(documents), 1)), 6),
            "duplicate_name_count": duplicate_name_count,
        },
        "review_candidates": {
            "possible_false_drop": possible_false_drop,
            "possible_false_keep": possible_false_keep,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build enriched summary.json from cleaning report directory")
    parser.add_argument("report_dir", type=Path, help="Directory containing *.cleaning_report.json and *.cleaned.txt")
    parser.add_argument("--output", type=Path, default=None, help="Output summary path (default: <report_dir>/summary.json)")
    args = parser.parse_args()

    report_dir = args.report_dir
    if not report_dir.exists() or not report_dir.is_dir():
        raise FileNotFoundError(f"Report directory not found: {report_dir}")

    summary = build_summary(report_dir)
    output_path = args.output or (report_dir / "summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Summary written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
