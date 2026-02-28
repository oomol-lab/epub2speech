#!/usr/bin/env python3
import argparse
import json
import math
import wave
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

try:
    import soundfile as sf
except ImportError:  # pragma: no cover - exercised in environments without optional dependency
    sf = None

DEFAULT_EXTENSIONS = (".wav", ".flac", ".aiff", ".aif", ".ogg", ".opus", ".mp3", ".m4a", ".aac")


def _to_dbfs(value: float) -> float | None:
    if value <= 0:
        return None
    return round((20 * math.log10(value)), 3)


def _duration_from_samples(sample_count: int, sample_rate: int) -> float:
    if sample_rate <= 0:
        return 0.0
    return round((sample_count / sample_rate), 3)


def _decode_pcm_wav(file_path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(file_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frame_count = wav.getnframes()
        compression = wav.getcomptype()
        if compression != "NONE":
            raise RuntimeError(f"Unsupported WAV compression: {compression}")

        raw_bytes = wav.readframes(frame_count)

    if sample_width == 1:
        data = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(raw_bytes, dtype="<i2").astype(np.float32) / 32768.0
    elif sample_width == 3:
        raw = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
        extended = np.zeros((raw.shape[0], 4), dtype=np.uint8)
        extended[:, :3] = raw
        extended[:, 3] = np.where(raw[:, 2] & 0x80, 0xFF, 0x00).astype(np.uint8)
        data = extended.view("<i4").reshape(-1).astype(np.float32) / 8388608.0
    elif sample_width == 4:
        data = np.frombuffer(raw_bytes, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise RuntimeError(f"Unsupported WAV sample width: {sample_width}")

    if channels > 1:
        data = data.reshape(-1, channels)
    return data, sample_rate


def _read_audio(file_path: Path) -> tuple[np.ndarray, int]:
    if sf is not None:
        data, sample_rate = sf.read(file_path)
        return np.asarray(data), int(sample_rate)

    if file_path.suffix.lower() != ".wav":
        raise RuntimeError("soundfile is required to analyze non-WAV files")

    return _decode_pcm_wav(file_path=file_path)


def _silence_boundaries(abs_mono: np.ndarray, sample_rate: int, threshold: float = 0.001) -> tuple[float, float]:
    if abs_mono.size == 0 or sample_rate <= 0:
        return (0.0, 0.0)

    non_silent = np.where(abs_mono > threshold)[0]
    if non_silent.size == 0:
        full_duration = _duration_from_samples(len(abs_mono), sample_rate)
        return (full_duration, full_duration)

    leading = _duration_from_samples(int(non_silent[0]), sample_rate)
    trailing = _duration_from_samples(int(len(abs_mono) - non_silent[-1] - 1), sample_rate)
    return (leading, trailing)


def analyze_audio_file(file_path: Path) -> dict:
    array, sample_rate = _read_audio(file_path)

    channels = int(array.shape[1]) if array.ndim > 1 else 1
    mono = np.mean(array, axis=1) if array.ndim > 1 else array
    abs_mono = np.abs(mono)

    sample_count = len(mono)
    peak = float(np.max(abs_mono)) if sample_count else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if sample_count else 0.0
    clipped_samples = int(np.sum(abs_mono >= 0.999)) if sample_count else 0
    silence_ratio = float(np.mean(abs_mono <= 0.001)) if sample_count else 1.0
    leading_silence, trailing_silence = _silence_boundaries(abs_mono=abs_mono, sample_rate=sample_rate)

    return {
        "file": str(file_path),
        "sample_rate": int(sample_rate),
        "channels": channels,
        "samples": sample_count,
        "duration_seconds": _duration_from_samples(sample_count, sample_rate),
        "peak_dbfs": _to_dbfs(peak),
        "rms_dbfs": _to_dbfs(rms),
        "silence_ratio": round(silence_ratio, 6),
        "leading_silence_seconds": leading_silence,
        "trailing_silence_seconds": trailing_silence,
        "clipped_samples": clipped_samples,
        "clipped_ratio": round((clipped_samples / max(sample_count, 1)), 6),
    }


def _list_audio_files(audio_root: Path, recursive: bool, extensions: tuple[str, ...]) -> list[Path]:
    ext_set = {ext.lower() for ext in extensions}
    iterator = audio_root.rglob("*") if recursive else audio_root.glob("*")
    files = [path for path in iterator if path.is_file() and path.suffix.lower() in ext_set]
    return sorted(files, key=lambda path: str(path))


def build_audio_qc(
    audio_root: Path,
    recursive: bool = True,
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS,
) -> dict:
    files = _list_audio_files(audio_root=audio_root, recursive=recursive, extensions=extensions)
    chapter_reports: list[dict] = []
    failed_files: list[dict] = []

    for file_path in files:
        try:
            chapter_reports.append(analyze_audio_file(file_path))
        except Exception as exc:  # pragma: no cover - covered by integration test behavior
            failed_files.append({"file": str(file_path), "error": f"{type(exc).__name__}: {exc}"})

    rms_values = [entry["rms_dbfs"] for entry in chapter_reports if entry.get("rms_dbfs") is not None]
    peak_values = [entry["peak_dbfs"] for entry in chapter_reports if entry.get("peak_dbfs") is not None]
    total_duration = sum(float(entry.get("duration_seconds", 0.0)) for entry in chapter_reports)
    high_silence_count = sum(1 for entry in chapter_reports if float(entry.get("silence_ratio", 0.0)) > 0.2)
    clipped_count = sum(1 for entry in chapter_reports if float(entry.get("clipped_ratio", 0.0)) > 0.0)

    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "audio_root": str(audio_root),
        "recursive": recursive,
        "extensions": list(extensions),
        "file_count": len(files),
        "analyzed_file_count": len(chapter_reports),
        "failed_file_count": len(failed_files),
        "total_duration_seconds": round(total_duration, 3),
        "mean_rms_dbfs": round((sum(rms_values) / len(rms_values)), 3) if rms_values else None,
        "mean_peak_dbfs": round((sum(peak_values) / len(peak_values)), 3) if peak_values else None,
        "high_silence_file_count": high_silence_count,
        "clipped_file_count": clipped_count,
        "files": chapter_reports,
        "failed_files": failed_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build audio_qc.json by scanning local audio files")
    parser.add_argument("audio_root", type=Path, help="Directory containing generated chapter audio")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path (default: <audio_root>/audio_qc.json)")
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="Only scan files directly under audio_root",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=",".join(DEFAULT_EXTENSIONS),
        help="Comma-separated list of file suffixes to scan (e.g. .wav,.m4a)",
    )
    args = parser.parse_args()

    if not args.audio_root.exists() or not args.audio_root.is_dir():
        raise FileNotFoundError(f"Audio root directory not found: {args.audio_root}")

    extensions = tuple(ext.strip().lower() for ext in args.extensions.split(",") if ext.strip())
    payload = build_audio_qc(
        audio_root=args.audio_root,
        recursive=not args.non_recursive,
        extensions=extensions or DEFAULT_EXTENSIONS,
    )

    output_path = args.output or (args.audio_root / "audio_qc.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Audio QC written: {output_path}")
    print(f"Analyzed files: {payload['analyzed_file_count']}, failed: {payload['failed_file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
