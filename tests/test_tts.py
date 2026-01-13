#!/usr/bin/env python3
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from tests.utils.config import TTSConfig


def create_tts_provider(provider_name: str, config: dict):
    """Factory function to create TTS provider instances"""
    if provider_name == "azure":
        from epub2speech.tts.azure_provider import AzureTextToSpeech

        return AzureTextToSpeech(subscription_key=config["azure_key"], region=config["azure_region"])
    elif provider_name == "doubao":
        from epub2speech.tts.doubao_provider import DoubaoTextToSpeech

        return DoubaoTextToSpeech(access_token=config["doubao_token"], base_url=config["doubao_url"])
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def get_test_cases_for_provider(provider_name: str):
    """Get test cases specific to each provider"""
    if provider_name == "azure":
        return [
            {"voice": "zh-CN-XiaochenNeural", "text": "这是一个中文语音测试", "filename": "chinese_test"},
            {"voice": "en-US-BrianNeural", "text": "This is an English voice test", "filename": "english_test"},
        ]
    elif provider_name == "doubao":
        return [
            {
                "voice": "zh_male_lengkugege_emo_v2_mars_bigtts",
                "text": "这是一个中文语音测试",
                "filename": "chinese_test",
            },
            {
                "voice": "en_female_candice_emo_v2_mars_bigtts",
                "text": "This is an English voice test",
                "filename": "english_test",
            },
        ]
    else:
        return []


class TestTTSIntegration(unittest.TestCase):
    """Test cases for TTS integration - runs for all configured providers"""

    @classmethod
    def setUpClass(cls):
        """Discover available providers from configuration"""
        cls.config = TTSConfig()
        cls.available_providers = cls.config.get_available_providers()

        if not cls.available_providers:
            raise unittest.SkipTest("No TTS providers configured in .env file")

    def setUp(self):
        """Set up test output directory"""
        self.output_dir = Path(__file__).parent / "temp" / "tts_outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old test files
        for old_file in self.output_dir.glob("*.wav"):
            old_file.unlink()

    def _test_provider_voice_functionality(self, provider_name: str):
        """Test voice parameter functionality for a specific provider"""
        if not self.config.has_provider(provider_name):
            self.skipTest(f"{provider_name} not configured in .env file")

        # Create provider instance
        provider_config = self.config.get_provider_config(provider_name)
        tts = create_tts_provider(provider_name, provider_config)

        # Get test cases for this provider
        test_cases = get_test_cases_for_provider(provider_name)

        for case in test_cases:
            with self.subTest(provider=provider_name, voice=case["voice"]):
                output_path = self.output_dir / f"{provider_name}_{case['filename']}.wav"

                tts.convert_text_to_audio(text=case["text"], output_path=output_path, voice=case["voice"])

                self.assertTrue(output_path.exists(), f"Audio file not created for {provider_name}")
                file_size = output_path.stat().st_size
                self.assertGreater(
                    file_size, 1000, f"Audio file too small for {provider_name} with voice {case['voice']}"
                )

    def test_azure_voice_functionality(self):
        """Test Azure TTS voice functionality"""
        self._test_provider_voice_functionality("azure")

    def test_doubao_voice_functionality(self):
        """Test Doubao TTS voice functionality"""
        self._test_provider_voice_functionality("doubao")


if __name__ == "__main__":
    unittest.main(verbosity=2)
