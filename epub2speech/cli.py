#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

from .convertor import convert_epub_to_m4b, ConversionProgress
from .tts import AzureTextToSpeech


def progress_callback(progress: ConversionProgress) -> None:
    """进度回调函数"""
    print(f"进度: {progress.progress:.1f}% - 章节 {progress.current_chapter}/{progress.total_chapters}: {progress.chapter_title}")


def main():
    """CLI 主函数"""
    parser = argparse.ArgumentParser(
        description="将 EPUB 文件转换为有声电子书 (M4B 格式)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --max-chapters 5
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --workspace /tmp/workspace
        """
    )

    parser.add_argument(
        "epub_path",
        type=str,
        help="输入的 EPUB 文件路径"
    )

    parser.add_argument(
        "output_path",
        type=str,
        help="输出的 M4B 文件路径"
    )

    parser.add_argument(
        "--voice",
        type=str,
        default="zh-CN-XiaoxiaoNeural",
        help="TTS 语音名称 (默认: zh-CN-XiaoxiaoNeural)"
    )

    parser.add_argument(
        "--max-chapters",
        type=int,
        help="最大转换章节数 (可选)"
    )

    parser.add_argument(
        "--workspace",
        type=str,
        help="工作目录路径 (默认: 系统临时目录)"
    )

    parser.add_argument(
        "--azure-key",
        type=str,
        default=os.environ.get("AZURE_SPEECH_KEY"),
        help="Azure Speech Service Key (也可以通过 AZURE_SPEECH_KEY 环境变量设置)"
    )

    parser.add_argument(
        "--azure-region",
        type=str,
        default=os.environ.get("AZURE_SPEECH_REGION"),
        help="Azure Speech Service 区域 (也可以通过 AZURE_SPEECH_REGION 环境变量设置)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式，不显示进度信息"
    )

    args = parser.parse_args()

    # 验证输入文件存在
    epub_path = Path(args.epub_path)
    if not epub_path.exists():
        print(f"错误: EPUB 文件不存在: {epub_path}", file=sys.stderr)
        sys.exit(1)

    if not epub_path.suffix.lower() == '.epub':
        print(f"错误: 输入文件必须是 EPUB 格式: {epub_path}", file=sys.stderr)
        sys.exit(1)

    # 验证 Azure 凭据
    if not args.azure_key or not args.azure_region:
        print("错误: 必须提供 Azure Speech Service 凭据", file=sys.stderr)
        print("请通过 --azure-key 和 --azure-region 参数，或设置 AZURE_SPEECH_KEY 和 AZURE_SPEECH_REGION 环境变量", file=sys.stderr)
        sys.exit(1)

    # 创建工作目录
    if args.workspace:
        workspace = Path(args.workspace)
        workspace.mkdir(parents=True, exist_ok=True)
    else:
        import tempfile
        workspace = Path(tempfile.mkdtemp(prefix="epub2speech_"))

    # 创建输出目录
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 创建 Azure TTS 提供商
        tts_provider = AzureTextToSpeech(
            subscription_key=args.azure_key,
            region=args.azure_region,
            default_voice=args.voice
        )

        print(f"开始转换: {epub_path.name}")
        print(f"输出文件: {output_path}")
        print(f"工作目录: {workspace}")
        print(f"使用语音: {args.voice}")
        if args.max_chapters:
            print(f"最大章节数: {args.max_chapters}")
        print()

        # 执行转换
        result_path = convert_epub_to_m4b(
            epub_path=epub_path,
            workspace=workspace,
            output_path=output_path,
            tts_protocol=tts_provider,
            voice=args.voice,
            max_chapters=args.max_chapters,
            progress_callback=None if args.quiet else progress_callback
        )
        if result_path:
            print(f"\n转换完成! 输出文件: {result_path}")
            print(f"文件大小: {result_path.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("\n转换失败: 没有生成输出文件", file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n转换被用户中断", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n转换失败: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # 清理临时工作目录
        if not args.workspace and workspace.exists():
            import shutil
            try:
                shutil.rmtree(workspace)
            except Exception:
                pass  # 忽略清理错误


if __name__ == "__main__":
    main()