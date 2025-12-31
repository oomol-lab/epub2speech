from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class TextToSpeechProtocol(Protocol):
    def convert_text_to_audio(
        self,
        text: str,
        output_path: Path,
        voice: str,
    ) -> None: ...
