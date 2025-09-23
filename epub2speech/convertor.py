#!/usr/bin/env python3
"""
EPUB转语音转换器
将EPUB电子书转换为M4B有声书的主入口
"""

import shutil
from pathlib import Path
from typing import Optional, List, Any
from dataclasses import dataclass

from .epub_picker import EpubPicker
from .chapter_tts import ChapterTTS
from .m4b_generator import M4BGenerator, ChapterInfo
from .tts.protocol import TextToSpeechProtocol


@dataclass
class ConversionProgress:
    """转换进度信息"""
    current_chapter: int
    total_chapters: int
    current_step: str
    chapter_title: str = ""

    @property
    def progress_percentage(self) -> float:
        return (self.current_chapter / self.total_chapters) * 100 if self.total_chapters > 0 else 0


class EpubToSpeechConverter:
    """EPUB转语音转换器主类"""

    def __init__(self,
                 epub_path: Path,
                 workspace: Path,
                 output_path: Path,
                 tts_protocol: TextToSpeechProtocol):
        """
        初始化转换器

        Args:
            epub_path: EPUB文件路径
            workspace: 工作目录（用于存放临时文件）
            output_path: 输出M4B文件路径
            tts_protocol: TTS协议实例
        """
        self.epub_path = Path(epub_path)
        self.workspace = Path(workspace)
        self.output_path = Path(output_path)
        self.tts_protocol = tts_protocol

        # 创建工作目录
        self.workspace.mkdir(parents=True, exist_ok=True)

        # 初始化EPUB解析器
        self.epub_picker = EpubPicker(epub_path)

        # 初始化章节TTS处理器
        self.chapter_tts = ChapterTTS(tts_protocol=tts_protocol)

        # 初始化M4B生成器
        self.m4b_generator = M4BGenerator()

        # 临时音频文件目录
        self.temp_audio_dir = self.workspace / "audio_chapters"
        self.temp_audio_dir.mkdir(exist_ok=True)

    @property
    def book_title(self) -> str:
        """获取书名"""
        titles = self.epub_picker.meta_titles
        return str(titles[0][0]) if titles else "未知书名"

    @property
    def book_author(self) -> str:
        """获取作者"""
        creators = self.epub_picker.meta_creators
        return str(creators[0][0]) if creators else "未知作者"

    def get_chapters(self, max_chapters: Optional[int] = None) -> List[tuple[str, str]]:
        """获取章节列表"""
        chapters = []

        # 从EPUB获取导航项目
        nav_items = list(self.epub_picker.get_nav_items())

        if not nav_items:
            return chapters

        # 限制章节数
        if max_chapters:
            nav_items = nav_items[:max_chapters]

        return nav_items

    def convert(self,
                max_chapters: Optional[int] = None,
                voice: Optional[str] = None,
                progress_callback: Optional[Any] = None) -> Path:
        """
        执行转换流程

        Args:
            max_chapters: 最大转换章节数（None表示全部）
            voice: TTS语音名称
            progress_callback: 进度回调函数

        Returns:
            生成的M4B文件路径
        """
        try:
            # 获取EPUB元数据
            book_title = self.book_title
            book_author = self.book_author

            # 获取章节列表
            chapters = self.get_chapters(max_chapters)

            if not chapters:
                raise ValueError("未找到可转换的章节")

            # 转换每个章节为音频
            chapter_audio_files = []
            for i, (chapter_title, chapter_href) in enumerate(chapters):
                progress = ConversionProgress(
                    current_chapter=i + 1,
                    total_chapters=len(chapters),
                    current_step="正在转换章节",
                    chapter_title=chapter_title
                )

                if progress_callback:
                    progress_callback(progress)

                # 转换单个章节
                audio_file = self._convert_chapter_to_audio(
                    chapter_title,
                    chapter_href,
                    i + 1,
                    voice
                )

                if audio_file:
                    chapter_audio_files.append(audio_file)

            # 生成M4B文件
            if progress_callback:
                progress_callback(ConversionProgress(
                    current_chapter=len(chapters),
                    total_chapters=len(chapters),
                    current_step="正在生成M4B文件"
                ))

            # 获取封面图片（如果有）
            cover_image = self._get_cover_image()

            # 生成M4B
            m4b_path = self._generate_m4b(
                book_title,
                book_author,
                chapter_audio_files,
                cover_image
            )

            # 移动到最终输出位置
            shutil.move(str(m4b_path), str(self.output_path))

            return self.output_path

        except Exception as e:
            # 清理工作目录
            shutil.rmtree(self.workspace, ignore_errors=True)
            raise e

    def _get_book_title(self) -> str:
        """获取书名（向后兼容）"""
        return self.book_title

    def _get_book_author(self) -> str:
        """获取作者（向后兼容）"""
        return self.book_author

    def _get_chapters(self, max_chapters: Optional[int] = None) -> List[tuple[str, str]]:
        """获取章节列表（向后兼容）"""
        return self.get_chapters(max_chapters)

    def _convert_chapter_to_audio(self,
                                  chapter_title: str,
                                  chapter_href: str,
                                  chapter_index: int,
                                  voice: Optional[str] = None) -> Optional[Path]:
        """将单个章节转换为音频"""
        try:
            # 提取章节文本
            chapter_text = self.epub_picker.extract_text(chapter_href)

            if not chapter_text.strip():
                return None

            # 生成音频文件路径
            audio_filename = f"chapter_{chapter_index:03d}_{self._sanitize_filename(chapter_title)}.wav"
            audio_path = self.temp_audio_dir / audio_filename

            # 使用ChapterTTS处理章节（包括句子分割等）
            temp_chapter_dir = self.workspace / f"temp_chapter_{chapter_index}"
            temp_chapter_dir.mkdir(exist_ok=True)

            success = self.chapter_tts.process_chapter(
                text=chapter_text,
                output_path=audio_path,
                temp_dir=temp_chapter_dir,
                voice=voice
            )

            if not success:
                raise RuntimeError(f"章节转换失败: {chapter_title}")

            return audio_path

        except Exception as e:
            print(f"转换章节失败 '{chapter_title}': {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不合法字符"""
        import re
        # 替换不合法字符为下划线
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        return sanitized[:50]

    def _get_cover_image(self) -> Optional[Path]:
        """获取封面图片（如果有）"""
        cover_data = self.epub_picker.cover
        if not cover_data:
            return None

        # 保存封面图片
        cover_path = self.workspace / "cover.jpg"
        with open(cover_path, 'wb') as f:
            f.write(cover_data)

        return cover_path

    def _generate_m4b(self,
                     title: str,
                     author: str,
                     audio_files: List[Path],
                     cover_image: Optional[Path]) -> Path:
        """生成M4B文件"""

        # 创建章节信息列表
        chapter_infos = []
        for i, audio_file in enumerate(audio_files):
            if audio_file.exists():
                # 从文件名提取章节标题
                chapter_title = f"第{i+1}章"
                if i < len(self._get_chapters()):
                    nav_title = self._get_chapters()[i][0]
                    chapter_title = nav_title

                chapter_infos.append(ChapterInfo(
                    title=chapter_title,
                    audio_file=audio_file
                ))

        # 生成M4B文件
        m4b_path = self.workspace / "output.m4b"

        self.m4b_generator.generate_m4b(
            title=title,
            _author=author,
            chapters=chapter_infos,
            output_path=m4b_path,
            cover_image=cover_image
        )

        return m4b_path


def convert_epub_to_m4b(epub_path: Path,
                       workspace: Path,
                       output_path: Path,
                       tts_protocol: TextToSpeechProtocol,
                       max_chapters: Optional[int] = None,
                       voice: Optional[str] = None,
                       progress_callback: Optional[Any] = None) -> Path:
    """
    便捷的函数接口，将EPUB转换为M4B

    Args:
        epub_path: EPUB文件路径
        workspace: 工作目录
        output_path: 输出M4B文件路径
        tts_protocol: TTS协议实例
        max_chapters: 最大章节数（可选）
        voice: TTS语音（可选）
        progress_callback: 进度回调函数（可选）

    Returns:
        生成的M4B文件路径
    """
    converter = EpubToSpeechConverter(
        epub_path=epub_path,
        workspace=workspace,
        output_path=output_path,
        tts_protocol=tts_protocol
    )

    return converter.convert(
        max_chapters=max_chapters,
        voice=voice,
        progress_callback=progress_callback
    )