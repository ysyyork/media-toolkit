"""Build a time-sampled visual index of every video under a project media root."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .models import Project

VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".mkv", ".avi"}
CELL_WIDTH = 320
CELL_HEIGHT = 180
LABEL_HEIGHT = 30
SHEET_COLUMNS = 8
SHEET_ROWS = 7


def _probe(path: Path, ffprobe: str) -> dict[str, object]:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_name,width,height,avg_frame_rate,codec_type:stream_tags=creation_time",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return {
        "duration_s": float(data.get("format", {}).get("duration", 0)),
        "size_bytes": int(data.get("format", {}).get("size", 0)),
        "codec": video.get("codec_name", ""),
        "width": video.get("width", ""),
        "height": video.get("height", ""),
        "fps": video.get("avg_frame_rate", ""),
        "creation_time": video.get("tags", {}).get("creation_time", ""),
    }


def _extract(path: Path, folder: Path, interval: float, ffmpeg: str, hardware: bool) -> tuple[list[Path], str]:
    pattern = folder / "%05d.jpg"
    filters = f"fps=1/{interval:g},scale={CELL_WIDTH}:{CELL_HEIGHT}:force_original_aspect_ratio=decrease,pad={CELL_WIDTH}:{CELL_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x181818"
    command = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    if hardware:
        command += ["-hwaccel", "videotoolbox"]
    command += ["-i", str(path), "-vf", filters, "-fps_mode", "vfr", "-start_number", "0", "-q:v", "4", "-pix_fmt", "yuvj420p", str(pattern)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode and hardware:
        # Keep the source review usable on clips the hardware decoder cannot handle.
        for old in folder.glob("*.jpg"):
            old.unlink()
        command.remove("videotoolbox")
        command.remove("-hwaccel")
        result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Could not sample {path.name}: {result.stderr.strip()}")
    return sorted(folder.glob("*.jpg")), "videotoolbox" if hardware and "videotoolbox" in command else "software"


def build_source_review(
    project: Project,
    sample_interval: float = 2.0,
    workers: int = 4,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
) -> tuple[list[Path], Path, Path]:
    """Sample all source videos, create paged contact sheets, and write an index.

    On macOS, source decoding uses VideoToolbox where supported. The contact
    sheets sample every ``sample_interval`` seconds and flag clips used by the
    current timeline so unused alternatives can be reviewed efficiently.
    """
    if sample_interval <= 0:
        raise ValueError("sample_interval must be greater than zero")
    if workers < 1:
        raise ValueError("workers must be at least one")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Install Pillow with `python3 -m pip install '.[video-review]'` to build source contact sheets") from exc

    ffmpeg = ffmpeg or shutil.which("ffmpeg")
    ffprobe = ffprobe or shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg and ffprobe are required for source review")

    media_root = project.media_root.resolve()
    output_root = project.output.parent.parent.resolve()
    sources = sorted(
        p for p in media_root.rglob("*")
        if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES
        and not p.resolve().is_relative_to(output_root)
    )
    if not sources:
        raise FileNotFoundError(f"No source videos found under {media_root}")
    used = {Path(shot.file).name.casefold() for shot in project.shots}
    output_dir = project.output.parent / "source_review"
    output_dir.mkdir(parents=True, exist_ok=True)
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    font = ImageFont.truetype(font_path, 12) if Path(font_path).exists() else ImageFont.load_default()
    label_font = ImageFont.truetype(font_path, 10) if Path(font_path).exists() else ImageFont.load_default()
    tiles: list[tuple[Path, str, float, bool]] = []
    records: list[dict[str, object]] = []
    hardware = __import__("sys").platform == "darwin"

    with tempfile.TemporaryDirectory(prefix="tripcut-source-review-") as temp_name:
        temp_root = Path(temp_name)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_probe, path, ffprobe): path for path in sources}
            metadata_by_path: dict[Path, dict[str, object]] = {}
            for future in as_completed(futures):
                metadata_by_path[futures[future]] = future.result()

        frames_by_path: dict[Path, tuple[list[Path], str]] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {}
            for number, path in enumerate(sources, start=1):
                folder = temp_root / f"{number:03d}"
                folder.mkdir()
                futures[pool.submit(_extract, path, folder, sample_interval, ffmpeg, hardware)] = path
            for complete, future in enumerate(as_completed(futures), start=1):
                frames_by_path[futures[future]] = future.result()
                print(f"Sampled {complete}/{len(sources)} source videos", flush=True)

        for path in sources:
            frames, decoder = frames_by_path[path]
            is_used = path.name.casefold() in used
            info = metadata_by_path[path]
            records.append({
                "file": str(path), "used_in_timeline": is_used,
                **info, "samples": len(frames), "decoder": decoder,
            })
            for frame_index, frame in enumerate(frames):
                tiles.append((frame, path.name, frame_index * sample_interval, is_used))

        per_sheet = SHEET_COLUMNS * SHEET_ROWS
        sheets: list[Path] = []
        map_path = output_dir / "source_review_index.txt"
        with map_path.open("w", encoding="utf-8") as map_file:
            map_file.write(f"Source review: {len(sources)} videos under {media_root}; one frame every {sample_interval:g}s.\n")
            map_file.write("Panels run left to right, then top to bottom. Each frame label gives source filename and time. USED marks clips in the current edit.\n")
            for page_start in range(0, len(tiles), per_sheet):
                page_tiles = tiles[page_start:page_start + per_sheet]
                rows = (len(page_tiles) + SHEET_COLUMNS - 1) // SHEET_COLUMNS
                sheet = Image.new("RGB", (SHEET_COLUMNS * CELL_WIDTH, rows * (CELL_HEIGHT + LABEL_HEIGHT)), "#181818")
                draw = ImageDraw.Draw(sheet)
                for local_index, (frame_path, filename, seconds, is_used) in enumerate(page_tiles):
                    col, row = local_index % SHEET_COLUMNS, local_index // SHEET_COLUMNS
                    x, y = col * CELL_WIDTH, row * (CELL_HEIGHT + LABEL_HEIGHT)
                    with Image.open(frame_path) as frame:
                        sheet.paste(frame.convert("RGB"), (x, y + LABEL_HEIGHT))
                    status = "USED" if is_used else "UNUSED"
                    color = "#e9c46a" if is_used else "#ffffff"
                    draw.text((x + 5, y + 2), f"{filename}  [{status}]", fill=color, font=label_font)
                    mm, ss = divmod(int(seconds), 60)
                    hh, mm = divmod(mm, 60)
                    draw.text((x + 5, y + 15), f"source {hh:02}:{mm:02}:{ss:02}", fill="#cccccc", font=label_font)
                    map_file.write(f"{page_start + local_index + 1:05d}  {filename}  {seconds:.2f}s  {status}\n")
                output = output_dir / f"source_review_{len(sheets) + 1:03d}.jpg"
                sheet.save(output, quality=92, optimize=True)
                sheets.append(output)

    csv_path = output_dir / "source_review_index.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return sheets, csv_path, map_path
