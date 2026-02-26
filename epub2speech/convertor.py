import io
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, UTC
from os import PathLike
from pathlib import Path
from typing import Callable, Generator

import numpy as np
import soundfile as sf
from PIL import Image

from .chapter_tts import ChapterTTS
from .epub_picker import EpubPicker
from .m4b_generator import ChapterInfo, M4BGenerator
from .tts.protocol import TextToSpeechProtocol

_SENTENCE_RE = re.compile(r"[^\n。！？!?；;]+[。！？!?；;]?")
_ABNORMAL_SYMBOL_RE = re.compile(r"[*#=_~]{3,}|�")
_NUMERIC_TOKEN_RE = re.compile(r"\d[\d,.:/\-]*")


@dataclass
class ConversionProgress:
    current_chapter: int
    total_chapters: int
    chapter_title: str

    @property
    def progress(self) -> float:
        return (self.current_chapter / self.total_chapters) * 100 if self.total_chapters > 0 else 0


class _EpubToSpeechConverter:
    def __init__(
        self,
        voice: str,
        epub_path: PathLike,
        workspace: PathLike,
        output_path: PathLike,
        max_chapters: int | None,
        max_tts_segment_chars: int,
        cleaning_strictness: str,
        text_normalization_level: str,
        dump_cleaning_report: bool,
        loudnorm_enabled: bool,
        loudnorm_i: float,
        loudnorm_tp: float,
        loudnorm_lra: float,
        tts_protocol: TextToSpeechProtocol,
        progress_callback: Callable[[ConversionProgress], None] | None = None,
    ):
        self._voice: str = voice
        self._epub_path: Path = Path(epub_path)
        self._workspace_path: Path = Path(workspace)
        self._output_path: Path = Path(output_path)
        self._max_chapters: int | None = max_chapters
        self._progress_callback: Callable[[ConversionProgress], None] | None = progress_callback
        self._epub_picker = EpubPicker(epub_path, cleaning_strictness=cleaning_strictness)
        self._cleaning_strictness = cleaning_strictness
        self._dump_cleaning_report = dump_cleaning_report
        self._chapter_tts = ChapterTTS(
            tts_protocol,
            max_tts_segment_chars,
            text_normalization_level=text_normalization_level,
        )
        self._m4b_generator = M4BGenerator()
        self._audio_filter_chain = (
            f"loudnorm=I={loudnorm_i}:TP={loudnorm_tp}:LRA={loudnorm_lra}" if loudnorm_enabled else None
        )
        self._document_reports: list[dict] = []
        self._audio_qc_reports: list[dict] = []
        assert max_chapters is None or max_chapters >= 1, "max_chapters must be at least 1"

    def convert(self) -> Path | None:
        chapters = list(self._epub_picker.get_nav_items())
        if not chapters:
            if self._dump_cleaning_report:
                self._write_cleaning_summary(chapters=[])
                self._write_audio_qc()
            return None
        if self._max_chapters is not None:
            chapters = chapters[: self._max_chapters]

        chapter_infos: list[ChapterInfo] = []
        for chapter_info in self._generate_chapter_infos(chapters):
            chapter_infos.append(chapter_info)

        if not chapter_infos:
            if self._dump_cleaning_report:
                self._write_cleaning_summary(chapters=chapters)
                self._write_audio_qc()
            return None

        cover_bytes = self._epub_picker.cover_bytes
        cover_path: Path | None = None
        if cover_bytes:
            cover_path = self._save_cover_with_proper_extension(cover_bytes)
            cover_bytes = None

        self._m4b_generator.generate_m4b(
            titles=self._epub_picker.title,
            authors=self._epub_picker.author,
            chapters=chapter_infos,
            output_path=self._output_path,
            workspace_path=self._workspace_path,
            cover_path=cover_path,
            audio_filter_chain=self._audio_filter_chain,
        )
        if self._dump_cleaning_report:
            self._write_cleaning_summary(chapters=chapters)
            self._write_audio_qc()
        return self._output_path

    def _generate_chapter_infos(self, chapters: list[tuple[str, str]]) -> Generator[ChapterInfo, None, None]:
        for i, (chapter_title, chapter_href) in enumerate(chapters):
            progress = ConversionProgress(current_chapter=i, total_chapters=len(chapters), chapter_title=chapter_title)
            if self._progress_callback:
                self._progress_callback(progress)

            audio_file = self._convert_chapter_to_audio(
                chapter_title=chapter_title,
                chapter_href=chapter_href,
                chapter_index=i,
            )
            if audio_file:
                yield ChapterInfo(title=chapter_title, audio_file=audio_file)

    def _convert_chapter_to_audio(
        self,
        chapter_title: str,
        chapter_href: str,
        chapter_index: int,
    ) -> Path | None:
        chapter_prefix = f"chapter_{(chapter_index + 1):03d}_{self._sanitize_filename(chapter_title)}"
        chapter_path = self._workspace_path / chapter_prefix
        audio_path = chapter_path / f"{chapter_prefix}.wav"
        chapter_path.mkdir(exist_ok=True, parents=True)

        chapter_text, cleaning_report = self._epub_picker.extract_text_with_report(
            chapter_href,
            cleaning_strictness=self._cleaning_strictness,
        )

        document_report = self._build_document_report(
            chapter_title=chapter_title,
            chapter_href=chapter_href,
            chapter_index=chapter_index,
            chapter_text=chapter_text,
            cleaning_report=cleaning_report,
        )
        self._document_reports.append(document_report)

        if not chapter_text.strip():
            return None

        if self._dump_cleaning_report:
            report_path = chapter_path / "cleaning_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(cleaning_report, f, ensure_ascii=False, indent=2)

        self._chapter_tts.process_chapter(
            text=chapter_text,
            output_path=audio_path,
            workspace_path=chapter_path,
            voice=self._voice,
        )
        if audio_path.exists():
            document_report["audio_generated"] = True
            self._audio_qc_reports.append(
                self._build_audio_qc_report(
                    chapter_title=chapter_title,
                    chapter_href=chapter_href,
                    chapter_index=chapter_index,
                    audio_path=audio_path,
                )
            )
            return audio_path

        return None

    def _build_document_report(
        self,
        chapter_title: str,
        chapter_href: str,
        chapter_index: int,
        chapter_text: str,
        cleaning_report: dict,
    ) -> dict:
        cleaned_chars = len(chapter_text)
        raw_chars = int(cleaning_report.get("raw_chars", cleaned_chars))
        kept_chars = int(cleaning_report.get("kept_chars", cleaned_chars))
        removed_chars = int(cleaning_report.get("removed_chars", max(raw_chars - kept_chars, 0)))
        retention_ratio = round((kept_chars / max(raw_chars, 1)), 6)
        readability = self._compute_readability_metrics(chapter_text)

        return {
            "index": chapter_index + 1,
            "title": chapter_title,
            "href": chapter_href,
            "cleaned_chars": cleaned_chars,
            "raw_chars": raw_chars,
            "kept_chars": kept_chars,
            "removed_chars": removed_chars,
            "retention_ratio": retention_ratio,
            "char_metrics_estimated": False,
            "total_blocks": int(cleaning_report.get("total_blocks", 0)),
            "kept_blocks": int(cleaning_report.get("kept_blocks", 0)),
            "removed_blocks": int(cleaning_report.get("removed_blocks", 0)),
            "removed_samples": list(cleaning_report.get("removed_samples", [])),
            "removed_reason_counts": dict(cleaning_report.get("removed_reason_counts", {})),
            "reason_counts": dict(cleaning_report.get("reason_counts", {})),
            "readability": readability,
            "audio_generated": False,
        }

    def _compute_readability_metrics(self, text: str) -> dict:
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
            "p95_sentence_length": self._percentile(sentence_lengths, 95),
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

    def _build_audio_qc_report(
        self,
        chapter_title: str,
        chapter_href: str,
        chapter_index: int,
        audio_path: Path,
    ) -> dict:
        data, sample_rate = sf.read(audio_path)
        if isinstance(data, np.ndarray) and data.ndim > 1:
            mono = np.mean(data, axis=1)
        else:
            mono = np.asarray(data)

        abs_mono = np.abs(mono)
        sample_count = len(mono)
        peak = float(np.max(abs_mono)) if sample_count else 0.0
        rms = float(np.sqrt(np.mean(np.square(mono)))) if sample_count else 0.0
        clipped_samples = int(np.sum(abs_mono >= 0.999)) if sample_count else 0
        silence_ratio = float(np.mean(abs_mono <= 0.001)) if sample_count else 1.0

        return {
            "index": chapter_index + 1,
            "title": chapter_title,
            "href": chapter_href,
            "audio_file": str(audio_path),
            "sample_rate": int(sample_rate),
            "duration_seconds": round((sample_count / sample_rate), 3) if sample_rate > 0 else 0.0,
            "peak_dbfs": self._to_dbfs(peak),
            "rms_dbfs": self._to_dbfs(rms),
            "silence_ratio": round(silence_ratio, 6),
            "clipped_samples": clipped_samples,
            "clipped_ratio": round((clipped_samples / max(sample_count, 1)), 6),
        }

    def _write_cleaning_summary(self, chapters: list[tuple[str, str]]) -> None:
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

        for report in self._document_reports:
            total_cleaned_chars += int(report.get("cleaned_chars", 0))
            total_raw_chars += int(report.get("raw_chars", 0))
            total_kept_chars += int(report.get("kept_chars", 0))
            total_removed_chars += int(report.get("removed_chars", 0))
            total_blocks += int(report.get("total_blocks", 0))
            total_removed_blocks += int(report.get("removed_blocks", 0))

            removed_reason_counts.update(report.get("removed_reason_counts", {}))
            reason_counts.update(report.get("reason_counts", {}))

            readability = report.get("readability", {})
            sentence_count = int(readability.get("sentence_count", 0))
            total_sentences += sentence_count
            total_sentence_chars += sentence_count * float(readability.get("avg_sentence_length", 0.0))
            total_overlong_sentences += int(readability.get("overlong_sentence_count", 0))
            total_abnormal_symbols += int(readability.get("abnormal_symbol_count", 0))
            total_numeric_chars += int(readability.get("numeric_char_count", 0))
            max_sentence_length = max(max_sentence_length, int(readability.get("max_sentence_length", 0)))

        document_count = len(self._document_reports)
        empty_chapter_count = sum(1 for report in self._document_reports if int(report.get("cleaned_chars", 0)) == 0)
        ultra_short_threshold = 120
        ultra_short_chapter_count = sum(
            1
            for report in self._document_reports
            if 0 < int(report.get("cleaned_chars", 0)) < ultra_short_threshold
        )
        generated_audio_count = sum(1 for report in self._document_reports if bool(report.get("audio_generated", False)))
        char_metrics_estimated_documents = sum(
            1 for report in self._document_reports if bool(report.get("char_metrics_estimated", False))
        )

        hrefs = [str(report.get("href", "")) for report in self._document_reports]
        duplicate_href_count = max(len(hrefs) - len(set(hrefs)), 0)
        order_consistent = [int(report.get("index", 0)) for report in self._document_reports] == list(
            range(1, document_count + 1)
        )

        possible_false_drop = [
            {
                "index": report.get("index"),
                "title": report.get("title"),
                "href": report.get("href"),
                "retention_ratio": report.get("retention_ratio"),
                "removed_chars": report.get("removed_chars"),
                "removed_reason_counts": report.get("removed_reason_counts", {}),
            }
            for report in self._document_reports
            if float(report.get("retention_ratio", 1.0)) < 0.6 and int(report.get("removed_chars", 0)) > 120
        ][:20]
        possible_false_keep = [
            {
                "index": report.get("index"),
                "title": report.get("title"),
                "href": report.get("href"),
                "abnormal_symbol_ratio": report.get("readability", {}).get("abnormal_symbol_ratio", 0.0),
                "numeric_char_ratio": report.get("readability", {}).get("numeric_char_ratio", 0.0),
            }
            for report in self._document_reports
            if float(report.get("readability", {}).get("abnormal_symbol_ratio", 0.0)) > 0.003
            or float(report.get("readability", {}).get("numeric_char_ratio", 0.0)) > 0.05
        ][:20]

        summary = {
            "book": self._epub_path.name,
            "strictness": self._cleaning_strictness,
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "documents": self._document_reports,
            "document_count": document_count,
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
                "planned_chapter_count": len(chapters),
                "generated_audio_chapter_count": generated_audio_count,
                "empty_chapter_count": empty_chapter_count,
                "empty_chapter_ratio": round((empty_chapter_count / max(document_count, 1)), 6),
                "ultra_short_threshold": ultra_short_threshold,
                "ultra_short_chapter_count": ultra_short_chapter_count,
                "ultra_short_chapter_ratio": round((ultra_short_chapter_count / max(document_count, 1)), 6),
                "duplicate_href_count": duplicate_href_count,
                "order_consistent": order_consistent,
            },
            "review_candidates": {
                "possible_false_drop": possible_false_drop,
                "possible_false_keep": possible_false_keep,
            },
        }

        with open(self._workspace_path / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    def _write_audio_qc(self) -> None:
        rms_values = [entry["rms_dbfs"] for entry in self._audio_qc_reports if entry.get("rms_dbfs") is not None]
        peak_values = [entry["peak_dbfs"] for entry in self._audio_qc_reports if entry.get("peak_dbfs") is not None]
        total_duration = sum(float(entry.get("duration_seconds", 0.0)) for entry in self._audio_qc_reports)
        high_silence_count = sum(1 for entry in self._audio_qc_reports if float(entry.get("silence_ratio", 0.0)) > 0.2)
        clipped_count = sum(1 for entry in self._audio_qc_reports if float(entry.get("clipped_ratio", 0.0)) > 0.0)

        payload = {
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "chapter_count": len(self._audio_qc_reports),
            "total_duration_seconds": round(total_duration, 3),
            "mean_rms_dbfs": round((sum(rms_values) / len(rms_values)), 3) if rms_values else None,
            "mean_peak_dbfs": round((sum(peak_values) / len(peak_values)), 3) if peak_values else None,
            "high_silence_chapter_count": high_silence_count,
            "clipped_chapter_count": clipped_count,
            "chapters": self._audio_qc_reports,
        }

        with open(self._workspace_path / "audio_qc.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _percentile(self, values: list[int], percent: float) -> int:
        if not values:
            return 0
        sorted_values = sorted(values)
        position = int(math.ceil((percent / 100.0) * len(sorted_values))) - 1
        clamped = min(max(position, 0), len(sorted_values) - 1)
        return sorted_values[clamped]

    def _to_dbfs(self, value: float) -> float | None:
        if value <= 0:
            return None
        return round((20 * math.log10(value)), 3)

    def _save_cover_with_proper_extension(self, cover_bytes: bytes) -> Path:
        try:
            image_buffer = io.BytesIO(cover_bytes)
            with Image.open(image_buffer) as img:
                format_name = img.format
                if format_name == "JPEG":
                    extension = ".jpg"
                elif format_name == "PNG":
                    extension = ".png"
                elif format_name == "GIF":
                    extension = ".gif"
                elif format_name == "BMP":
                    extension = ".bmp"
                elif format_name == "WEBP":
                    extension = ".webp"
                else:
                    extension = ".jpg"

                cover_path = self._workspace_path / f"cover{extension}"

                # 保存图片
                img.save(cover_path, format=format_name)
                return cover_path

        except Exception:
            # 如果检测失败，回退到默认的jpg
            cover_path = self._workspace_path / "cover.jpg"
            with open(cover_path, "wb") as f:
                f.write(cover_bytes)
            return cover_path

    def _sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r'[<>:"/\|?*]', "_", filename)
        return sanitized[:50]


def convert_epub_to_m4b(
    epub_path: PathLike,
    workspace: PathLike,
    output_path: PathLike,
    tts_protocol: TextToSpeechProtocol,
    voice: str,
    max_chapters: int | None = None,
    max_tts_segment_chars: int = 500,
    cleaning_strictness: str = "balanced",
    text_normalization_level: str = "basic",
    dump_cleaning_report: bool = False,
    loudnorm_enabled: bool = True,
    loudnorm_i: float = -16.0,
    loudnorm_tp: float = -1.5,
    loudnorm_lra: float = 11.0,
    progress_callback: Callable[[ConversionProgress], None] | None = None,
) -> Path | None:
    converter = _EpubToSpeechConverter(
        epub_path=epub_path,
        workspace=workspace,
        output_path=output_path,
        tts_protocol=tts_protocol,
        max_chapters=max_chapters,
        max_tts_segment_chars=max_tts_segment_chars,
        cleaning_strictness=cleaning_strictness,
        text_normalization_level=text_normalization_level,
        dump_cleaning_report=dump_cleaning_report,
        loudnorm_enabled=loudnorm_enabled,
        loudnorm_i=loudnorm_i,
        loudnorm_tp=loudnorm_tp,
        loudnorm_lra=loudnorm_lra,
        voice=voice,
        progress_callback=progress_callback,
    )
    return converter.convert()
