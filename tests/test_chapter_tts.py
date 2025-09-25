#!/usr/bin/env python3
import sys
import os
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech.chapter_tts import ChapterTTS
from epub2speech.tts import TextToSpeechProtocol


class TestChapterTTS(unittest.TestCase):
    """Test cases for ChapterTTS functionality"""


    def test_cjk_sentence_splitting(self):
        """Test CJK sentence splitting with different languages"""
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

        output_dir = Path(__file__).parent / "temp"
        temp_dir = output_dir / "chapter_tts_workspace"
        output_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)

        for test_case in test_cases:

            segments = chapter_tts.split_text_into_segments(test_case['text'])
            segment_list = list(segments)

            self.assertGreaterEqual(len(segment_list), test_case['expected_min_sentences'],
                                   f"Expected at least {test_case['expected_min_sentences']} segments, got {len(segment_list)}")

            output_path = output_dir / f"mock_{test_case['name'].replace(' ', '_').lower()}.wav"
            chapter_tts.process_chapter(
                text=test_case['text'],
                output_path=output_path,
                workspace_path=temp_dir,
                voice="mock-voice"
            )

        # Clean up workspace files after all tests
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    def test_different_sample_rates_resampling(self):
        """Test that audio segments with different sample rates are properly resampled"""
        import numpy as np
        import soundfile as sf

        class MixedSampleRateTTSProtocol(TextToSpeechProtocol):
            """Mock TTS protocol that generates audio with different sample rates"""

            def __init__(self):
                self.segment_count = 0

            def convert_text_to_audio(self, text: str, output_path: Path, voice: str | None = None) -> None:
                _ = text, voice
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Alternate between different sample rates to simulate real-world scenario
                if self.segment_count % 2 == 0:
                    sample_rate = 16000  # 16kHz
                    audio_data = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000))  # 1 second of 440Hz tone
                else:
                    sample_rate = 48000  # 48kHz
                    audio_data = np.sin(2 * np.pi * 880 * np.linspace(0, 1, 48000))  # 1 second of 880Hz tone

                sf.write(output_path, audio_data, sample_rate)
                self.segment_count += 1

            def get_available_voices(self) -> list[str]:
                return ["mixed-rate-voice"]

            def validate_config(self) -> bool:
                return True

        mock_tts = MixedSampleRateTTSProtocol()
        chapter_tts = ChapterTTS(tts_protocol=mock_tts)

        # Test text that should be split into multiple segments
        test_text = "This is the first sentence. This is the second sentence with different content. This is the third sentence. This is the fourth sentence."

        output_dir = Path(__file__).parent / "temp"
        temp_dir = output_dir / "chapter_tts_workspace_mixed_rates"
        output_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)

        output_path = output_dir / "mixed_sample_rates_test.wav"

        try:
            # Process chapter - this should trigger resampling since segments have different rates
            chapter_tts.process_chapter(
                text=test_text,
                output_path=output_path,
                workspace_path=temp_dir,
                voice="mixed-rate-voice"
            )

            # Verify the output file was created
            self.assertTrue(output_path.exists(), "Output audio file should be created")

            # Verify the output has consistent sample rate (should match first segment)
            audio_data, sample_rate = sf.read(output_path)
            self.assertEqual(sample_rate, 16000, "Final sample rate should match the first segment's rate")

            # Verify audio data is not empty
            self.assertGreater(len(audio_data), 0, "Output audio should not be empty")
        finally:
            # Clean up files
            if output_path.exists():
                output_path.unlink()
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
if __name__ == "__main__":
    unittest.main(verbosity=2)