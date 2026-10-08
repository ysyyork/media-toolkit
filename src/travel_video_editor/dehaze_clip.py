"""Apply a restrained, temporally stable haze reduction to a video range.

This is an optional preprocessing step for a single difficult shot, not a
global look. It estimates a shared atmospheric light from the selected range,
then applies a highlight-protected dark-channel correction frame by frame.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np


def _ffprobe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate,r_frame_rate", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)["streams"][0]


def _frames(command: list[str], width: int, height: int) -> Iterator[np.ndarray]:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert process.stdout is not None
    frame_bytes = width * height * 3
    try:
        while True:
            data = bytearray()
            while len(data) < frame_bytes:
                chunk = process.stdout.read(frame_bytes - len(data))
                if not chunk:
                    break
                data.extend(chunk)
            if len(data) != frame_bytes:
                break
            yield np.frombuffer(data, np.uint8).reshape(height, width, 3)
    finally:
        process.stdout.close()
        if process.wait() != 0:
            raise RuntimeError("FFmpeg failed while decoding the selected video range")


def _dark_channel(rgb: np.ndarray, radius: int = 7) -> np.ndarray:
    minimum = np.min(rgb, axis=2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (radius * 2 + 1, radius * 2 + 1))
    return cv2.erode(minimum, kernel)


def _estimate_atmospheric_light(samples: list[np.ndarray]) -> np.ndarray:
    estimates = []
    for bgr in samples:
        rgb = cv2.resize(bgr, (960, 540), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 255
        dark = _dark_channel(rgb)
        flat = dark.ravel()
        count = max(1, int(flat.size * 0.001))
        indices = np.argpartition(flat, -count)[-count:]
        candidates = rgb.reshape(-1, 3)[indices]
        estimates.append(np.percentile(candidates, 90, axis=0))
    # A shared estimate avoids brightness/color pumping between adjacent frames.
    return np.clip(np.median(estimates, axis=0), 0.65, 1.0).astype(np.float32)


def _correct_frame(
    bgr: np.ndarray,
    atmosphere: np.ndarray,
    strength: float,
    omega: float,
    minimum_transmission: float,
) -> np.ndarray:
    height, width = bgr.shape[:2]
    rgb = bgr[:, :, ::-1].astype(np.float32) / 255
    small = cv2.resize(rgb, (960, 540), interpolation=cv2.INTER_AREA)
    dark = _dark_channel(small)
    transmission = np.clip(1 - omega * dark / float(np.mean(atmosphere)), minimum_transmission, 1)
    guide = cv2.cvtColor((small * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    if hasattr(cv2, "ximgproc"):
        transmission = cv2.ximgproc.guidedFilter(guide, transmission.astype(np.float32), 24, 0.002)
    else:
        transmission = cv2.bilateralFilter(transmission.astype(np.float32), 9, 0.08, 12)
    transmission = np.clip(transmission, minimum_transmission, 1)
    transmission = cv2.resize(transmission, (width, height), interpolation=cv2.INTER_CUBIC)

    recovered = np.clip(
        (rgb - atmosphere[None, None, :]) / transmission[:, :, None] + atmosphere[None, None, :],
        0, 1,
    )
    luma = rgb[:, :, 0] * 0.2126 + rgb[:, :, 1] * 0.7152 + rgb[:, :, 2] * 0.0722
    highlight_protection = np.clip((luma - 0.52) / 0.30, 0, 1)
    blend = strength * (1 - 0.92 * highlight_protection)
    result = rgb * (1 - blend[:, :, None]) + recovered * blend[:, :, None]
    return np.clip(result[:, :, ::-1] * 255, 0, 255).astype(np.uint8)


def dehaze_range(
    source: Path,
    output: Path,
    start: float,
    duration: float,
    strength: float = 0.70,
    omega: float = 0.90,
    minimum_transmission: float = 0.28,
    bitrate: str = "100M",
) -> Path:
    """Create a high-bitrate, hardware-encoded dehazed intermediate clip."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and ffprobe are required")
    if not source.is_file() or start < 0 or duration <= 0:
        raise ValueError("Provide an existing source and a positive in-point/duration")
    if not 0 < strength <= 1 or not 0 < omega < 1 or not 0 < minimum_transmission < 1:
        raise ValueError("Strength, omega, and minimum transmission must be between 0 and 1")

    metadata = _ffprobe(source)
    width, height = int(metadata["width"]), int(metadata["height"])
    rate = Fraction(metadata.get("avg_frame_rate", "0/0"))
    if rate <= 0:
        rate = Fraction(metadata["r_frame_rate"])
    fps = float(rate)
    sample_command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", str(start), "-i", str(source),
        "-t", str(duration), "-vf", "fps=2,scale=960:540:flags=area,format=bgr24",
        "-f", "rawvideo", "pipe:1",
    ]
    samples = list(_frames(sample_command, 960, 540))
    if not samples:
        raise RuntimeError("No frames were decoded from the selected range")
    atmosphere = _estimate_atmospheric_light(samples)

    output.parent.mkdir(parents=True, exist_ok=True)
    decode_command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", str(start), "-i", str(source),
        "-t", str(duration), "-an", "-vf", "format=bgr24", "-f", "rawvideo", "pipe:1",
    ]
    encode_command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pixel_format", "bgr24", "-video_size", f"{width}x{height}", "-framerate", str(rate),
        "-i", "pipe:0", "-an", "-c:v", "h264_videotoolbox", "-b:v", bitrate,
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    decoder = subprocess.Popen(decode_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    encoder = subprocess.Popen(encode_command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert encoder.stdin is not None and encoder.stderr is not None
    try:
        for frame in _frames_from_process(decoder, width, height):
            encoder.stdin.write(_correct_frame(frame, atmosphere, strength, omega, minimum_transmission).tobytes())
        encoder.stdin.close()
        error = encoder.stderr.read().decode("utf-8", errors="replace")
        if decoder.wait() != 0 or encoder.wait() != 0:
            raise RuntimeError("FFmpeg failed to create the dehazed intermediate: " + error[-2000:])
    except Exception:
        decoder.kill()
        encoder.kill()
        output.unlink(missing_ok=True)
        raise
    return output


def _frames_from_process(process: subprocess.Popen, width: int, height: int) -> Iterator[np.ndarray]:
    assert process.stdout is not None
    frame_bytes = width * height * 3
    try:
        while True:
            data = bytearray()
            while len(data) < frame_bytes:
                chunk = process.stdout.read(frame_bytes - len(data))
                if not chunk:
                    break
                data.extend(chunk)
            if len(data) != frame_bytes:
                break
            yield np.frombuffer(data, np.uint8).reshape(height, width, 3)
    finally:
        process.stdout.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a restrained dehazed intermediate for one video range")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start", type=float, required=True, help="Source in-point in seconds")
    parser.add_argument("--duration", type=float, required=True, help="Range duration in seconds")
    parser.add_argument("--strength", type=float, default=0.70)
    parser.add_argument("--omega", type=float, default=0.90)
    parser.add_argument("--minimum-transmission", type=float, default=0.28)
    parser.add_argument("--bitrate", default="100M")
    args = parser.parse_args()
    result = dehaze_range(
        args.source, args.output, args.start, args.duration,
        args.strength, args.omega, args.minimum_transmission, args.bitrate,
    )
    print(f"Created {result}")


if __name__ == "__main__":
    main()
