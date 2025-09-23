#!/usr/bin/env python3
"""Test script for Azure TTS implementation"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from epub2speech.azure_tts import AzureTextToSpeech

def test_azure_tts():
    """Test Azure TTS functionality"""
    print("🧪 Testing Azure TTS implementation...\n")

    # Create Azure TTS instance
    tts = AzureTextToSpeech()

    # Check if configured
    if not tts.validate_config():
        print("⚠️  Azure Speech not properly configured")
        print("Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables")
        print("\nTo get Azure Speech credentials:")
        print("1. Go to https://portal.azure.com")
        print("2. Create a Speech Service resource")
        print("3. Get the key and region from the resource overview")
        return False

    print("✅ Azure Speech configuration validated")

    # Get available voices
    voices = tts.get_available_voices()
    print(f"✅ Found {len(voices)} available voices")
    if voices:
        print(f"Sample voices: {voices[:3]}")

    # Test text to speech conversion
    test_text = "您好，这是来自epub2speech的测试。Azure文本转语音服务工作正常！"
    output_path = Path("test_output.wav")

    print(f"\n🎤 Converting text: {test_text[:50]}...")
    success = tts.convert_text_to_audio(
        text=test_text,
        output_path=output_path,
        voice="zh-CN-XiaoxiaoNeural",
        rate="-10%",  # Slightly slower
        volume="+0%"
    )

    if success:
        print(f"✅ Audio saved to: {output_path.absolute()}")
        print(f"📊 File size: {output_path.stat().st_size} bytes")
    else:
        print("❌ Text to speech conversion failed")
        return False

    # Test with longer text
    longer_text = """
    明朝那些事儿，主要讲述的是从1344年到1644年这三百年间关于明朝的一些故事。
    以史料为基础，以年代和具体人物为主线，并加入了小说的笔法，语言幽默风趣。
    ""
".strip()

    longer_output = Path("test_long_output.wav")
    print(f"\n🎤 Converting longer text: {len(longer_text)} characters")
    success = tts.convert_text_to_audio(
        text=longer_text,
        output_path=longer_output,
        voice="zh-CN-YunjianNeural"  # Try different voice
    )

    if success:
        print(f"✅ Longer audio saved to: {longer_output.absolute()}")
        print(f"📊 File size: {longer_output.stat().st_size} bytes")
    else:
        print("❌ Longer text conversion failed")
        return False

    print("\n🎉 All Azure TTS tests completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_azure_tts()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)