#!/usr/bin/env python3
import sys
import os
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech.convertor import convert_epub_to_m4b
from epub2speech.tts.azure_provider import AzureTextToSpeech
from tests.utils.config import TTSConfig


class TestM4BGeneration(unittest.TestCase):
    """Test cases for M4B audiobook generation"""

    def test_epub_to_m4b_conversion(self):
        """Test complete EPUB to M4B conversion using real EPUB file"""
        config_path = Path(__file__).parent / "tts_config.json"

        if not config_path.exists():
            print("⚠️  TTS config file not found, skipping M4B generation test")
            print("To run TTS tests locally, copy tts_config.json.template to tts_config.json")
            print("and fill in your Azure Speech credentials")
            self.skipTest("TTS config file not found")

        config = TTSConfig(config_path)
        self.assertTrue(config.validate_config(), "TTS configuration is invalid")

        azure_config = config.get_azure_config()
        self.assertIsNotNone(azure_config, "No Azure configuration found in config file")

        subscription_key = azure_config["subscription_key"]
        region = azure_config["region"]

        self.assertIsNotNone(subscription_key, "Azure configuration missing subscription_key")
        self.assertIsNotNone(region, "Azure configuration missing region")

        # Create TTS provider
        tts_provider = AzureTextToSpeech(
            subscription_key=subscription_key,
            region=region
        )

        # Use real EPUB file from tests/assets
        epub_path = Path(__file__).parent / "assets" / "明朝那些事儿.epub"
        self.assertTrue(epub_path.exists(), f"EPUB file not found: {epub_path}")

        # Setup output paths
        output_dir = Path(__file__).parent / "temp"
        temp_dir = output_dir / "m4b_test_workspace"
        output_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)

        output_path = output_dir / "test_output.m4b"

        # Convert EPUB to M4B using the full conversion pipeline
        result_path = convert_epub_to_m4b(
            epub_path=epub_path,
            workspace=temp_dir,
            output_path=output_path,
            tts_protocol=tts_provider,
            voice="zh-CN-XiaochenNeural",
            max_chapters=2  # Limit to first 2 chapters for faster testing
        )

        # Verify conversion was successful
        self.assertIsNotNone(result_path, "M4B conversion returned None")
        self.assertTrue(result_path and result_path.exists(), "M4B file was not created")

        # Verify file size is reasonable
        if result_path:
            file_size = result_path.stat().st_size
            self.assertGreater(file_size, 50000, "M4B file seems too small (< 50KB)")

            # Verify it's actually an M4B file (should have M4B extension)
            self.assertEqual(result_path.suffix, ".m4b", "Output file should have .m4b extension")

    def test_epub_to_m4b_with_different_voices(self):
        """Test M4B generation with different voice parameters"""
        config_path = Path(__file__).parent / "tts_config.json"

        if not config_path.exists():
            self.skipTest("TTS config file not found")

        config = TTSConfig(config_path)
        azure_config = config.get_azure_config()

        tts_provider = AzureTextToSpeech(
            subscription_key=azure_config["subscription_key"],
            region=azure_config["region"]
        )

        epub_path = Path(__file__).parent / "assets" / "明朝那些事儿.epub"
        output_dir = Path(__file__).parent / "temp"
        temp_base_dir = output_dir / "m4b_voices_workspace"
        output_dir.mkdir(exist_ok=True)
        temp_base_dir.mkdir(exist_ok=True)

        # Test with different voices
        test_voices = [
            "zh-CN-XiaochenNeural",
            "zh-CN-XiaoxiaoNeural"
        ]

        for voice in test_voices:
            with self.subTest(voice=voice):
                output_path = output_dir / f"test_{voice.replace('-', '_')}.m4b"

                result_path = convert_epub_to_m4b(
                    epub_path=epub_path,
                    workspace=temp_base_dir / voice,
                    output_path=output_path,
                    tts_protocol=tts_provider,
                    voice=voice,
                    max_chapters=1  # Just first chapter for speed
                )

                self.assertIsNotNone(result_path, f"M4B conversion failed for voice: {voice}")
                self.assertTrue(result_path and result_path.exists(), f"M4B file not created for voice: {voice}")

                if result_path:
                    file_size = result_path.stat().st_size
                    self.assertGreater(file_size, 10000, f"M4B file too small for voice: {voice}")


if __name__ == "__main__":
    unittest.main(verbosity=2)