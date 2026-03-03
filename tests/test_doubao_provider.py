#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from epub2speech.tts.doubao_provider import DoubaoTextToSpeech


class TestDoubaoProviderDownload(unittest.TestCase):
    def _create_provider(self, *, retries: int = 3) -> DoubaoTextToSpeech:
        return DoubaoTextToSpeech(
            access_token="token",
            base_url="https://example.com/api/v1/tts",
            download_connect_timeout=1.0,
            download_read_timeout=2.0,
            download_max_retries=retries,
            download_retry_delay=0.0,
        )

    @staticmethod
    def _as_response_context(response: MagicMock) -> MagicMock:
        context_manager = MagicMock()
        context_manager.__enter__.return_value = response
        context_manager.__exit__.return_value = None
        return context_manager

    @patch("epub2speech.tts.doubao_provider.time.sleep", return_value=None)
    @patch("epub2speech.tts.doubao_provider.requests.get")
    def test_download_audio_retries_after_timeout_then_succeeds(self, mock_get: MagicMock, _: MagicMock) -> None:
        provider = self._create_provider(retries=3)
        success_response = MagicMock()
        success_response.raise_for_status.return_value = None
        success_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_get.side_effect = [
            requests.exceptions.Timeout("tls handshake timeout"),
            self._as_response_context(success_response),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.wav"
            provider._download_audio("https://audio.example.com/file", output_path)

            self.assertEqual(output_path.read_bytes(), b"chunk1chunk2")
            self.assertFalse(output_path.with_suffix(".wav.part").exists())
            self.assertEqual(mock_get.call_count, 2)
            for call in mock_get.call_args_list:
                self.assertEqual(call.kwargs["timeout"], (1.0, 2.0))
                self.assertTrue(call.kwargs["stream"])

    @patch("epub2speech.tts.doubao_provider.time.sleep", return_value=None)
    @patch("epub2speech.tts.doubao_provider.requests.get")
    def test_download_audio_raises_timeout_after_retries_exhausted(self, mock_get: MagicMock, _: MagicMock) -> None:
        provider = self._create_provider(retries=2)
        mock_get.side_effect = requests.exceptions.Timeout("tls handshake timeout")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.wav"
            with self.assertRaises(TimeoutError) as err:
                provider._download_audio("https://audio.example.com/file", output_path)

            self.assertIn("Download timeout after 2 attempts", str(err.exception))
            self.assertEqual(mock_get.call_count, 2)
            self.assertFalse(output_path.exists())
            self.assertFalse(output_path.with_suffix(".wav.part").exists())

    @patch("epub2speech.tts.doubao_provider.time.sleep", return_value=None)
    @patch("epub2speech.tts.doubao_provider.requests.get")
    def test_download_audio_retries_on_retryable_http_status(self, mock_get: MagicMock, _: MagicMock) -> None:
        provider = self._create_provider(retries=2)
        http_error = requests.exceptions.HTTPError("service unavailable")
        http_error.response = MagicMock(status_code=503, text="busy")

        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = http_error

        success_response = MagicMock()
        success_response.raise_for_status.return_value = None
        success_response.iter_content.return_value = [b"ok"]

        mock_get.side_effect = [
            self._as_response_context(fail_response),
            self._as_response_context(success_response),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.wav"
            provider._download_audio("https://audio.example.com/file", output_path)

            self.assertEqual(output_path.read_bytes(), b"ok")
            self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
