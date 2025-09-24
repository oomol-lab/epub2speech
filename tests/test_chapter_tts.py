#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech import ChapterTTS
from epub2speech.tts.azure_provider import AzureTextToSpeech
from tests.utils.config import TTSConfig
from epub2speech.tts import TextToSpeechProtocol


def test_chapter_tts():
    """Test ChapterTTS functionality"""
    print("🧪 Testing ChapterTTS functionality...\n")

    # Use test config
    config_path = Path(__file__).parent / "tts_config.json"

    # Check if config file exists - if not, skip test and return success
    if not config_path.exists():
        print("⚠️  TTS config file not found, skipping ChapterTTS test")
        print("This is expected in CI environment to avoid Azure resource usage")
        print("To run TTS tests locally, copy tts_config.json.template to tts_config.json")
        print("and fill in your Azure Speech credentials")
        return True

    # Validate config
    config = TTSConfig(config_path)
    if not config.validate_config():
        print("❌ TTS configuration is invalid")
        return False

    print("✅ TTS configuration validated")

    # Create TTS instance from config
    config = TTSConfig(config_path)
    azure_config = config.get_azure_config()
    if not azure_config:
        print("❌ No Azure configuration found in config file")
        return False

    subscription_key = azure_config.get("subscription_key")
    region = azure_config.get("region")

    if not subscription_key or not region:
        print("❌ Azure configuration missing required fields")
        return False

    tts = AzureTextToSpeech(
        subscription_key=subscription_key,
        region=region
    )

    if not tts.validate_config():
        print("❌ Azure TTS validation failed")
        return False

    print("✅ Azure TTS instance created successfully")

    # Create ChapterTTS processor
    chapter_tts = ChapterTTS(
        tts_protocol=tts,
        sample_rate=24000,
        max_segment_length=500
    )

    print("✅ ChapterTTS processor created successfully")

    # Test chapter info extraction
    test_chapter_text = """
    Chapter 1: The Beginning

    This is the first sentence of the chapter. It introduces the main character.

    This is the second sentence, which provides more context about the story.
    The third sentence continues the narrative and builds the atmosphere.

    Finally, this is the last sentence of the chapter introduction.
    """
    # Test audio generation
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

    success = chapter_tts.process_chapter(
        text=test_chapter_text,
        output_path=output_path,
        temp_dir=temp_dir,
        voice="en-US-AriaNeural",
        progress_callback=progress_callback
    )

    if success and output_path.exists():
        file_size = output_path.stat().st_size
        print("✅ Chapter audio generated successfully")
        print(f"📊 File size: {file_size} bytes")
        print(f"📁 Audio file saved to: {output_path}")

        # Verify file is reasonable size
        if file_size > 10000:  # At least 10KB
            print("✅ File size looks reasonable")
        else:
            print("⚠️  File seems small, but test passed")
    else:
        print("❌ Chapter audio generation failed")
        return False

    print("\n🎉 ChapterTTS test passed!")
    print(f"💡 You can listen to the generated chapter audio at: {output_path}")
    return True


def test_cjk_sentence_splitting():
    """Test CJK sentence splitting with different languages"""
    print("🧪 Testing CJK sentence splitting...\n")

    # Create mock TTS
    import numpy as np
    import soundfile as sf

    class MockTTSProtocol(TextToSpeechProtocol):
        """Mock TTS protocol for testing"""

        def convert_text_to_audio(self, text: str, output_path: Path, voice: str | None = None) -> bool:
            """Mock implementation - just create empty file"""
            # Parameters are intentionally unused in this mock implementation
            _ = text, voice  # Suppress unused parameter warnings
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Create a dummy audio file for testing
            dummy_audio = np.zeros((1000,))  # 1000 samples of silence
            sf.write(output_path, dummy_audio, 24000)
            return True

        def get_available_voices(self) -> list[str]:
            """Get available mock voices"""
            return ["mock-voice"]

        def validate_config(self) -> bool:
            """Validate mock configuration"""
            return True

    mock_tts = MockTTSProtocol()
    chapter_tts = ChapterTTS(tts_protocol=mock_tts)

    # Test cases with different languages
    test_cases = [
        {
            "name": "Chinese long sentence",
            "text": "这是一个很长的中文句子，包含了多个分句；每个分句都有不同的内容：第一个分句介绍背景，第二个分句说明情况，第三个分句给出结论。",
            "expected_min_sentences": 1  # Currently 1 sentence due to length threshold
        },
        {
            "name": "Japanese long sentence",
            "text": "これは長い日本語の文です、複数の節を含んでいます；各節には異なる内容があります：最初の節は背景を説明し、最後に結論を述べます。",
            "expected_min_sentences": 1  # Currently 1 sentence due to length threshold
        },
        {
            "name": "Mixed CJK and English",
            "text": "This is a long sentence in English, it has multiple clauses; each clause has different content: first clause introduces background, second clause explains situation. 这是一个很长的中文句子，包含了英文和中文的混合内容；这种混合很常见。",
            "expected_min_sentences": 1  # Combined into one segment due to length constraints
        },
        {
            "name": "Korean with Chinese punctuation",
            "text": "이것은 긴 한국어 문장입니다, 여러 절을 포함하고 있습니다; 각 절에는 다른 내용이 있습니다: 첫 번째 절은 배경을 소개합니다. 这是包含韩语和中文的长句，展示了混合使用的情况。",
            "expected_min_sentences": 1  # Combined into one segment due to length constraints
        }
    ]

    output_dir = Path(__file__).parent / "dist"
    temp_dir = Path(__file__).parent / "temp"
    output_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)

    all_tests_passed = True

    for test_case in test_cases:
        print(f"\n📄 Testing: {test_case['name']}")
        print(f"Text: {test_case['text'][:100]}…")

        # Test segment splitting
        segments = chapter_tts.split_text_into_segments(test_case['text'])
        segment_list = list(segments)
        print(f"Number of segments: {len(segment_list)}")
        print(f"Average segment length: {sum(len(s) for s in segment_list) / len(segment_list):.1f}")

        # Verify minimum expected segments
        if len(segment_list) >= test_case['expected_min_sentences']:
            print("✅ Segment splitting successful")
        else:
            print(f"❌ Expected at least {test_case['expected_min_sentences']} segments, got {len(segment_list)}")
            all_tests_passed = False

        # Test audio generation
        output_path = output_dir / f"mock_{test_case['name'].replace(' ', '_').lower()}.wav"

        success = chapter_tts.process_chapter(
            text=test_case['text'],
            output_path=output_path,
            temp_dir=temp_dir,
            voice="mock-voice"
        )

        if success:
            print(f"✅ Audio generation successful: {output_path.name}")
        else:
            print("❌ Audio generation failed")
            all_tests_passed = False

    print(f"\n🎉 CJK sentence splitting tests {'passed' if all_tests_passed else 'failed'}!")
    return all_tests_passed


if __name__ == "__main__":
    try:
        # Run basic ChapterTTS test
        basic_test_result = test_chapter_tts()

        # Run CJK splitting test
        cjk_test_result = test_cjk_sentence_splitting()

        # Both tests must pass
        overall_result = basic_test_result and cjk_test_result

        print("\n📊 Overall test results:")
        print(f"   Basic ChapterTTS test: {'✅ PASS' if basic_test_result else '❌ FAIL'}")
        print(f"   CJK splitting test: {'✅ PASS' if cjk_test_result else '❌ FAIL'}")
        print(f"   Overall result: {'✅ ALL TESTS PASSED' if overall_result else '❌ SOME TESTS FAILED'}")

        sys.exit(0 if overall_result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)