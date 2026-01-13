#!/usr/bin/env python3
import argparse
import contextlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

from .convertor import ConversionProgress, convert_epub_to_m4b
from .tts.protocol import TextToSpeechProtocol


@dataclass
class _ProviderConfig:
    args: list[str]
    env_vars: list[str]
    display_name: str


# Provider configuration mapping
_PROVIDER_CONFIGS: dict[str, _ProviderConfig] = {
    "azure": _ProviderConfig(
        args=["azure_key", "azure_region"],
        env_vars=["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"],
        display_name="Azure TTS",
    ),
    "doubao": _ProviderConfig(
        args=["doubao_token", "doubao_url"],
        env_vars=["DOUBAO_ACCESS_TOKEN", "DOUBAO_BASE_URL"],
        display_name="Doubao TTS",
    ),
}


def progress_callback(progress: ConversionProgress) -> None:
    print(
        f"Progress: {progress.progress:.1f}% - Chapter {progress.current_chapter}/{progress.total_chapters}: {progress.chapter_title}"
    )


def _create_provider(provider_name: str, values: dict[str, Any]) -> tuple[str, TextToSpeechProtocol]:
    """Create TTS provider instance based on provider name and configuration values."""
    if provider_name == "azure":
        from .tts.azure_provider import AzureTextToSpeech

        return provider_name, AzureTextToSpeech(subscription_key=values["azure_key"], region=values["azure_region"])
    elif provider_name == "doubao":
        from .tts.doubao_provider import DoubaoTextToSpeech

        return provider_name, DoubaoTextToSpeech(access_token=values["doubao_token"], base_url=values["doubao_url"])
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def _error_missing_config(provider_name: str, missing_args: list[str]) -> NoReturn:
    """Report error when specified provider has incomplete configuration."""
    config = _PROVIDER_CONFIGS[provider_name]
    print(f"Error: {config.display_name} requires the following parameters:", file=sys.stderr)
    for arg_name in missing_args:
        idx = config.args.index(arg_name)
        env_var = config.env_vars[idx]
        print(f"  --{arg_name.replace('_', '-')} or ${env_var}", file=sys.stderr)
    sys.exit(1)


def _error_no_complete_config(incomplete_providers: dict[str, list[str]]) -> NoReturn:
    """Report error when no provider has complete configuration."""
    print("Error: No complete TTS provider configuration found.", file=sys.stderr)
    print("Missing configurations:", file=sys.stderr)
    for provider_name, missing_args in incomplete_providers.items():
        config = _PROVIDER_CONFIGS[provider_name]
        print(f"\n{config.display_name}:", file=sys.stderr)
        for arg_name in missing_args:
            idx = config.args.index(arg_name)
            env_var = config.env_vars[idx]
            print(f"  --{arg_name.replace('_', '-')} or ${env_var}", file=sys.stderr)
    sys.exit(1)


def _error_multiple_complete_configs(complete_providers: list[str]) -> NoReturn:
    """Report error when multiple providers have complete configuration."""
    print("Error: Multiple TTS providers are configured.", file=sys.stderr)
    print("Please specify which one to use with --provider:", file=sys.stderr)
    for provider_name in complete_providers:
        display_name = _PROVIDER_CONFIGS[provider_name].display_name
        print(f"  --provider {provider_name}  # Use {display_name}", file=sys.stderr)
    sys.exit(1)


def _detect_and_create_tts_provider(args: argparse.Namespace) -> tuple[str, TextToSpeechProtocol]:
    """
    Detect and create TTS provider based on configuration.

    Logic:
    1. If provider is specified, validate its configuration is complete
    2. If provider is not specified, auto-detect which configurations are complete
       - 0 complete: error listing all missing configs
       - 1 complete: auto-use that provider
       - multiple complete: error requiring explicit --provider

    Returns:
        tuple: (provider_name, tts_instance)
    """
    # Step 1: Collect actual configuration values for each provider
    provider_values: dict[str, dict[str, Any]] = {}
    for provider_name, config in _PROVIDER_CONFIGS.items():
        values: dict[str, Any] = {}
        for arg_name, env_var in zip(config.args, config.env_vars):
            # Args override environment variables
            arg_value = getattr(args, arg_name, None)
            env_value = os.environ.get(env_var)
            values[arg_name] = arg_value or env_value
        provider_values[provider_name] = values

    # Step 2: Check which providers have complete configuration
    complete_providers: list[str] = []
    incomplete_providers: dict[str, list[str]] = {}

    for provider_name, values in provider_values.items():
        missing = [k for k, v in values.items() if not v]
        if not missing:
            complete_providers.append(provider_name)
        else:
            incomplete_providers[provider_name] = missing

    # Step 3: Decide behavior based on args.provider
    if args.provider:
        # Provider explicitly specified
        if args.provider in complete_providers:
            return _create_provider(args.provider, provider_values[args.provider])
        else:
            # Configuration incomplete, report error
            missing = incomplete_providers[args.provider]
            _error_missing_config(args.provider, missing)
    else:
        # Provider not specified, auto-detect
        if len(complete_providers) == 0:
            _error_no_complete_config(incomplete_providers)
        elif len(complete_providers) == 1:
            provider_name = complete_providers[0]
            print(f"Auto-detected provider: {_PROVIDER_CONFIGS[provider_name].display_name}")
            return _create_provider(provider_name, provider_values[provider_name])
        else:
            _error_multiple_complete_configs(complete_providers)


def main():
    parser = argparse.ArgumentParser(
        description="Convert EPUB files to audiobooks (M4B format)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using Azure (auto-detected if configured)
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural

  # Using Doubao explicitly
  %(prog)s input.epub output.m4b --provider doubao --voice zh_male_lengkugege_emo_v2_mars_bigtts

  # Limit chapters
  %(prog)s input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --max-chapters 5
        """,
    )

    parser.add_argument("epub_path", type=str, help="Input EPUB file path")

    parser.add_argument("output_path", type=str, help="Output M4B file path")

    parser.add_argument(
        "--provider",
        type=str,
        choices=list(_PROVIDER_CONFIGS.keys()),
        help="TTS provider to use (auto-detected if not specified)",
    )

    parser.add_argument("--voice", type=str, help="TTS voice name (provider-specific)")

    parser.add_argument("--max-chapters", type=int, help="Maximum number of chapters to convert (optional)")

    parser.add_argument("--workspace", type=str, help="Workspace directory path (default: system temp directory)")

    # Azure TTS options
    azure_group = parser.add_argument_group("Azure TTS options")
    azure_group.add_argument(
        "--azure-key",
        type=str,
        default=os.environ.get("AZURE_SPEECH_KEY"),
        help="Azure Speech Service Key (or set AZURE_SPEECH_KEY env var)",
    )
    azure_group.add_argument(
        "--azure-region",
        type=str,
        default=os.environ.get("AZURE_SPEECH_REGION"),
        help="Azure Speech Service region (or set AZURE_SPEECH_REGION env var)",
    )

    # Doubao TTS options
    doubao_group = parser.add_argument_group("Doubao TTS options")
    doubao_group.add_argument(
        "--doubao-token",
        type=str,
        default=os.environ.get("DOUBAO_ACCESS_TOKEN"),
        help="Doubao access token (or set DOUBAO_ACCESS_TOKEN env var)",
    )
    doubao_group.add_argument(
        "--doubao-url",
        type=str,
        default=os.environ.get("DOUBAO_BASE_URL"),
        help="Doubao API base URL (or set DOUBAO_BASE_URL env var)",
    )

    parser.add_argument("--quiet", action="store_true", help="Quiet mode, do not show progress information")

    args = parser.parse_args()

    epub_path = Path(args.epub_path)
    if not epub_path.exists():
        print(f"Error: EPUB file does not exist: {epub_path}", file=sys.stderr)
        sys.exit(1)

    if not epub_path.suffix.lower() == ".epub":
        print(f"Error: Input file must be in EPUB format: {epub_path}", file=sys.stderr)
        sys.exit(1)

    # Create workspace context manager
    if args.workspace:
        workspace_path = Path(args.workspace)
        workspace_path.mkdir(parents=True, exist_ok=True)
        workspace_ctx = contextlib.nullcontext(workspace_path)
    else:
        workspace_ctx = tempfile.TemporaryDirectory(prefix="epub2speech_")

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with workspace_ctx as workspace_dir:
            workspace = Path(workspace_dir)

            # Detect and create TTS provider
            provider_name, tts_provider = _detect_and_create_tts_provider(args)

            print(f"Starting conversion: {epub_path.name}")
            print(f"Output file: {output_path}")
            print(f"Workspace: {workspace}")
            print(f"TTS Provider: {_PROVIDER_CONFIGS[provider_name].display_name}")
            if args.voice:
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
                progress_callback=None if args.quiet else progress_callback,
            )
            if result_path:
                print(f"\nConversion complete! Output file: {result_path}")
                print(f"File size: {result_path.stat().st_size / (1024 * 1024):.1f} MB")
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
