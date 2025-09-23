#!/usr/bin/env python3
"""
EPUB to Speech Converter Example

This script demonstrates how to convert EPUB book content to audio files
using Azure Text-to-Speech service.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from epub2speech import EpubPicker, create_azure_tts_from_config
from epub2speech.tts.config import TTSConfig


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def convert_epub_to_speech(
    epub_path: Path,
    output_dir: Path,
    config_path: Path = None,
    max_chapters: int = None,
    voice: str = None
) -> bool:
    """
    Convert EPUB book to speech audio files

    Args:
        epub_path: Path to EPUB file
        output_dir: Directory to save audio files
        config_path: Optional path to TTS config file
        max_chapters: Maximum number of chapters to convert (for testing)
        voice: Optional voice override

    Returns:
        True if successful, False otherwise
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"🎯 Converting EPUB to speech: {epub_path.name}")

    # Load TTS configuration
    config = TTSConfig(config_path)
    if not config.validate_config():
        logger.error("❌ TTS configuration is invalid")
        logger.info("Please copy azure_tts_config.template.json to azure_tts_config.json")
        logger.info("and fill in your Azure Speech credentials")
        return False

    # Create TTS instance
    tts = create_azure_tts_from_config(config_path)
    if not tts.validate_config():
        logger.error("❌ Azure TTS configuration is invalid")
        return False

    logger.info("✅ Azure TTS configured successfully")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create EPUB picker
        picker = EpubPicker(epub_path)
        logger.info(f"📚 Loaded EPUB: {picker.meta_titles[0] if picker.meta_titles else 'Unknown Title'}")

        # Get navigation items (chapters)
        nav_items = list(picker.get_nav_items())
        if not nav_items:
            logger.error("❌ No chapters found in EPUB")
            return False

        logger.info(f"📖 Found {len(nav_items)} chapters")

        # Process chapters
        success_count = 0
        total_chapters = min(len(nav_items), max_chapters) if max_chapters else len(nav_items)

        for i, (chapter_title, href) in enumerate(nav_items[:total_chapters]):
            logger.info(f"\n🎤 Processing chapter {i+1}/{total_chapters}: {chapter_title}")

            try:
                # Extract text from chapter
                text = picker.extract_text(href)
                if not text or len(text.strip()) < 10:
                    logger.warning(f"⚠️  Chapter '{chapter_title}' has insufficient text")
                    continue

                logger.info(f"📄 Extracted {len(text)} characters")

                # Create safe filename
                safe_title = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_title = safe_title[:50]  # Limit filename length
                audio_filename = f"{i+1:03d}_{safe_title}.wav"
                audio_path = output_dir / audio_filename

                # Convert text to speech
                logger.info(f"🎙️  Converting to speech...")
                success = tts.convert_text_to_audio(
                    text=text,
                    output_path=audio_path,
                    voice=voice
                )

                if success:
                    logger.info(f"✅ Audio saved: {audio_filename}")
                    success_count += 1
                else:
                    logger.error(f"❌ Failed to convert chapter: {chapter_title}")

            except Exception as e:
                logger.error(f"❌ Error processing chapter '{chapter_title}': {e}")
                continue

        logger.info(f"\n🎉 Conversion completed!")
        logger.info(f"✅ Successfully converted {success_count}/{total_chapters} chapters")
        logger.info(f"📁 Audio files saved to: {output_dir.absolute()}")

        return success_count > 0

    except Exception as e:
        logger.error(f"❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    # Example usage
    epub_path = Path("tests/assets/The little prince.epub")  # Default test file
    output_dir = Path("output_audio")

    # You can override with command line arguments
    if len(sys.argv) > 1:
        epub_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])

    # Convert EPUB to speech
    success = convert_epub_to_speech(
        epub_path=epub_path,
        output_dir=output_dir,
        max_chapters=3,  # Limit to first 3 chapters for testing
        voice="zh-CN-XiaoxiaoNeural"
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()