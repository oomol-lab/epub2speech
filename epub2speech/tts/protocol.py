from typing import Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class TextToSpeechProtocol(Protocol):
    def convert_text_to_audio(
        self,
        text: str,
        output_path: Path,
        voice: str | None = None
    ) -> None:
        ...

    def get_available_voices(self) -> list[str]:
        ...

    def validate_config(self) -> bool:
        ...