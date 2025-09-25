from typing import Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class TextToSpeechProtocol(Protocol):
    """Protocol for text-to-speech conversion"""

    def convert_text_to_audio(
        self,
        text: str,
        output_path: Path,
        voice: str | None = None
    ) -> None:
        """
        Convert text to audio file

        Args:
            text: Text content to convert
            output_path: Path to save the audio file
            voice: Voice to use (implementation specific)

        Returns:
            True if conversion successful, False otherwise
        """
        ...

    def get_available_voices(self) -> list[str]:
        """
        Get list of available voices

        Returns:
            List of voice names/IDs
        """
        ...

    def validate_config(self) -> bool:
        """
        Validate that the TTS service is properly configured

        Returns:
            True if configuration is valid, False otherwise
        """
        ...