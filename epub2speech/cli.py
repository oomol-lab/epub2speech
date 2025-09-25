#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

from .convertor import convert_epub_to_m4b, ConversionProgress


def progress_callback(progress: ConversionProgress) -> None:
    print(f"Progress: {progress.progress:.1f}% - Chapter {progress.current_chapter}/{progress.total_chapters}: {progress.chapter_title}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert EPUB files to audiobooks (M4B format)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --max-chapters 5
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --workspace /tmp/workspace
        """
    )

    parser.add_argument(
        "epub_path",
        type=str,
        help="Input EPUB file path"
    )

    parser.add_argument(
        "output_path",
        type=str,
        help="Output M4B file path"
    )

    parser.add_argument(
        "--voice",
        type=str,
        default="zh-CN-XiaoxiaoNeural",
        help="TTS voice name (default: zh-CN-XiaoxiaoNeural)"
    )

    parser.add_argument(
        "--max-chapters",
        type=int,
        help="Maximum number of chapters to convert (optional)"
    )

    parser.add_argument(
        "--workspace",
        type=str,
        help="Workspace directory path (default: system temp directory)"
    )

    parser.add_argument(
        "--azure-key",
        type=str,
        default=os.environ.get("AZURE_SPEECH_KEY"),
        help="Azure Speech Service Key (can also be set via AZURE_SPEECH_KEY environment variable)"
    )

    parser.add_argument(
        "--azure-region",
        type=str,
        default=os.environ.get("AZURE_SPEECH_REGION"),
        help="Azure Speech Service region (can also be set via AZURE_SPEECH_REGION environment variable)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode, do not show progress information"
    )

    args = parser.parse_args()

    epub_path = Path(args.epub_path)
    if not epub_path.exists():
        print(f"Error: EPUB file does not exist: {epub_path}", file=sys.stderr)
        sys.exit(1)

    if not epub_path.suffix.lower() == '.epub':
        print(f"Error: Input file must be in EPUB format: {epub_path}", file=sys.stderr)
        sys.exit(1)

    if not args.azure_key or not args.azure_region:
        print("Error: Azure Speech Service credentials must be provided", file=sys.stderr)
        print("Please provide via --azure-key and --azure-region parameters, or set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables", file=sys.stderr)
        sys.exit(1)

    if args.workspace:
        workspace = Path(args.workspace)
        workspace.mkdir(parents=True, exist_ok=True)
    else:
        import tempfile
        workspace = Path(tempfile.mkdtemp(prefix="epub2speech_"))

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from .tts.azure_provider import AzureTextToSpeech
        tts_provider = AzureTextToSpeech(
            subscription_key=args.azure_key,
            region=args.azure_region,
            default_voice=args.voice
        )

        print(f"Starting conversion: {epub_path.name}")
        print(f"Output file: {output_path}")
        print(f"Workspace: {workspace}")
        print(f"Using voice: {args.voice}")
        if args.max_chapters:
            print(f"Maximum chapters: {args.max_chapters}")
        print()

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
            print(f"\nConversion complete! Output file: {result_path}")
            print(f"File size: {result_path.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("\nConversion failed: no output file generated", file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nConversion interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nConversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()