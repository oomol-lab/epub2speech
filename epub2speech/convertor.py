import re

from os import PathLike
from pathlib import Path
from typing import Callable
from dataclasses import dataclass

from .epub_picker import EpubPicker
from .chapter_tts import ChapterTTS
from .m4b_generator import M4BGenerator, ChapterInfo
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
        tts_protocol: TextToSpeechProtocol,
        progress_callback: Callable[[ConversionProgress], None] | None = None,
    ):
        self._voice: str = voice
        self._epub_path: Path = Path(epub_path)
        self._workspace_path: Path = Path(workspace)
        self._output_path: Path = Path(output_path)
        self._max_chapters: int | None = max_chapters
        self._tts_protocol: TextToSpeechProtocol = tts_protocol
        self._progress_callback: Callable[[ConversionProgress], None] | None = progress_callback
        self._epub_picker = EpubPicker(epub_path)
        self._chapter_tts = ChapterTTS(tts_protocol=tts_protocol)
        self._m4b_generator = M4BGenerator()

    def convert(self) -> Path | None:
        chapters = list(self._epub_picker.get_nav_items())
        if self._max_chapters is not None:
            chapters = chapters[:self._max_chapters]
        if not chapters:
            return None

        chapter_infos: list[ChapterInfo] = []

        for i, (chapter_title, chapter_href) in enumerate(chapters):
            progress = ConversionProgress(
                current_chapter=i,
                total_chapters=len(chapters),
                chapter_title=chapter_title
            )
            if self._progress_callback:
                self._progress_callback(progress)

            audio_file = self._convert_chapter_to_audio(
                chapter_title,
                chapter_href,
                i,
            )
            if audio_file:
                chapter_infos.append(ChapterInfo(
                    title=chapter_title,
                    audio_file=audio_file
                ))

        cover_bytes = self._epub_picker.cover_bytes
        cover_path: Path | None = None
        if cover_bytes:
            # TODO: 类型不一定是 jpg
            cover_path = self._workspace_path / "cover.jpg"
            with open(cover_path, "wb") as f:
                f.write(cover_bytes)
                cover_bytes = None

        self._m4b_generator.generate_m4b(
            title=self._epub_picker.title[0] if self._epub_picker.title else "Unknown",
            chapters=chapter_infos,
            output_path=self._output_path,
            cover_path=cover_path
        )
        return self._output_path

    def _convert_chapter_to_audio(
        self,
        chapter_title: str,
        chapter_href: str,
        chapter_index: int,
    ) -> Path | None:
        chapter_prefix = f"chapter_{(chapter_index + 1):03d}_{self._sanitize_filename(chapter_title)}"
        chapter_path = self._workspace_path / chapter_prefix
        audio_path = chapter_path / f"{chapter_prefix}.wav"

        chapter_text = self._epub_picker.extract_text(chapter_href)
        if not chapter_text.strip():
            return None

        chapter_path.mkdir(exist_ok=True, parents=True)
        self._chapter_tts.process_chapter(
            text=chapter_text,
            output_path=audio_path,
            workspace_path=chapter_path,
            voice=self._voice,
        )
        return audio_path

    def _sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r'[<>:"/\|?*]', '_', filename)
        return sanitized[:50]


def convert_epub_to_m4b(
    epub_path: PathLike,
    workspace: PathLike,
    output_path: PathLike,
    tts_protocol: TextToSpeechProtocol,
    voice: str,
    max_chapters: int | None = None,
    progress_callback: Callable[[ConversionProgress], None] | None = None,
) -> Path | None:
    converter = _EpubToSpeechConverter(
        epub_path=epub_path,
        workspace=workspace,
        output_path=output_path,
        tts_protocol=tts_protocol,
        max_chapters=max_chapters,
        voice=voice,
        progress_callback=progress_callback
    )
    return converter.convert()