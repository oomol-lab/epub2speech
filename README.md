<div align=center>
  <h1>EPUB to Speech</h1>
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

Convert an EPUB file to audiobook (provider auto-detected):

```bash
# Set up your TTS provider credentials first (see Quick Start section)
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

1. Create an Azure account at https://azure.microsoft.com
2. Create a Speech Service resource in Azure Portal
3. Get your subscription key and region from the Azure dashboard
4. Set environment variables:

```bash
export AZURE_SPEECH_KEY="your-subscription-key"
export AZURE_SPEECH_REGION="your-region"

epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
```

### Option 2: Using Doubao TTS

1. Get your Doubao access token and API base URL
2. Set environment variables:

```bash
export DOUBAO_ACCESS_TOKEN="your-access-token"
export DOUBAO_BASE_URL="your-api-base-url"

epub2speech input.epub output.m4b --voice zh_male_lengkugege_emo_v2_mars_bigtts
```

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

You can pass Azure credentials via command-line arguments instead of environment variables:

```bash
epub2speech input.epub output.m4b \
  --voice zh-CN-XiaoxiaoNeural \
  --azure-key YOUR_KEY \
  --azure-region YOUR_REGION
```

Available Azure voices: [Azure Neural Voices](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#neural-voices)

### Doubao TTS Configuration

You can pass Doubao credentials via command-line arguments:

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

- [Azure Cognitive Services](https://azure.microsoft.com/services/cognitive-services/) for Azure TTS provider
- [Doubao](https://www.volcengine.com/product/doubao) for Doubao TTS provider
- [ebooklib](https://github.com/aerkalov/ebooklib) for EPUB parsing
- [FFmpeg](https://ffmpeg.org/) for audio processing
- [spaCy](https://spacy.io/) for natural language processing

## Support

For issues and questions:
1. Check existing GitHub issues
2. Create a new issue with detailed information
3. Include EPUB file samples if relevant (ensure no copyright restrictions)”，“file_path”: