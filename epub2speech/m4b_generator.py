#!/usr/bin/env python3
import subprocess
import shutil
from pathlib import Path


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

    def generate_m4b(
        self,
        titles: list[str],
        authors: list[str],
        chapters: list[ChapterInfo],
        output_path: Path,
        workspace_path: Path,
        cover_path: Path | None = None,
        audio_bitrate: str = "64k"
    ) -> Path:
        output_path = Path(output_path)
        output_dir = output_path.parent

        workspace_path.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        for chapter in chapters:
            if not chapter.audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {chapter.audio_file}")

        metadata_file = self._create_chapter_metadata(chapters, workspace_path, titles, authors)
        concat_audio = self._concat_audio_files(chapters, workspace_path)
        cover_args: list[str] = []

        if cover_path and cover_path.exists():
            cover_args = [
                "-i", str(cover_path),
                "-map", "2:v",
                "-disposition:v", "attached_pic",
                "-c:v", "copy",
            ]
        ffmpeg_cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(concat_audio),
            "-i", str(metadata_file),
        ]
        if cover_args:
            ffmpeg_cmd.extend(cover_args)

        ffmpeg_cmd.extend([
            "-map", "0:a",
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            "-map_metadata", "1",
            "-f", "mp4",
            str(output_path)
        ])
        self._run_command(ffmpeg_cmd, "FFmpeg failed to create M4B")
        return output_path

    def _create_chapter_metadata(self, chapters: list[ChapterInfo], work_dir: Path, titles: list[str], authors: list[str]) -> Path:
        metadata_file = work_dir / "chapters.txt"

        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write(";FFMETADATA1\n")

            # Write titles
            if titles:
                # Use first title as main title, join multiple titles with " / " for compatibility
                main_title = " / ".join(titles)
                f.write(f"title={main_title}\n")
                f.write("\n")

            # Write authors
            if authors:
                # Join multiple authors with " / " for compatibility
                author_string = " / ".join(authors)
                f.write(f"author={author_string}\n")
                f.write("\n")

            start_time = 0
            for chapter in chapters:
                duration = self._probe_duration(chapter.audio_file)
                end_time = start_time + int(duration * 1000)

                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={start_time}\n")
                f.write(f"END={end_time}\n")
                f.write(f"title={chapter.title}\n")
                f.write("\n")

                start_time = end_time

        return metadata_file

    def _probe_duration(self, file_path: Path) -> float:
        args = [
            self.ffprobe_path,
            "-i", str(file_path),
            "-show_entries", "format=duration",
            "-v", "quiet",
            "-of", "default=noprint_wrappers=1:nokey=1"
        ]
        result = self._run_command(args, f"Failed to probe duration for {file_path}")
        return float(result.stdout.strip())

    def _concat_audio_files(self, chapters: list[ChapterInfo], work_dir: Path) -> Path:
        work_dir.mkdir(parents=True, exist_ok=True)

        file_list_path = work_dir / "concat_list.txt"
        concat_audio_path = work_dir / "concatenated.tmp.mp4"

        with open(file_list_path, "w", encoding="utf-8") as f:
            for chapter in chapters:
                abs_path = chapter.audio_file.resolve()
                f.write(f"file '{abs_path}'\n")

        concat_cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(file_list_path),
            "-c", "copy",
            str(concat_audio_path)
        ]
        self._run_command(concat_cmd, "Failed to concatenate audio files")
        return concat_audio_path

    def _run_command(self, args: list[str], error_message: str) -> subprocess.CompletedProcess:
        """Run subprocess command with proper error handling

        We explicitly handle exit codes ourselves rather than using subprocess.run's check parameter
        to provide custom error messages with stderr content for better debugging.
        """
        result = subprocess.run(args, capture_output=True, text=True)  # pylint: disable=subprocess-run-check
        if result.returncode != 0:
            stderr_content = result.stderr.strip() if result.stderr else "No stderr output"
            raise RuntimeError(f"{error_message}: {stderr_content}")
        return result