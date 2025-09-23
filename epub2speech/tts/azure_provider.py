import logging
from pathlib import Path
from typing import Optional

import azure.cognitiveservices.speech as speechsdk

from .protocol import TextToSpeechProtocol
from .config import load_tts_config


logger = logging.getLogger(__name__)


class AzureTextToSpeech(TextToSpeechProtocol):
    """Azure Cognitive Services Speech implementation of Text-to-Speech"""

    def __init__(
        self,
        subscription_key: Optional[str] = None,
        region: Optional[str] = None,
        default_voice: str = "zh-CN-XiaoxiaoNeural"
    ):
        """
        Initialize Azure TTS service

        Args:
            subscription_key: Azure Speech Service subscription key
            region: Azure Speech Service region
            default_voice: Default voice to use (default: zh-CN-XiaoxiaoNeural)
        """
        self.subscription_key = subscription_key
        self.region = region
        self.default_voice = default_voice
        self._speech_config = None
        self._setup_speech_config()

    def _setup_speech_config(self) -> None:
        """Setup Azure Speech configuration"""
        if not self.subscription_key or not self.region:
            logger.warning("Azure Speech credentials not configured")
            return

        try:
            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )
            logger.info("Azure Speech configured for region: %s", self.region)
        except Exception as e:
            logger.error("Failed to setup Azure Speech config: %s", e)
            self._speech_config = None

    def convert_text_to_audio(
        self,
        text: str,
        output_path: Path,
        voice: str | None = None
    ) -> bool:
        """
        Convert text to audio file using Azure Speech Service

        Args:
            text: Text content to convert
            output_path: Path to save the audio file (.wav format)
            voice: Voice to use (defaults to self.default_voice)

        Returns:
            True if conversion successful, False otherwise
        """
        if not self._speech_config:
            logger.error("Azure Speech not properly configured")
            return False

        if not text or not text.strip():
            logger.warning("Empty text provided for conversion")
            return False

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use default voice if not specified
        voice = voice or self.default_voice

        try:
            # Configure audio output
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))

            # Configure speech synthesis
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self._speech_config,
                audio_config=audio_config
            )

            # Build SSML for speech synthesis
            ssml = self._build_ssml(text, voice)

            logger.info("Converting text to speech: %s characters", len(text))
            result = speech_synthesizer.speak_ssml_async(ssml).get()

            if result and result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("Audio saved to: %s", output_path)
                return True
            elif result and result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error("Speech synthesis canceled: %s", cancellation_details.reason)
                if cancellation_details.error_details:
                    logger.error("Error details: %s", cancellation_details.error_details)
                return False
            else:
                error_reason = result.reason if result else "Unknown error"
                logger.error("Speech synthesis failed: %s", error_reason)
                return False

        except Exception as e:
            logger.error("Exception during speech synthesis: %s", e)
            return False

    def _build_ssml(self, text: str, voice: str) -> str:
        """
        Build SSML (Speech Synthesis Markup Language) for speech synthesis

        Args:
            text: Text content
            voice: Voice to use

        Returns:
            SSML string
        """
        return f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN"><voice name="{voice}">{text}</voice></speak>'

    def get_available_voices(self) -> list[str]:
        """
        Get list of available voices from Azure Speech Service

        Returns:
            List of voice names
        """
        if not self._speech_config:
            logger.warning("Azure Speech not configured, returning default voices")
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
                audio_config=None  # No audio output needed for voice listing
            )

            result = synthesizer.get_voices_async().get()

            if result and result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                voices = []
                if hasattr(result, 'voices'):
                    for voice in result.voices:
                        voices.append(voice.name)
                return sorted(voices)
            else:
                error_reason = result.reason if result else "Unknown error"
                logger.error("Failed to retrieve voices: %s", error_reason)
                return []

        except Exception as e:
            logger.error("Exception while retrieving voices: %s", e)
            return []

    def validate_config(self) -> bool:
        """
        Validate Azure Speech configuration by testing connection

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self._speech_config:
            return False

        try:
            # Test with a simple synthesis
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self._speech_config,
                audio_config=None  # No audio output needed for validation
            )

            result = synthesizer.speak_text_async("Test").get()
            if result is None:
                return False
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted

        except Exception as e:
            logger.error("Configuration validation failed: %s", e)
            return False

def create_azure_tts_from_config(config_path: Optional[Path] = None) -> AzureTextToSpeech:
    """
    Create Azure TTS instance from configuration file

    Args:
        config_path: Optional path to config file, defaults to azure_tts_config.json

    Returns:
        AzureTextToSpeech instance configured from file
    """
    config = load_tts_config(config_path)
    azure_config = config.get_azure_config()

    return AzureTextToSpeech(
        subscription_key=azure_config.get("subscription_key"),
        region=azure_config.get("region")
    )