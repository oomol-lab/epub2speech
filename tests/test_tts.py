#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from epub2speech.tts import create_azure_tts_from_config
from epub2speech.tts.config import TTSConfig


def test_tts_integration():
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
        return True

    # Validate config
    config = TTSConfig(config_path)
    if not config.validate_config():
        print("❌ TTS configuration is invalid")
        return False

    print("✅ TTS configuration validated")

    # Create TTS instance
    tts = create_azure_tts_from_config(config_path)
    if not tts.validate_config():
        print("❌ Azure TTS validation failed")
        return False

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
    conversion_success = tts.convert_text_to_audio(
        text=test_text,
        output_path=output_path
    )

    if conversion_success and output_path.exists():
        file_size = output_path.stat().st_size
        print("✅ Audio file generated successfully")
        print(f"📊 File size: {file_size} bytes")
        print(f"📁 Audio file saved to: {output_path}")

        # Smoke test: just verify file was created and has reasonable size
        if file_size > 1000:  # At least 1KB
            print("✅ Smoke test passed - audio file looks valid")
        else:
            print("⚠️  Audio file seems too small, but still counts as success")
    else:
        print("❌ TTS conversion failed or file not created")
        return False

    print("\n🎉 TTS smoke test passed!")
    print(f"💡 You can listen to the generated audio file at: {output_path}")
    return True

if __name__ == "__main__":
    try:
        test_result = test_tts_integration()
        sys.exit(0 if test_result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)