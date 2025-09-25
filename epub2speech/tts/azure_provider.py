import soundfile as sf
import numpy as np

import azure.cognitiveservices.speech as speechsdk

from pathlib import Path
from .protocol import TextToSpeechProtocol


class AzureTextToSpeech(TextToSpeechProtocol):
    def __init__(
        self,
        subscription_key: str,
        region: str,
        default_voice: str = "zh-CN-XiaoxiaoNeural"
    ):
        if not subscription_key:
            raise ValueError("subscription_key is required and cannot be None or empty")
        if not region:
            raise ValueError("region is required and cannot be None or empty")

        self.subscription_key = subscription_key
        self.region = region
        self.default_voice = default_voice
        self._speech_config = None

        self._setup_speech_config()

    def _setup_speech_config(self) -> None:
        try:
            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )
        except Exception as e:
            raise RuntimeError(f"Failed to setup Azure Speech config: {e}") from e

    def convert_text_to_audio(
        self,
        text: str,
        output_path: Path,
        voice: str | None = None
    ):
        if not self._speech_config:
            raise RuntimeError("Azure Speech not properly configured - cannot convert text to audio")

        if not text or not text.strip():
            raise ValueError("Empty text provided for conversion")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice = voice or self.default_voice

        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))

        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._speech_config,
            audio_config=audio_config
        )

        self._speech_config.speech_synthesis_voice_name = voice

        result = speech_synthesizer.speak_text_async(text).get()

        if result and result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            if output_path.exists():
                audio_data, _ = sf.read(output_path)
                if len(audio_data) > 0:
                    audio_range = np.max(audio_data) - np.min(audio_data)
                    is_silent = np.allclose(audio_data, 0) or audio_range < 0.001
                    if is_silent:
                        raise RuntimeError(f"Generated audio file is silent! Audio range: [{np.min(audio_data)}, {np.max(audio_data)}]. This may indicate Azure TTS configuration or language support issue")
                else:
                    raise RuntimeError("Generated audio file is empty (0 samples)")

        elif result and result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            raise RuntimeError(f"Speech synthesis canceled: {cancellation_details.reason}. Error details: {cancellation_details.error_details if cancellation_details.error_details else 'None'}")
        else:
            error_reason = result.reason if result else "Unknown error"
            raise RuntimeError(f"Speech synthesis failed: {error_reason}")

    def get_available_voices(self) -> list[str]:
        if not self._speech_config:
            return [
                "zh-CN-XiaoxiaoNeural",
                "zh-CN-XiaoyiNeural",
                "zh-CN-YunjianNeural",
                "zh-CN-YunxiNeural",
                "zh-CN-YunxiaNeural",
                "zh-CN-YunyangNeural"
            ]

        try:
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self._speech_config,
                audio_config=None
            )

            result = synthesizer.get_voices_async().get()

            if result and result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                voices = []
                if hasattr(result, 'voices'):
                    for voice in result.voices:
                        voices.append(voice.name)
                return sorted(voices)
            else:
                return []

        except Exception:
            return []

    def validate_config(self) -> bool:
        if not self._speech_config:
            return False

        try:
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self._speech_config,
                audio_config=None
            )

            result = synthesizer.speak_text_async("Test").get()
            if result is None:
                return False
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted

        except Exception:
            return False


def create_azure_tts_from_config() -> AzureTextToSpeech:
    raise RuntimeError(
        "create_azure_tts_from_config() is deprecated. "
        "Please create AzureTextToSpeech with explicit subscription_key and region parameters: "
        "AzureTextToSpeech(subscription_key='your_key', region='your_region')"
    )