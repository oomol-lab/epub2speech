from pathlib import Path

from .protocol import TextToSpeechProtocol


class DoubaoTextToSpeech(TextToSpeechProtocol):
    """Doubao (ByteDance) Text-to-Speech implementation.

    Args:
        access_token: Authentication token for Doubao API
        base_url: API endpoint URL (e.g., https://openspeech.bytedance.com/api/v1/tts)

    Voice Options:
        For available voice options, refer to the official documentation:
        - Official: https://www.volcengine.com/docs/6561/1257544
        - Example voices: zh_male_lengkugege_emo_v2_mars_bigtts, en_female_candice_emo_v2_mars_bigtts
    """

    def __init__(
        self,
        access_token: str,
        base_url: str,
    ):
        if not access_token:
            raise ValueError("access_token is required and cannot be None or empty")
        if not base_url:
            raise ValueError("base_url is required and cannot be None or empty")

        self.access_token = access_token
        self.base_url = base_url

        self._setup()

    def _setup(self) -> None:
        """Initialize the Doubao TTS client."""
        ...

    def convert_text_to_audio(
        self,
        text: str,
        output_path: Path,
        voice: str,
    ):
        """Convert text to audio using Doubao TTS service.

        This method follows an async pattern:
        1. Submit the TTS task and get a task_id
        2. Poll for the result until completion
        3. Download the audio file to output_path
        """
        if not text or not text.strip():
            raise ValueError("Empty text provided for conversion")

        # Step 1: Submit TTS task
        task_id = self._submit_tts_task(text, voice)

        # Step 2: Poll for result
        audio_url = self._poll_tts_result(task_id)

        # Step 3: Download audio file
        self._download_audio(audio_url, output_path)

    def _submit_tts_task(self, text: str, voice: str) -> str:
        """Submit a TTS task and return the task_id."""
        ...

    def _poll_tts_result(self, task_id: str) -> str:
        """Poll for TTS result and return the audio URL."""
        ...

    def _download_audio(self, audio_url: str, output_path: Path) -> None:
        """Download audio file from URL to output_path."""
        ...
