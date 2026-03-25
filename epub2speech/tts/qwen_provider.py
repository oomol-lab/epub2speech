import time
from pathlib import Path

import requests

from .protocol import TextToSpeechProtocol


class QwenTextToSpeech(TextToSpeechProtocol):
    """Qwen TTS implementation backed by fusion-api action endpoints."""

    def __init__(
        self,
        access_token: str,
        base_url: str,
        model: str | None = None,
        voice: str | None = None,
        language_type: str | None = None,
        instructions: str | None = None,
        optimize_instructions: bool | None = None,
        submit_timeout: float = 120.0,
        download_connect_timeout: float = 20.0,
        download_read_timeout: float = 300.0,
        download_max_retries: int = 3,
        download_retry_delay: float = 2.0,
    ):
        if not access_token:
            raise ValueError("access_token is required and cannot be None or empty")
        if not base_url:
            raise ValueError("base_url is required and cannot be None or empty")
        if submit_timeout <= 0:
            raise ValueError("submit_timeout must be > 0")
        if download_connect_timeout <= 0:
            raise ValueError("download_connect_timeout must be > 0")
        if download_read_timeout <= 0:
            raise ValueError("download_read_timeout must be > 0")
        if download_max_retries < 1:
            raise ValueError("download_max_retries must be at least 1")
        if download_retry_delay < 0:
            raise ValueError("download_retry_delay must be >= 0")
        if optimize_instructions and not instructions:
            raise ValueError("instructions are required when optimize_instructions is enabled")

        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.voice = voice
        self.language_type = language_type
        self.instructions = instructions
        self.optimize_instructions = optimize_instructions
        self.submit_timeout = submit_timeout
        self.download_connect_timeout = download_connect_timeout
        self.download_read_timeout = download_read_timeout
        self.download_max_retries = download_max_retries
        self.download_retry_delay = download_retry_delay

        self._setup()

    def _setup(self) -> None:
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
    ) -> None:
        if not text or not text.strip():
            raise ValueError("Empty text provided for conversion")

        resolved_voice = voice or self.voice
        if not resolved_voice:
            raise ValueError("voice is required either during initialization or convert_text_to_audio")

        audio_url = self._submit_tts_task(text=text, voice=resolved_voice)
        self._download_audio(audio_url, output_path)

    def _submit_tts_task(self, text: str, voice: str) -> str:
        submit_url = f"{self.base_url}/action/generate"

        payload: dict[str, str | bool] = {
            "text": text,
            "voice": voice,
        }
        if self.model:
            payload["model"] = self.model
        if self.language_type:
            payload["languageType"] = self.language_type
        if self.instructions:
            payload["instructions"] = self.instructions
        if self.optimize_instructions is not None:
            payload["optimizeInstructions"] = self.optimize_instructions

        try:
            response = self.session.post(submit_url, json=payload, timeout=self.submit_timeout)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Submit request timeout after {self.submit_timeout} seconds") from e
        except requests.exceptions.HTTPError as e:
            resp = e.response
            if resp is not None:
                raise RuntimeError(f"HTTP Error {resp.status_code}: {resp.text}") from e
            raise RuntimeError(f"HTTP Error: {e}") from e
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Submit request failed: {e}") from e
        except ValueError as e:
            raise RuntimeError("Submit request returned invalid JSON") from e

        if result.get("success") is not True:
            raise RuntimeError(f"Unexpected response format: {result}")

        data = result.get("data")
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected response format, missing data object: {result}")

        audio_url = data.get("audioURL")
        if not audio_url:
            raise RuntimeError(f"Unexpected response format, missing data.audioURL: {result}")

        return audio_url

    def _download_audio(self, audio_url: str, output_path: Path) -> None:
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
