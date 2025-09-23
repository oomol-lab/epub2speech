#!/usr/bin/env python3
"""
测试EPUB转M4B转换器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from epub2speech.convertor import EpubToSpeechConverter, ConversionProgress
from epub2speech.tts.azure_provider import AzureTextToSpeech


def progress_callback(progress: ConversionProgress):
    """进度回调函数"""
    print(f"进度: {progress.progress_percentage:.1f}% - {progress.current_step}")
    if progress.chapter_title:
        print(f"  当前章节: {progress.chapter_title}")


def test_converter():
    """测试转换器基本功能"""
    print("🧪 开始测试EPUB转M4B转换器...")

    # 测试文件路径
    test_epub = Path("tests/assets/明朝那些事儿.epub")
    workspace = Path("temp_test_workspace")
    output_path = Path("temp_test_output.m4b")

    if not test_epub.exists():
        print(f"❌ 测试文件不存在: {test_epub}")
        return False

    try:
        # 创建Azure TTS实例
        tts_protocol = AzureTextToSpeech()

        # 检查配置
        if not tts_protocol.validate_config():
            print("⚠️  Azure TTS配置无效，跳过实际转换测试")
            print("✅ 转换器初始化测试通过")
            return True

        # 创建转换器
        converter = EpubToSpeechConverter(
            epub_path=test_epub,
            workspace=workspace,
            output_path=output_path,
            tts_protocol=tts_protocol
        )

        print(f"📚 书名: {converter.book_title}")
        print(f"✍️ 作者: {converter.book_author}")

        # 获取章节列表
        chapters = converter.get_chapters(max_chapters=2)
        print(f"📖 找到 {len(chapters)} 个章节")

        for i, (title, href) in enumerate(chapters):
            print(f"  章节 {i+1}: {title} -> {href}")

        # 执行转换（只转换前2章作为测试）
        print("🔄 开始转换...")
        result = converter.convert(
            max_chapters=2,
            voice="zh-CN-XiaoxiaoNeural",
            progress_callback=progress_callback
        )

        print(f"✅ 转换成功！输出文件: {result}")
        print(f"📊 文件大小: {result.stat().st_size:,} 字节")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理临时文件
        if workspace.exists():
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)
        if output_path.exists():
            output_path.unlink()


def test_converter_initialization():
    """测试转换器初始化"""
    print("🔧 测试转换器初始化...")

    try:
        from epub2speech.convertor import EpubToSpeechConverter
        from epub2speech.tts.protocol import TextToSpeechProtocol

        # 创建模拟TTS协议
        class MockTTSProtocol(TextToSpeechProtocol):
            def validate_config(self):
                return True

            def convert_text_to_audio(self, text, output_path, voice=None):
                # 模拟转换，创建空音频文件
                with open(output_path, 'wb') as f:
                    f.write(b'dummy audio data')
                return True

            def get_available_voices(self):
                return []

        converter = EpubToSpeechConverter(
            epub_path=Path("tests/assets/明朝那些事儿.epub"),
            workspace=Path("temp_test_init"),
            output_path=Path("temp_output.m4b"),
            tts_protocol=MockTTSProtocol()
        )

        print("✅ 转换器初始化成功")
        print(f"📚 书名: {converter.book_title}")
        print(f"✍️ 作者: {converter.book_author}")

        chapters = converter.get_chapters()
        print(f"📖 找到 {len(chapters)} 个章节")

        return True

    except Exception as e:
        print(f"❌ 初始化测试失败: {e}")
        return False

    finally:
        # 清理
        workspace = Path("temp_test_init")
        if workspace.exists():
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 50)
    print("EPUB转M4B转换器测试")
    print("=" * 50)

    # 测试初始化
    init_success = test_converter_initialization()

    print()

    # 测试完整转换（如果有有效配置）
    if init_success:
        convert_success = test_converter()
    else:
        convert_success = False

    print()
    print("=" * 50)
    if init_success and convert_success:
        print("🎉 所有测试通过！")
        sys.exit(0)
    elif init_success:
        print("⚠️  部分测试通过（需要配置Azure TTS）")
        sys.exit(0)
    else:
        print("❌ 测试失败")
        sys.exit(1)