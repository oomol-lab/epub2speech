#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from epub2speech.tts.qwen_provider import QwenTextToSpeech


class TestQwenProvider(unittest.TestCase):
    def _create_provider(self, **kwargs) -> QwenTextToSpeech:
        return QwenTextToSpeech(
            access_token="token",
            base_url="https://example.com/api/v1/qwen-tts",
            download_connect_timeout=1.0,
            download_read_timeout=2.0,
            download_max_retries=kwargs.pop("download_max_retries", 3),
            download_retry_delay=0.0,
            **kwargs,
        )

    @staticmethod
    def _as_response_context(response: MagicMock) -> MagicMock:
        context_manager = MagicMock()
        context_manager.__enter__.return_value = response
        context_manager.__exit__.return_value = None
        return context_manager

    @patch("epub2speech.tts.qwen_provider.requests.get")
    def test_convert_text_to_audio_submits_expected_payload_and_downloads_audio(self, mock_get: MagicMock) -> None:
        provider = self._create_provider(
            model="qwen3-tts-instruct-flash",
            language_type="Chinese",
            instructions="Speak in a calm tone.",
            optimize_instructions=True,
        )
        submit_response = MagicMock()
        submit_response.raise_for_status.return_value = None
        submit_response.json.return_value = {
            "success": True,
            "data": {"audioURL": "https://audio.example.com/file.wav"},
        }
        provider.session.post = MagicMock(return_value=submit_response)

        download_response = MagicMock()
        download_response.raise_for_status.return_value = None
        download_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_get.return_value = self._as_response_context(download_response)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.wav"
            provider.convert_text_to_audio("你好，世界", output_path, "Cherry")

            self.assertEqual(output_path.read_bytes(), b"chunk1chunk2")
            provider.session.post.assert_called_once_with(
                "https://example.com/api/v1/qwen-tts/action/generate",
                json={
                    "text": "你好，世界",
                    "voice": "Cherry",
                    "model": "qwen3-tts-instruct-flash",
                    "languageType": "Chinese",
                    "instructions": "Speak in a calm tone.",
                    "optimizeInstructions": True,
                },
                timeout=120.0,
            )

    @patch("epub2speech.tts.qwen_provider.requests.get")
    def test_convert_text_to_audio_uses_provider_default_voice(self, mock_get: MagicMock) -> None:
        provider = self._create_provider(voice="Serena")
        submit_response = MagicMock()
        submit_response.raise_for_status.return_value = None
        submit_response.json.return_value = {
            "success": True,
            "data": {"audioURL": "https://audio.example.com/file.wav"},
        }
        provider.session.post = MagicMock(return_value=submit_response)

        download_response = MagicMock()
        download_response.raise_for_status.return_value = None
        download_response.iter_content.return_value = [b"ok"]
        mock_get.return_value = self._as_response_context(download_response)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.wav"
            provider.convert_text_to_audio("hello world", output_path, "")

            self.assertEqual(output_path.read_bytes(), b"ok")
            provider.session.post.assert_called_once_with(
                "https://example.com/api/v1/qwen-tts/action/generate",
                json={"text": "hello world", "voice": "Serena"},
                timeout=120.0,
            )

    def test_submit_raises_when_audio_url_missing(self) -> None:
        provider = self._create_provider()
        submit_response = MagicMock()
        submit_response.raise_for_status.return_value = None
        submit_response.json.return_value = {
            "success": True,
            "data": {},
        }
        provider.session.post = MagicMock(return_value=submit_response)

        with self.assertRaises(RuntimeError) as err:
            provider._submit_tts_task("hello world", "Cherry")

        self.assertIn("missing data.audioURL", str(err.exception))

    def test_submit_raises_for_http_error(self) -> None:
        provider = self._create_provider()
        http_error = requests.exceptions.HTTPError("bad request")
        http_error.response = MagicMock(status_code=400, text="bad request")
        submit_response = MagicMock()
        submit_response.raise_for_status.side_effect = http_error
        provider.session.post = MagicMock(return_value=submit_response)

        with self.assertRaises(RuntimeError) as err:
            provider._submit_tts_task("hello world", "Cherry")

        self.assertEqual(str(err.exception), "HTTP Error 400: bad request")

    @patch("epub2speech.tts.qwen_provider.time.sleep", return_value=None)
    @patch("epub2speech.tts.qwen_provider.requests.get")
    def test_download_audio_retries_after_timeout_then_succeeds(self, mock_get: MagicMock, _: MagicMock) -> None:
        provider = self._create_provider(download_max_retries=3)
        success_response = MagicMock()
        success_response.raise_for_status.return_value = None
        success_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_get.side_effect = [
            requests.exceptions.Timeout("tls handshake timeout"),
            self._as_response_context(success_response),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.wav"
            provider._download_audio("https://audio.example.com/file.wav", output_path)

            self.assertEqual(output_path.read_bytes(), b"chunk1chunk2")
            self.assertFalse(output_path.with_suffix(".wav.part").exists())
            self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
