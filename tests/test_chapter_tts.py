#!/usr/bin/env python3
import sys
import os
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech import ChapterTTS
from epub2speech.tts.azure_provider import AzureTextToSpeech
from tests.utils.config import TTSConfig
from epub2speech.tts import TextToSpeechProtocol


class TestChapterTTS(unittest.TestCase):
    """Test cases for ChapterTTS functionality"""

    def test_chapter_tts(self):
        """Test ChapterTTS functionality"""
        print("🧪 Testing ChapterTTS functionality...\n")

        config_path = Path(__file__).parent / "tts_config.json"

        if not config_path.exists():
            print("⚠️  TTS config file not found, skipping ChapterTTS test")
            print("This is expected in CI environment to avoid Azure resource usage")
            print("To run TTS tests locally, copy tts_config.json.template to tts_config.json")
            print("and fill in your Azure Speech credentials")
            self.skipTest("TTS config file not found")

        config = TTSConfig(config_path)
        self.assertTrue(config.validate_config(), "TTS configuration is invalid")
        print("✅ TTS configuration validated")

        config = TTSConfig(config_path)
        azure_config = config.get_azure_config()
        self.assertIsNotNone(azure_config, "No Azure configuration found in config file")

        subscription_key = azure_config["subscription_key"]
        region = azure_config["region"]

        self.assertIsNotNone(subscription_key, "Azure configuration missing subscription_key")
        self.assertIsNotNone(region, "Azure configuration missing region")

        tts = AzureTextToSpeech(
            subscription_key=subscription_key,
            region=region
        )

        self.assertTrue(tts.validate_config(), "Azure TTS validation failed")
        print("✅ Azure TTS instance created successfully")

        chapter_tts = ChapterTTS(
            tts_protocol=tts,
            sample_rate=24000,
            max_segment_length=500
        )

        print("✅ ChapterTTS processor created successfully")

        test_chapter_text = """
        Chapter 1: The Beginning

        This is the first sentence of the chapter. It introduces the main character.

        This is the second sentence, which provides more context about the story.
        The third sentence continues the narrative and builds the atmosphere.

        Finally, this is the last sentence of the chapter introduction.
        """
        output_dir = Path(__file__).parent / "dist"
        temp_dir = Path(__file__).parent / "temp"
        output_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)
        output_path = output_dir / "test_chapter.wav"

        print("\n🎤 Converting chapter to speech...")
        print(f"Output file: {output_path}")
        print(f"Temp directory: {temp_dir}")

        def progress_callback(current, total):
            print(f"Progress: {current}/{total} sentences")

        chapter_tts.process_chapter(
            text=test_chapter_text,
            output_path=output_path,
            workspace_path=temp_dir,
            voice="en-US-AriaNeural",
            progress_callback=progress_callback
        )
        self.assertTrue(output_path.exists(), "Chapter audio generation failed")

        file_size = output_path.stat().st_size
        print("✅ Chapter audio generated successfully")
        print(f"📊 File size: {file_size} bytes")
        print(f"📁 Audio file saved to: {output_path}")

        self.assertGreater(file_size, 10000, "File seems too small")
        print("✅ File size looks reasonable")

        print("\n🎉 ChapterTTS test passed!")
        print(f"💡 You can listen to the generated chapter audio at: {output_path}")

    def test_cjk_sentence_splitting(self):
        """Test CJK sentence splitting with different languages"""
        print("🧪 Testing CJK sentence splitting...\n")

        import numpy as np
        import soundfile as sf

        class MockTTSProtocol(TextToSpeechProtocol):
            """Mock TTS protocol for testing"""

            def convert_text_to_audio(self, text: str, output_path: Path, voice: str | None = None) -> None:
                _ = text, voice
                output_path.parent.mkdir(parents=True, exist_ok=True)
                dummy_audio = np.zeros((1000,))
                sf.write(output_path, dummy_audio, 24000)

            def get_available_voices(self) -> list[str]:
                return ["mock-voice"]

            def validate_config(self) -> bool:
                return True

        mock_tts = MockTTSProtocol()
        chapter_tts = ChapterTTS(tts_protocol=mock_tts)

        test_cases = [
            {
                "name": "Chinese long sentence",
                "text": "这是一个很长的中文句子，包含了多个分句；每个分句都有不同的内容：第一个分句介绍背景，第二个分句说明情况，第三个分句给出结论。",
                "expected_min_sentences": 1
            },
            {
                "name": "Japanese long sentence",
                "text": "これは長い日本語の文です、複数の節を含んでいます；各節には異なる内容があります：最初の節は背景を説明し、最後に結論を述べます。",
                "expected_min_sentences": 1
            },
            {
                "name": "Mixed CJK and English",
                "text": "This is a long sentence in English, it has multiple clauses; each clause has different content: first clause introduces background, second clause explains situation. 这是一个很长的中文句子，包含了英文和中文的混合内容；这种混合很常见。",
                "expected_min_sentences": 1
            },
            {
                "name": "Korean with Chinese punctuation",
                "text": "이것은 긴 한국어 문장입니다, 여러 절을 포함하고 있습니다; 각 절에는 다른 내용이 있습니다: 첫 번째 절은 배경을 소개합니다. 这是包含韩语和中文的长句，展示了混合使用的情况。",
                "expected_min_sentences": 1
            }
        ]

        output_dir = Path(__file__).parent / "dist"
        temp_dir = Path(__file__).parent / "temp"
        output_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)

        for test_case in test_cases:
            print(f"\n📄 Testing: {test_case['name']}")
            print(f"Text: {test_case['text'][:100]}…")

            segments = chapter_tts.split_text_into_segments(test_case['text'])
            segment_list = list(segments)
            print(f"Number of segments: {len(segment_list)}")
            print(f"Average segment length: {sum(len(s) for s in segment_list) / len(segment_list):.1f}")

            self.assertGreaterEqual(len(segment_list), test_case['expected_min_sentences'],
                                   f"Expected at least {test_case['expected_min_sentences']} segments, got {len(segment_list)}")
            print("✅ Segment splitting successful")

            output_path = output_dir / f"mock_{test_case['name'].replace(' ', '_').lower()}.wav"
            chapter_tts.process_chapter(
                text=test_case['text'],
                output_path=output_path,
                workspace_path=temp_dir,
                voice="mock-voice"
            )

        print(f"\n🎉 CJK sentence splitting tests passed!")


if __name__ == "__main__":
    unittest.main(verbosity=2)