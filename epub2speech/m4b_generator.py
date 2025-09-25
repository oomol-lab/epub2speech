#!/usr/bin/env python3
"""
M4B有声书生成器
基于FFmpeg将多个音频章节合并成带导航的M4B文件
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any


class ChapterInfo:
    """章节信息"""

    def __init__(self, title: str, audio_file: Path):
        self.title = title
        self.audio_file = Path(audio_file)

    def __repr__(self):
        return f"ChapterInfo(title='{self.title}', audio_file='{self.audio_file}')"


class M4BGenerator:
    """M4B有声书生成器"""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        初始化M4B生成器

        Args:
            ffmpeg_path: FFmpeg可执行文件路径
            ffprobe_path: FFprobe可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self._check_dependencies()

    def _check_dependencies(self):
        """检查必要的依赖"""
        if not shutil.which(self.ffmpeg_path):
            raise RuntimeError(f"FFmpeg not found at {self.ffmpeg_path}. Please install FFmpeg.")
        if not shutil.which(self.ffprobe_path):
            raise RuntimeError(f"FFprobe not found at {self.ffprobe_path}. Please install FFmpeg.")

    def probe_duration(self, file_path: Path) -> float:
        """
        获取音频文件时长

        Args:
            file_path: 音频文件路径

        Returns:
            时长（秒）
        """
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
        """
        创建章节元数据文件

        Args:
            chapters: 章节信息列表
            output_dir: 输出目录

        Returns:
            元数据文件路径
        """
        metadata_file = output_dir / "chapters.txt"

        with open(metadata_file, "w", encoding="utf-8") as f:
            # FFMPEG元数据头部
            f.write(";FFMETADATA1\n")

            # 计算每个章节的时间戳
            start_time = 0
            for chapter in chapters:
                duration = self.probe_duration(chapter.audio_file)
                end_time = start_time + int(duration * 1000)  # 转换为毫秒

                # 写入章节信息
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={start_time}\n")
                f.write(f"END={end_time}\n")
                f.write(f"title={chapter.title}\n")
                f.write("\n")

                start_time = end_time

        return metadata_file

    def concat_audio_files(self, chapters: List[ChapterInfo], output_dir: Path, book_title: str) -> Path:
        """
        合并音频文件

        Args:
            chapters: 章节信息列表
            output_dir: 输出目录
            book_title: 书名（用于临时文件名）

        Returns:
            合并后的音频文件路径
        """
        # 创建文件列表用于concat
        file_list_path = output_dir / f"{book_title}_concat_list.txt"
        concat_audio_path = output_dir / f"{book_title}_concatenated.tmp.mp4"

        # 写入文件列表
        with open(file_list_path, 'w', encoding='utf-8') as f:
            for chapter in chapters:
                # 使用绝对路径并确保路径被正确引用
                abs_path = chapter.audio_file.resolve()
                f.write(f"file '{abs_path}'\n")

        # 使用FFmpeg concat合并音频
        concat_cmd = [
            self.ffmpeg_path,
            '-y',  # 覆盖输出
            '-f', 'concat',
            '-safe', '0',
            '-i', str(file_list_path),
            '-c', 'copy',  # 直接复制，不重新编码
            str(concat_audio_path)
        ]

        try:
            subprocess.run(concat_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to concatenate audio files: {e.stderr}") from e
        finally:
            # 清理临时文件列表
            file_list_path.unlink(missing_ok=True)

        return concat_audio_path

    def generate_m4b(self,
                    title: str,
                    chapters: List[ChapterInfo],
                    output_path: Path,
                    cover_path: Path | None = None,
                    audio_bitrate: str = "64k") -> Path:
        """
        生成M4B有声书文件

        Args:
            title: 书名
            author: 作者
            chapters: 章节信息列表
            output_path: 输出M4B文件路径
            cover_image: 封面图片路径（可选）
            audio_bitrate: 音频比特率，默认64k

        Returns:
            生成的M4B文件路径
        """
        output_path = Path(output_path)
        output_dir = output_path.parent

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 验证所有音频文件存在
        for chapter in chapters:
            if not chapter.audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {chapter.audio_file}")

        # 创建章节元数据文件
        metadata_file = self.create_chapter_metadata(chapters, output_dir)

        # 合并音频文件
        concat_audio = self.concat_audio_files(chapters, output_dir, title)

        # 准备封面参数
        cover_args = []
        if cover_path and cover_path.exists():
            cover_args = [
                '-i', str(cover_path),
                '-map', '2:v',
                '-disposition:v', 'attached_pic',
                '-c:v', 'copy',
            ]

        # 构建FFmpeg命令
        ffmpeg_cmd = [
            self.ffmpeg_path,
            '-y',  # 覆盖输出

            # 音频输入
            '-i', str(concat_audio),
            # 章节元数据输入
            '-i', str(metadata_file),
        ]

        # 添加封面输入（如果有）
        if cover_args:
            ffmpeg_cmd.extend(cover_args)

        # 输出参数
        ffmpeg_cmd.extend([
            # 音频映射和编码
            '-map', '0:a',
            '-c:a', 'aac',
            '-b:a', audio_bitrate,

            # 元数据映射
            '-map_metadata', '1',

            # 输出格式和文件
            '-f', 'mp4',
            str(output_path)
        ])

        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed to create M4B: {e.stderr}") from e

        finally:
            # 清理临时文件
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
    """
    从章节数据创建M4B文件的便捷函数

    Args:
        title: 书名
        author: 作者
        chapters: 章节列表，每个章节包含 'title' 和 'audio_file' 键
        output_path: 输出M4B文件路径
        cover_image: 封面图片路径（可选）
        audio_bitrate: 音频比特率

    Returns:
        生成的M4B文件路径

    Example:
        chapters = [
            {"title": "第一章：开始", "audio_file": "/path/to/chapter1.wav"},
            {"title": "第二章：发展", "audio_file": "/path/to/chapter2.wav"},
            {"title": "第三章：结束", "audio_file": "/path/to/chapter3.wav"}
        ]
        m4b_path = create_m4b_from_chapters("我的书", "作者名", chapters, "/output/book.m4b")
    """
    generator = M4BGenerator()

    # 转换章节数据格式
    chapter_infos = []
    for chapter_data in chapters:
        chapter_info = ChapterInfo(
            title=chapter_data["title"],
            audio_file=Path(chapter_data["audio_file"])
        )
        chapter_infos.append(chapter_info)

    # 生成M4B
    result_path = generator.generate_m4b(
        title=title,
        chapters=chapter_infos,
        output_path=Path(output_path),
        cover_path=Path(cover_image) if cover_image else None,
        audio_bitrate=audio_bitrate
    )
    return str(result_path)