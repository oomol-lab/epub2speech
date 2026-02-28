#!/usr/bin/env python3
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from scripts.build_audio_qc import build_audio_qc


class TestBuildAudioQc(unittest.TestCase):
    def _write_pcm16_wav(self, path: Path, samples: np.ndarray, sample_rate: int) -> None:
        clipped = np.clip(samples, -1.0, 1.0)
        pcm = (clipped * 32767.0).astype(np.int16)
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())

    def test_build_audio_qc_collects_success_and_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sr = 24000

            # 0.1s silence + 0.2s tone + 0.1s silence
            silence = np.zeros(int(0.1 * sr), dtype=np.float32)
            tone = (0.3 * np.sin(2 * np.pi * 440 * np.arange(int(0.2 * sr)) / sr)).astype(np.float32)
            wave = np.concatenate([silence, tone, silence])
            self._write_pcm16_wav(root / "ok.wav", wave, sr)

            (root / "bad.wav").write_text("not a wav file", encoding="utf-8")

            payload = build_audio_qc(audio_root=root, recursive=False, extensions=(".wav",))

            self.assertEqual(payload["file_count"], 2)
            self.assertEqual(payload["analyzed_file_count"], 1)
            self.assertEqual(payload["failed_file_count"], 1)
            self.assertEqual(len(payload["files"]), 1)
            self.assertEqual(len(payload["failed_files"]), 1)

            info = payload["files"][0]
            self.assertEqual(info["sample_rate"], sr)
            self.assertEqual(info["channels"], 1)
            self.assertGreater(info["duration_seconds"], 0.35)
            self.assertGreater(info["leading_silence_seconds"], 0.05)
            self.assertGreater(info["trailing_silence_seconds"], 0.05)


if __name__ == "__main__":
    unittest.main(verbosity=2)
