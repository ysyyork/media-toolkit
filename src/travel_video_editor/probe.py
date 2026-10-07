"""Thin, structured wrapper around ffprobe."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path


def ffprobe(path: Path) -> dict:
    binary = shutil.which("ffprobe")
    if not binary:
        raise RuntimeError("ffprobe is required; install FFmpeg first")
    result = subprocess.run(
        [binary, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def verify_inputs(paths: list[Path]) -> None:
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing input media:\n" + "\n".join(missing))
