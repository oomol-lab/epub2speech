<div align=center>
  <h1>EPUB to Speech</h1>
  <p>
    <a href="https://github.com/oomol-lab/epub2speech/actions/workflows/merge-build.yml" target="_blank"><img src="https://img.shields.io/github/actions/workflow/status/oomol-lab/epub2speech/merge-build.yml?branch=main&label=build" alt="build" /></a>
    <a href="https://pypi.org/project/epub2speech/" target="_blank"><img src="https://img.shields.io/badge/pip_install-epub2speech-blue" alt="pip install epub2speech" /></a>
    <a href="https://pypi.org/project/epub2speech/" target="_blank"><img src="https://img.shields.io/pypi/v/epub2speech.svg" alt="pypi epub2speech" /></a>
    <a href="https://pypi.org/project/epub2speech/" target="_blank"><img src="https://img.shields.io/pypi/pyversions/epub2speech.svg" alt="python versions" /></a>
    <a href="https://github.com/oomol-lab/epub2speech/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/oomol-lab/epub2speech" alt="license" /></a>
  </p>
  <p>English | <a href="./README_zh-CN.md">中文</a></p>
</div>

Convert EPUB e-books into high-quality audiobooks using multiple Text-to-Speech providers.

## Features

- **📚 EPUB Support**: Compatible with EPUB 2 and EPUB 3 formats
- **🎙️ Multiple TTS Providers**: Supports Azure and Doubao TTS services
- **🔄 Auto-Detection**: Automatically detects configured provider
- **🌍 Multi-Language Support**: Supports various languages and voices
- **📱 M4B Output**: Generates standard M4B audiobook format with chapter navigation
- **🔧 CLI Interface**: Easy-to-use command-line tool with progress tracking

## Basic Usage

```bash
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
```

## Installation

### Prerequisites

- Python 3.11 or higher
- FFmpeg (for audio processing)
- TTS provider credentials (Azure or Doubao)

### Install Dependencies

```bash
# Install Python dependencies
pip install poetry
poetry install

# Install FFmpeg
# macOS: brew install ffmpeg
# Ubuntu/Debian: sudo apt install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html
```

## Quick Start

### Option 1: Using Azure TTS

Set environment variables and run:

```bash
export AZURE_SPEECH_KEY="your-subscription-key"
export AZURE_SPEECH_REGION="your-region"

epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
```

**Where to get credentials:**
- Create an Azure account at https://azure.microsoft.com
- Create a Speech Service resource in Azure Portal
- Get your subscription key and region from the dashboard

**Available voices:**
- Voice list: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#voice-styles-and-roles
- Voice gallery (preview): https://speech.microsoft.com/portal/voicegallery

### Option 2: Using Doubao TTS

Set environment variables and run:

```bash
export DOUBAO_ACCESS_TOKEN="your-access-token"
export DOUBAO_BASE_URL="your-api-base-url"

epub2speech input.epub output.m4b --voice zh_male_lengkugege_emo_v2_mars_bigtts
```

**Where to get credentials:**
- Get your Doubao access token and API base URL from Volcengine console

**Available voices:** https://www.volcengine.com/docs/6561/1257544
_(Find voice IDs in the Doubao TTS documentation)_

### Provider Auto-Detection

If you have configured only one provider, it will be automatically detected and used. If multiple providers are configured, specify which one to use:

```bash
# Explicitly use Azure
epub2speech input.epub output.m4b --provider azure --voice zh-CN-XiaoxiaoNeural

# Explicitly use Doubao
epub2speech input.epub output.m4b --provider doubao --voice zh_male_lengkugege_emo_v2_mars_bigtts
```

## Advanced Options

### General Options

```bash
# Limit to first 5 chapters
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --max-chapters 5

# Use custom workspace directory
epub2speech input.epub output.m4b --voice zh-CN-YunxiNeural --workspace /tmp/my-workspace

# Quiet mode (no progress output)
epub2speech input.epub output.m4b --voice ja-JP-NanamiNeural --quiet
```

### Azure TTS Configuration

Pass credentials via command-line arguments:

```bash
epub2speech input.epub output.m4b \
  --voice zh-CN-XiaoxiaoNeural \
  --azure-key YOUR_KEY \
  --azure-region YOUR_REGION
```

### Doubao TTS Configuration

Pass credentials via command-line arguments:

```bash
epub2speech input.epub output.m4b \
  --voice zh_male_lengkugege_emo_v2_mars_bigtts \
  --doubao-token YOUR_TOKEN \
  --doubao-url YOUR_BASE_URL
```

## How It Works

1. **EPUB Parsing**: Extracts text content and metadata from EPUB files
2. **Chapter Detection**: Identifies chapters using EPUB navigation data
3. **Text Processing**: Cleans and segments text for optimal speech synthesis
4. **Audio Generation**: Converts text to speech using your chosen TTS provider
5. **M4B Creation**: Combines audio files with chapter metadata into M4B format

## Development

### Using as a Library

You can integrate epub2speech into your own Python application:

```python
from pathlib import Path
from epub2speech import convert_epub_to_m4b, ConversionProgress
from epub2speech.tts.azure_provider import AzureTextToSpeech
# Or use: from epub2speech.tts.doubao_provider import DoubaoTextToSpeech

# Initialize TTS provider
tts = AzureTextToSpeech(
    subscription_key="your-key",
    region="your-region"
)

# Optional: Define progress callback
def on_progress(progress: ConversionProgress):
    print(f"{progress.progress:.1f}% - Chapter {progress.current_chapter}/{progress.total_chapters}")

# Convert EPUB to M4B
result = convert_epub_to_m4b(
    epub_path=Path("input.epub"),
    workspace=Path("./workspace"),
    output_path=Path("output.m4b"),
    tts_protocol=tts,
    voice="zh-CN-XiaoxiaoNeural",
    max_chapters=None,  # Optional: limit chapters
    progress_callback=on_progress  # Optional
)

if result:
    print(f"Success: {result}")
```

### Running Tests

```bash
python test.py
```

Run specific test modules:

```bash
python test.py --test test_epub_picker
python test.py --test test_tts
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [ebooklib](https://github.com/aerkalov/ebooklib) for EPUB parsing
- [FFmpeg](https://ffmpeg.org/) for audio processing
- [spaCy](https://spacy.io/) for natural language processing

## Support

For issues and questions:
1. Check existing GitHub issues
2. Create a new issue with detailed information
3. Include EPUB file samples if relevant (ensure no copyright restrictions)”，“file_path”: