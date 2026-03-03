import time
from pathlib import Path

import requests

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
        max_retries: int = 900,
        poll_interval: float = 2.0,
        submit_timeout: float = 1800.0,
        poll_timeout: float = 30.0,
        download_connect_timeout: float = 20.0,
        download_read_timeout: float = 300.0,
        download_max_retries: int = 3,
        download_retry_delay: float = 2.0,
    ):
        if not access_token:
            raise ValueError("access_token is required and cannot be None or empty")
        if not base_url:
            raise ValueError("base_url is required and cannot be None or empty")
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")
        if submit_timeout <= 0:
            raise ValueError("submit_timeout must be > 0")
        if poll_timeout <= 0:
            raise ValueError("poll_timeout must be > 0")
        if download_connect_timeout <= 0:
            raise ValueError("download_connect_timeout must be > 0")
        if download_read_timeout <= 0:
            raise ValueError("download_read_timeout must be > 0")
        if download_max_retries < 1:
            raise ValueError("download_max_retries must be at least 1")
        if download_retry_delay < 0:
            raise ValueError("download_retry_delay must be >= 0")

        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        self.submit_timeout = submit_timeout
        self.poll_timeout = poll_timeout
        self.download_connect_timeout = download_connect_timeout
        self.download_read_timeout = download_read_timeout
        self.download_max_retries = download_max_retries
        self.download_retry_delay = download_retry_delay

        self._setup()

    def _setup(self) -> None:
        """Initialize the Doubao TTS client."""
        # Prepare session for reuse
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": self.access_token,
                "Content-Type": "application/json",
            }
        )

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
        submit_url = f"{self.base_url}/submit"

        payload = {"text": text, "voice": voice}

        try:
            response = self.session.post(submit_url, json=payload, timeout=self.submit_timeout)
            response.raise_for_status()

            result = response.json()

            # Extract task ID from response - handle multiple possible formats
            if "sessionID" in result:
                task_id = result["sessionID"]
            elif "taskId" in result:
                task_id = result["taskId"]
            elif "data" in result and "taskId" in result["data"]:
                task_id = result["data"]["taskId"]
            elif "id" in result:
                task_id = result["id"]
            elif "data" in result and "id" in result["data"]:
                task_id = result["data"]["id"]
            else:
                raise ValueError(f"Unexpected response format, cannot find task ID: {result}")

            return task_id

        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Submit request timeout after {self.submit_timeout} seconds") from e
        except requests.exceptions.HTTPError as e:
            # HTTPError always has a response attribute
            resp = e.response
            if resp is not None:
                raise RuntimeError(f"HTTP Error {resp.status_code}: {resp.text}") from e
            raise RuntimeError(f"HTTP Error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Submit request failed: {e}") from e

    def _poll_tts_result(self, task_id: str) -> str:
        """Poll for TTS result and return the audio URL."""
        result_url = f"{self.base_url}/result/{task_id}"

        retry_count = 0

        while retry_count < self.max_retries:
            try:
                response = self.session.get(result_url, timeout=self.poll_timeout)
                response.raise_for_status()

                result = response.json()

                # Get state from response
                state = result.get("state", "unknown")

                # If state is 'processing', continue polling
                if state == "processing":
                    retry_count += 1
                    if retry_count < self.max_retries:
                        time.sleep(self.poll_interval)
                    continue

                # State is not 'processing', extract audio URL from result
                data = result.get("data", {})

                # Try different possible fields for audio URL
                audio_url = None
                if "audioURL" in data:
                    audio_url = data["audioURL"]
                elif "audio_url" in data:
                    audio_url = data["audio_url"]
                elif "url" in data:
                    audio_url = data["url"]
                elif "audioURL" in result:
                    audio_url = result["audioURL"]
                elif "audio_url" in result:
                    audio_url = result["audio_url"]
                elif "url" in result:
                    audio_url = result["url"]

                if not audio_url:
                    raise ValueError(f"No audio URL found in response. State: {state}, Result: {result}")

                return audio_url

            except requests.exceptions.Timeout as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.poll_interval)
                    continue
                raise TimeoutError(f"Poll request timeout after {self.max_retries} retries") from e

            except requests.exceptions.HTTPError as e:
                # HTTPError always has a response attribute
                resp = e.response
                if resp is not None:
                    raise RuntimeError(f"HTTP Error {resp.status_code}: {resp.text}") from e
                raise RuntimeError(f"HTTP Error: {e}") from e

            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.poll_interval)
                    continue
                raise ConnectionError(f"Network error after {self.max_retries} retries") from e

        raise TimeoutError(f"TTS task still processing after {self.max_retries} retries (timeout)")

    def _download_audio(self, audio_url: str, output_path: Path) -> None:
        """Download audio file from URL to output_path."""
        temp_output_path = output_path.with_suffix(f"{output_path.suffix}.part")
        last_timeout_error: requests.exceptions.Timeout | None = None
        last_network_error: requests.exceptions.RequestException | None = None

        for attempt in range(1, self.download_max_retries + 1):
            try:
                with requests.get(
                    audio_url,
                    timeout=(self.download_connect_timeout, self.download_read_timeout),
                    stream=True,
                ) as response:
                    response.raise_for_status()

                    with open(temp_output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                temp_output_path.replace(output_path)
                return

            except requests.exceptions.Timeout as e:
                temp_output_path.unlink(missing_ok=True)
                last_timeout_error = e
                if attempt < self.download_max_retries:
                    time.sleep(self.download_retry_delay * attempt)
                    continue

            except requests.exceptions.HTTPError as e:
                temp_output_path.unlink(missing_ok=True)
                resp = e.response
                status_code = resp.status_code if resp is not None else None
                retryable_status_codes = {408, 425, 429, 500, 502, 503, 504}
                if status_code in retryable_status_codes and attempt < self.download_max_retries:
                    time.sleep(self.download_retry_delay * attempt)
                    continue

                if resp is not None:
                    raise RuntimeError(f"Download failed with HTTP Error {resp.status_code}: {resp.text}") from e
                raise RuntimeError(f"Download failed with HTTP Error: {e}") from e

            except requests.exceptions.RequestException as e:
                temp_output_path.unlink(missing_ok=True)
                last_network_error = e
                if attempt < self.download_max_retries:
                    time.sleep(self.download_retry_delay * attempt)
                    continue
                raise ConnectionError(f"Download failed after {self.download_max_retries} attempts: {e}") from e

            except OSError as e:
                temp_output_path.unlink(missing_ok=True)
                raise RuntimeError(f"Failed to write audio file to {output_path}: {e}") from e

        if last_timeout_error is not None:
            raise TimeoutError(
                f"Download timeout after {self.download_max_retries} attempts "
                f"(connect_timeout={self.download_connect_timeout}s, read_timeout={self.download_read_timeout}s)"
            ) from last_timeout_error

        if last_network_error is not None:
            raise ConnectionError(f"Download failed after {self.download_max_retries} attempts") from last_network_error

        raise RuntimeError("Download failed due to an unknown error")
