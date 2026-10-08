"""Dense, labelled source-range sheets for reviewing edit boundaries.

These sheets expose the source handles around each edit. They support motion
review; they cannot establish smooth playback or replace watching the preview.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .models import Project, Shot
from .probe import ffprobe


def build_motion_review(project: Project, interval: float = 0.5,
                        handles: float = 1.0, workers: int = 3) -> list[Path]:
    """Sample each selected source range, including available boundary handles.

    Labels use source time, not output time; speed and the selected in/out points
    are recorded above every sheet. Unselected handle frames are labelled.
    """
    if interval <= 0 or handles < 0 or workers < 1:
        raise ValueError("Positive interval/workers and nonnegative handles required")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Install media-toolkit[video-review] for motion sheets") from exc

    binary = shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError("FFmpeg is required")
    folder = project.output.parent / (project.output.stem + "_motion_review")
    folder.mkdir(parents=True, exist_ok=True)
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    font = ImageFont.truetype(str(font_path), 14) if font_path.exists() else ImageFont.load_default()
    width, height, columns = 400, 226, 5

    with tempfile.TemporaryDirectory(prefix="tripcut-motion-") as temp:
        def sample(item: tuple[int, Shot]) -> list[Path]:
            index, shot = item
            source = project.source_path(shot)
            metadata = ffprobe(source)
            length = float(metadata["format"]["duration"])
            start = max(0.0, shot.start - handles)
            end = min(length, shot.start + shot.duration + handles)
            frames_dir = Path(temp) / str(index)
            frames_dir.mkdir()
            args = [binary, "-v", "error", "-y", "-threads", "2"]
            if sys.platform == "darwin":
                args += ["-hwaccel", "videotoolbox"]
            args += ["-ss", str(start), "-t", str(end-start), "-i", str(source),
                     "-vf", f"fps=1/{interval}:start_time=0,scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                     "-pix_fmt", "yuvj420p", "-q:v", "3", "-start_number", "0", str(frames_dir / "%04d.jpg")]
            result = subprocess.run(args, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(f"Motion sampling failed for {source.name}: {result.stderr}")
            frames = sorted(frames_dir.glob("*.jpg"))
            if not frames:
                raise RuntimeError(f"No motion samples for {source.name}")
            outputs = []
            # Cap page height so long candidate ranges remain readable.
            for page, offset in enumerate(range(0, len(frames), 30), start=1):
                batch = frames[offset:offset+30]
                rows = math.ceil(len(batch) / columns)
                sheet = Image.new("RGB", (width*columns, 60 + rows*(height+28)), "#151515")
                draw = ImageDraw.Draw(sheet)
                draw.text((8, 6), f"SHOT {index:02d}: {source.name}", font=font, fill="white")
                draw.text((8, 28), f"SOURCE IN {shot.start:.2f}s / OUT {shot.start+shot.duration:.2f}s / SPEED {shot.speed:g}x / samples {interval:g}s", font=font, fill="#dddddd")
                for cell, path in enumerate(batch):
                    seconds = start + (offset+cell)*interval
                    handle = seconds < shot.start or seconds >= shot.start+shot.duration
                    x, y = (cell % columns)*width, 60 + (cell // columns)*(height+28)
                    draw.text((x+6, y+5), f"{seconds:.2f}s  {'HANDLE' if handle else 'SELECTED'}", font=font, fill="#efb35d" if handle else "#eeeeee")
                    with Image.open(path) as frame:
                        sheet.paste(frame.convert("RGB"), (x, y+28))
                target = folder / f"shot_{index:02d}_{page:02d}.jpg"
                sheet.save(target, quality=92)
                outputs.append(target)
            print(f"Reviewed source range {index:02d}: {source.name}", flush=True)
            return outputs

        with ThreadPoolExecutor(max_workers=workers) as pool:
            pages = list(pool.map(sample, enumerate(project.shots, start=1)))
    return [path for group in pages for path in group]
