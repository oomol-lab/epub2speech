#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "epub2speech" / "m4b_generator.py"
SPEC = importlib.util.spec_from_file_location("m4b_generator_module_for_test_concat", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

ChapterInfo = module.ChapterInfo
M4BGenerator = module.M4BGenerator


class _DummyResult:
    def __init__(self):
        self.returncode = 0
        self.stdout = ""
        self.stderr = ""


class _ConcatCommandCaptureGenerator(M4BGenerator):
    def _check_dependencies(self):
        return None

    def __init__(self):
        self.commands: list[list[str]] = []
        super().__init__(ffmpeg_path="ffmpeg", ffprobe_path="ffprobe")

    def _run_command(self, args, error_message):
        _ = error_message
        self.commands.append(list(args))
        Path(args[-1]).write_bytes(b"dummy")
        return _DummyResult()


class TestM4BConcatCommand(unittest.TestCase):
    def test_concat_uses_wav_intermediate_for_cross_ffmpeg_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chapter_a = root / "chapter_a.wav"
            chapter_b = root / "chapter_b.wav"
            chapter_a.write_bytes(b"a")
            chapter_b.write_bytes(b"b")

            generator = _ConcatCommandCaptureGenerator()
            concat_path = generator._concat_audio_files(
                chapters=[ChapterInfo("c1", chapter_a), ChapterInfo("c2", chapter_b)],
                work_dir=root / "workspace",
            )

            self.assertEqual(concat_path.suffix, ".wav")
            self.assertTrue(generator.commands, "Expected ffmpeg concat command to be recorded")
            cmd = generator.commands[0]
            self.assertIn("-c:a", cmd)
            codec_index = cmd.index("-c:a")
            self.assertEqual(cmd[codec_index + 1], "pcm_s16le")
            self.assertNotIn("-c", cmd)


if __name__ == "__main__":
    unittest.main(verbosity=2)
