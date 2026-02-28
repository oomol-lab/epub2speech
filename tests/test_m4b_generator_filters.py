#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "epub2speech" / "m4b_generator.py"
SPEC = importlib.util.spec_from_file_location("m4b_generator_module_for_test", MODULE_PATH)
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


class DummyM4BGenerator(M4BGenerator):
    def _check_dependencies(self):
        return None

    def __init__(self):
        self.last_command: list[str] = []
        super().__init__(ffmpeg_path="ffmpeg", ffprobe_path="ffprobe")

    def _create_chapter_metadata(self, chapters, work_dir, titles, authors):
        _ = chapters, titles, authors
        path = Path(work_dir) / "dummy_meta.txt"
        path.write_text(";FFMETADATA1\n", encoding="utf-8")
        return path

    def _concat_audio_files(self, chapters, work_dir):
        _ = chapters
        path = Path(work_dir) / "dummy_concat.mp4"
        path.write_bytes(b"dummy")
        return path

    def _run_command(self, args, error_message):
        _ = error_message
        self.last_command = list(args)
        return _DummyResult()


class TestM4BGeneratorFilters(unittest.TestCase):
    def test_includes_loudnorm_filter_when_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chapter_file = root / "chapter.wav"
            chapter_file.write_bytes(b"dummy")

            generator = DummyM4BGenerator()
            generator.generate_m4b(
                titles=["t"],
                authors=["a"],
                chapters=[ChapterInfo("c1", chapter_file)],
                output_path=root / "out.m4b",
                workspace_path=root / "workspace",
                audio_filter_chain="loudnorm=I=-16:TP=-1.5:LRA=11",
            )

            self.assertIn("-af", generator.last_command)
            af_index = generator.last_command.index("-af")
            self.assertEqual(generator.last_command[af_index + 1], "loudnorm=I=-16:TP=-1.5:LRA=11")

    def test_does_not_include_audio_filter_when_not_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chapter_file = root / "chapter.wav"
            chapter_file.write_bytes(b"dummy")

            generator = DummyM4BGenerator()
            generator.generate_m4b(
                titles=["t"],
                authors=["a"],
                chapters=[ChapterInfo("c1", chapter_file)],
                output_path=root / "out.m4b",
                workspace_path=root / "workspace",
                audio_filter_chain=None,
            )

            self.assertNotIn("-af", generator.last_command)


if __name__ == "__main__":
    unittest.main(verbosity=2)
