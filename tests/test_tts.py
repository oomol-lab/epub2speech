#!/usr/bin/env python3
import sys
import os
import unittest
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech.tts.azure_provider import AzureTextToSpeech
from tests.utils.config import TTSConfig


class TestTTSIntegration(unittest.TestCase):
    """Test cases for TTS integration"""

    def test_tts_integration(self):
        """Test TTS integration with configuration - smoke test"""
        print("🧪 Testing TTS integration (smoke test)...\n")

        # Use test config
        config_path = Path(__file__).parent / "tts_config.json"

        # Check if config file exists - if not, skip test and return success
        if not config_path.exists():
            print("⚠️  TTS config file not found, skipping Azure TTS test")
            print("This is expected in CI environment to avoid Azure resource usage")
            print("To run TTS tests locally, copy tts_config.json.template to tts_config.json")
            print("and fill in your Azure Speech credentials")
            self.skipTest("TTS config file not found")

        # Validate config
        config = TTSConfig(config_path)
        self.assertTrue(config.validate_config(), "TTS configuration is invalid")
        print("✅ TTS configuration validated")

        # Create TTS instance from config
        config = TTSConfig(config_path)
        azure_config = config.get_azure_config()
        self.assertIsNotNone(azure_config, "No Azure configuration found in config file")

        tts = AzureTextToSpeech(
            subscription_key=azure_config["subscription_key"],
            region=azure_config["region"],
        )
        self.assertTrue(tts.validate_config(), "Azure TTS validation failed")
        print("✅ Azure TTS instance created successfully")

        # Setup output directory
        output_dir = Path(__file__).parent / "dist"
        output_dir.mkdir(exist_ok=True)

        # Clean up old test files before running
        for old_file in output_dir.glob("*.wav"):
            old_file.unlink()

        # Test with simple text - smoke test: just ensure file gets generated
        test_text = "Hello, this is a smoke test of the text to speech system."
        timestamp = "test"
        output_path = output_dir / f"tts_{timestamp}.wav"

        print(f"🎤 Converting test text: {test_text[:50]}...")
        tts.convert_text_to_audio(
            text=test_text,
            output_path=output_path
        )
        self.assertTrue(output_path.exists(),
                       "TTS conversion failed or file not created")

        file_size = output_path.stat().st_size
        print("✅ Audio file generated successfully")
        print(f"📊 File size: {file_size} bytes")
        print(f"📁 Audio file saved to: {output_path}")

        # Smoke test: just verify file was created and has reasonable size
        self.assertGreater(file_size, 1000, "Audio file seems too small")
        print("✅ Smoke test passed - audio file looks valid")

        print("\n🎉 TTS smoke test passed!")
        print(f"💡 You can listen to the generated audio file at: {output_path}")


if __name__ == "__main__":
    unittest.main(verbosity=2)