#!/usr/bin/env python3
"""
EPUB转M4B转换器使用示例
"""

from pathlib import Path
from .convertor import convert_epub_to_m4b, ConversionProgress
from .tts.azure_provider import AzureTextToSpeech


def progress_callback(progress: ConversionProgress):
    """简单的进度回调函数"""
    print(f"进度: {progress.progress_percentage:.1f}% - {progress.current_step}")
    if progress.chapter_title:
        print(f"  当前章节: {progress.chapter_title}")


def example_conversion():
    """转换示例"""
    # EPUB文件路径
    epub_path = Path("tests/assets/明朝那些事儿.epub")

    # 工作目录（用于存放临时文件）
    workspace = Path("temp_workspace")

    # 输出M4B文件路径
    output_path = Path("output/明朝那些事儿.m4b")

    # 创建输出目录
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建Azure TTS实例（需要配置）
    # 注意：需要先设置Azure配置
    tts_protocol = AzureTextToSpeech()

    # 检查TTS配置
    if not tts_protocol.validate_config():
        print("错误: TTS配置无效，请先配置Azure语音服务凭据")
        return

    try:
        # 执行转换
        result_path = convert_epub_to_m4b(
            epub_path=epub_path,
            workspace=workspace,
            output_path=output_path,
            tts_protocol=tts_protocol,
            max_chapters=4,  # 只转换前4章作为示例
            voice="zh-CN-XiaoxiaoNeural",  # 使用中文语音
            progress_callback=progress_callback
        )

        print(f"转换完成！M4B文件已保存至: {result_path}")
        print(f"文件大小: {result_path.stat().st_size:,} 字节")

    except Exception as e:
        print(f"转换失败: {e}")
        raise
    finally:
        # 清理工作目录（可选）
        # import shutil
        # shutil.rmtree(workspace, ignore_errors=True)
        pass


def example_with_custom_converter():
    """使用自定义转换器类的示例"""
    from .convertor import EpubToSpeechConverter

    # 创建转换器实例
    converter = EpubToSpeechConverter(
        epub_path=Path("tests/assets/明朝那些事儿.epub"),
        workspace=Path("temp_workspace"),
        output_path=Path("output/明朝那些儿.m4b"),
        tts_protocol=AzureTextToSpeech()
    )

    # 执行转换
    result = converter.convert(
        max_chapters=2,  # 只转换前2章
        voice="zh-CN-XiaoxiaoNeural",
        progress_callback=progress_callback
    )

    print(f"转换完成: {result}")


if __name__ == "__main__":
    print("开始EPUB转M4B转换示例...")
    example_conversion()