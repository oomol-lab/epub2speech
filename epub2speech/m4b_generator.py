#!/usr/bin/env python3
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any


class ChapterInfo:
    def __init__(self, title: str, audio_file: Path):
        self.title = title
        self.audio_file = Path(audio_file)

    def __repr__(self):
        return f"ChapterInfo(title='{self.title}', audio_file='{self.audio_file}')"


class M4BGenerator:
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self._check_dependencies()

    def _check_dependencies(self):
        if not shutil.which(self.ffmpeg_path):
            raise RuntimeError(f"FFmpeg not found at {self.ffmpeg_path}. Please install FFmpeg.")
        if not shutil.which(self.ffprobe_path):
            raise RuntimeError(f"FFprobe not found at {self.ffprobe_path}. Please install FFmpeg.")

    def probe_duration(self, file_path: Path) -> float:
        try:
            args = [
                self.ffprobe_path,
                '-i', str(file_path),
                '-show_entries', 'format=duration',
                '-v', 'quiet',
                '-of', 'default=noprint_wrappers=1:nokey=1'
            ]
            proc = subprocess.run(args, capture_output=True, text=True, check=True)
            return float(proc.stdout.strip())
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to probe duration for {file_path}: {e.stderr}") from e

    def create_chapter_metadata(self, chapters: List[ChapterInfo], output_dir: Path) -> Path:
        metadata_file = output_dir / "chapters.txt"

        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\n")

            start_time = 0
            for chapter in chapters:
                duration = self.probe_duration(chapter.audio_file)
                end_time = start_time + int(duration * 1000)

                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={start_time}\n")
                f.write(f"END={end_time}\n")
                f.write(f"title={chapter.title}\n")
                f.write("\n")

                start_time = end_time

        return metadata_file

    def concat_audio_files(self, chapters: List[ChapterInfo], output_dir: Path, book_title: str) -> Path:
        file_list_path = output_dir / f"{book_title}_concat_list.txt"
        concat_audio_path = output_dir / f"{book_title}_concatenated.tmp.mp4"

        with open(file_list_path, 'w', encoding='utf-8') as f:
            for chapter in chapters:
                abs_path = chapter.audio_file.resolve()
                f.write(f"file '{abs_path}'\n")

        concat_cmd = [
            self.ffmpeg_path,
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(file_list_path),
            '-c', 'copy',
            str(concat_audio_path)
        ]

        try:
            subprocess.run(concat_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to concatenate audio files: {e.stderr}") from e
        finally:
            file_list_path.unlink(missing_ok=True)

        return concat_audio_path

    def generate_m4b(
        self,
        title: str,
        chapters: List[ChapterInfo],
        output_path: Path,
        cover_path: Path | None = None,
        audio_bitrate: str = "64k"
    ) -> Path:
        output_path = Path(output_path)
        output_dir = output_path.parent

        output_dir.mkdir(parents=True, exist_ok=True)

        for chapter in chapters:
            if not chapter.audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {chapter.audio_file}")

        metadata_file = self.create_chapter_metadata(chapters, output_dir)
        concat_audio = self.concat_audio_files(chapters, output_dir, title)

        cover_args = []
        if cover_path and cover_path.exists():
            cover_args = [
                '-i', str(cover_path),
                '-map', '2:v',
                '-disposition:v', 'attached_pic',
                '-c:v', 'copy',
            ]

        ffmpeg_cmd = [
            self.ffmpeg_path,
            '-y',
            '-i', str(concat_audio),
            '-i', str(metadata_file),
        ]

        if cover_args:
            ffmpeg_cmd.extend(cover_args)

        ffmpeg_cmd.extend([
            '-map', '0:a',
            '-c:a', 'aac',
            '-b:a', audio_bitrate,
            '-map_metadata', '1',
            '-f', 'mp4',
            str(output_path)
        ])

        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed to create M4B: {e.stderr}") from e

        finally:
            for temp_file in [metadata_file, concat_audio]:
                if temp_file.exists():
                    temp_file.unlink()

        return output_path


def create_m4b_from_chapters(
    title: str,
    chapters: List[Dict[str, Any]],
    output_path: str,
    cover_image: Optional[str] = None,
    audio_bitrate: str = "64k"
) -> str:
    generator = M4BGenerator()

    chapter_infos = []
    for chapter_data in chapters:
        chapter_info = ChapterInfo(
            title=chapter_data["title"],
            audio_file=Path(chapter_data["audio_file"])
        )
        chapter_infos.append(chapter_info)

    result_path = generator.generate_m4b(
        title=title,
        chapters=chapter_infos,
        output_path=Path(output_path),
        cover_path=Path(cover_image) if cover_image else None,
        audio_bitrate=audio_bitrate
    )
    return str(result_path)