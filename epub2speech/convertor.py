import io
import json
import re
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Callable, Generator

from PIL import Image

from .chapter_tts import ChapterTTS
from .epub_picker import EpubPicker
from .m4b_generator import ChapterInfo, M4BGenerator
from .tts.protocol import TextToSpeechProtocol


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
        dump_cleaning_report: bool,
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
        self._chapter_tts = ChapterTTS(tts_protocol, max_tts_segment_chars)
        self._m4b_generator = M4BGenerator()
        assert max_chapters is None or max_chapters >= 1, "max_chapters must be at least 1"

    def convert(self) -> Path | None:
        chapters = list(self._epub_picker.get_nav_items())
        if not chapters:
            return None

        chapter_infos: list[ChapterInfo] = []
        for chapter_info in self._generate_chapter_infos(chapters):
            chapter_infos.append(chapter_info)
            if self._max_chapters is not None and len(chapter_infos) >= self._max_chapters:
                break

        if not chapter_infos:
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
        )
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
        return audio_path

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
    dump_cleaning_report: bool = False,
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
        dump_cleaning_report=dump_cleaning_report,
        voice=voice,
        progress_callback=progress_callback,
    )
    return converter.convert()
