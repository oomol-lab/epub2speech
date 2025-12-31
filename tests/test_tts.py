#!/usr/bin/env python3
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech.tts.azure_provider import AzureTextToSpeech
from tests.utils.config import TTSConfig


class TestTTSIntegration(unittest.TestCase):
    """Test cases for TTS integration"""

    def setUp(self):
        """Set up test configuration"""
        self.config_path = Path(__file__).parent / "tts_config.json"
        if not self.config_path.exists():
            self.skipTest("TTS config file not found")

        config = TTSConfig(self.config_path)
        self.assertTrue(config.validate_config())

        azure_config = config.get_azure_config()
        self.tts = AzureTextToSpeech(subscription_key=azure_config["subscription_key"], region=azure_config["region"])

        self.output_dir = Path(__file__).parent / "temp" / "tts_outputs"
        self.output_dir.mkdir(exist_ok=True)

        for old_file in self.output_dir.glob("*.wav"):
            old_file.unlink()

    def test_voice_parameter_functionality(self):
        """Test voice parameter with different languages and voices"""
        test_cases = [
            {"voice": "zh-CN-XiaochenNeural", "text": "这是一个中文语音测试", "filename": "chinese_test"},
            {"voice": "en-US-BrianNeural", "text": "This is an English voice test", "filename": "english_test"},
        ]
        for case in test_cases:
            output_path = self.output_dir / f"{case['filename']}.wav"

            self.tts.convert_text_to_audio(text=case["text"], output_path=output_path, voice=case["voice"])
            self.assertTrue(output_path.exists())
            file_size = output_path.stat().st_size
            self.assertGreater(file_size, 1000, f"Audio file too small for {case['voice']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
