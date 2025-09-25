<div align=center>
  <h1>EPUB to Speech</h1>
  <p>English | <a href="./README_zh-CN.md">中文</a></p>
</div>

Convert EPUB e-books into high-quality audiobooks using Azure Text-to-Speech technology.

## Features

- **📚 EPUB Support**: Compatible with EPUB 2 and EPUB 3 formats
- **🎙️ High-Quality TTS**: Uses Azure Cognitive Services Speech for natural voice synthesis
- **🌍 Multi-Language Support**: Supports various languages and voices via Azure TTS
- **📱 M4B Output**: Generates standard M4B audiobook format with chapter navigation
- **🔧 CLI Interface**: Easy-to-use command-line tool with progress tracking

## Basic Usage

Convert an EPUB file to audiobook:

```bash
epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural --azure-key YOUR_KEY --azure-region YOUR_REGION
```

## Installation

### Prerequisites

- Python 3.11 or higher
- FFmpeg (for audio processing)
- Azure Speech Service credentials

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

### Azure Speech Service Setup

1. Create an Azure account at https://azure.microsoft.com
2. Create a Speech Service resource in Azure Portal
3. Get your subscription key and region from the Azure dashboard

## Quick Start

### Environment Variables

Set your Azure credentials as environment variables:

```bash
export AZURE_SPEECH_KEY="your-subscription-key"
export AZURE_SPEECH_REGION="your-region"

epub2speech input.epub output.m4b --voice zh-CN-XiaoxiaoNeural
```

### Advanced Options

```bash
# Limit to first 5 chapters
epub2speech input.epub output.m4b --voice en-US-AriaNeural --max-chapters 5

# Use custom workspace directory
epub2speech input.epub output.m4b --voice zh-CN-YunxiNeural --workspace /tmp/my-workspace

# Quiet mode (no progress output)
epub2speech input.epub output.m4b --voice ja-JP-NanamiNeural --quiet
```

## Available Voices

For a complete list, see [Azure Neural Voices](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support#neural-voices).

## How It Works

1. **EPUB Parsing**: Extracts text content and metadata from EPUB files
2. **Chapter Detection**: Identifies chapters using EPUB navigation data
3. **Text Processing**: Cleans and segments text for optimal speech synthesis
4. **Audio Generation**: Converts text to speech using Azure TTS
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

- [Azure Cognitive Services](https://azure.microsoft.com/services/cognitive-services/) for text-to-speech technology
- [ebooklib](https://github.com/aerkalov/ebooklib) for EPUB parsing
- [FFmpeg](https://ffmpeg.org/) for audio processing
- [spaCy](https://spacy.io/) for natural language processing

## Support

For issues and questions:
1. Check existing GitHub issues
2. Create a new issue with detailed information
3. Include EPUB file samples if relevant (ensure no copyright restrictions)”，“file_path”: