"""Two-pass, bounded stabilization for explicitly selected moving shots.

Preserve intentional camera movement with a short smoothing window, fixed
edge crop, and limited correction. Review the candidate before using it.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .probe import ffprobe


@dataclass(frozen=True)
class StabilizationSettings:
    fps: int = 30
    smoothing: int = 4
    max_shift_fraction: float = 0.006
    max_angle: float = 0.0
    zoom_percent: float = 2.0

    def validate(self) -> None:
        if not 1 <= self.fps <= 120 or not 1 <= self.smoothing <= 15:
            raise ValueError("Use a positive frame rate and a short smoothing window")
        if not 0 < self.max_shift_fraction <= 0.02 or not 0 <= self.max_angle <= 0.02:
            raise ValueError("Correction limits must remain small for moving shots")
        if not 0 <= self.zoom_percent <= 5:
            raise ValueError("Fixed edge zoom must be between zero and five percent")


def stabilize_range(
    source: Path, output: Path, *, start: float, duration: float,
    speed: float = 1.0, width: int | None = None,
    settings: StabilizationSettings = StabilizationSettings(),
    before_output: Path | None = None, bitrate: str = "100M",
) -> Path:
    """Analyze and correct at delivery speed/resolution; never reuse scaled vectors."""
    settings.validate()
    source, output = source.resolve(), output.resolve()
    if not source.is_file() or source == output:
        raise ValueError("Source must exist and output must be a separate file")
    if not all(math.isfinite(x) and x > 0 for x in (duration, speed)) or not math.isfinite(start) or start < 0:
        raise ValueError("Invalid source range or speed")
    if width is not None and (width < 128 or width % 2):
        raise ValueError("Review width must be an even number of at least 128")
    if before_output and before_output.resolve() in (source, output):
        raise ValueError("Before comparison must have its own output path")
    binary = shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError("FFmpeg with vidstabdetect/vidstabtransform is required")
    metadata = ffprobe(source)
    stream = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    frame_width = width or int(stream["width"])
    output.parent.mkdir(parents=True, exist_ok=True)
    base = f"setpts=(PTS-STARTPTS)/{speed},fps={settings.fps}"
    if width:
        base += f",scale={width}:-2:flags=lanczos"
    base += ",format=yuv420p"
    inputs = [binary, "-hide_banner", "-loglevel", "error", "-y", "-threads", "3",
              "-ss", str(start), "-t", str(duration), "-i", str(source), "-an"]
    encode = ["-c:v", "h264_videotoolbox", "-allow_sw", "0", "-b:v", bitrate,
              "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    with tempfile.TemporaryDirectory(prefix="trip-stabilize-") as directory:
        work = Path(directory)
        subprocess.run(inputs + ["-vf", base + ",vidstabdetect=shakiness=5:accuracy=15:"
                                  "mincontrast=0.3:result=transforms.trf", "-f", "null", "-"],
                       cwd=work, check=True)
        transform = (
            "vidstabtransform=input=transforms.trf:"
            f"smoothing={settings.smoothing}:optalgo=gauss:"
            f"maxshift={max(1, round(frame_width * settings.max_shift_fraction))}:"
            f"maxangle={settings.max_angle}:optzoom=0:zoom={settings.zoom_percent}:"
            "crop=black:interpol=bicubic:tripod=0"
        )
        candidate = work / "candidate.mp4"
        subprocess.run(inputs + ["-vf", base + "," + transform, *encode, str(candidate)],
                       cwd=work, check=True)
        # Move atomically on the output filesystem, even if temp is another volume.
        staging = output.with_name(output.stem + ".staging.mp4")
        try:
            shutil.copyfile(candidate, staging)
            staging.replace(output)
        finally:
            staging.unlink(missing_ok=True)
        if before_output:
            before_output = before_output.resolve()
            before_output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(inputs + ["-vf", base, *encode, str(before_output)], check=True)
    report = {"source": str(source), "start": start, "duration": duration, "speed": speed,
              "output": str(output), "review_width": width, "settings": asdict(settings),
              "review_status": "candidate_requires_playback_review"}
    output.with_suffix(".stabilization.json").write_text(json.dumps(report, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument("--width", type=int, help="Optional small review width; omit for native output")
    parser.add_argument("--before-output", type=Path)
    parser.add_argument("--bitrate", default="100M")
    args = parser.parse_args()
    print(stabilize_range(args.source, args.output, start=args.start, duration=args.duration,
                         speed=args.speed, width=args.width, before_output=args.before_output,
                         bitrate=args.bitrate))


if __name__ == "__main__":
    main()
