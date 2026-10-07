"""Rendered-video quality checks and review contact sheets."""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from .models import Project
from .probe import ffprobe
from .timeline import transition_offsets


def review_points(project: Project) -> list[tuple[float, str]]:
    """Return one midpoint per shot, transition midpoint, and the ending."""
    starts = [0.0, *transition_offsets(project)]
    points: list[tuple[float, str]] = []
    for index, (shot, start) in enumerate(zip(project.shots, starts), start=1):
        midpoint = start + project.output_durations[index - 1] / 2
        points.append((midpoint, f"SHOT {index:02d}: {shot.file}"))
        if index > 1 and shot.transition_duration:
            transition_mid = start + shot.transition_duration / 2
            points.append((transition_mid, f"TRANSITION {index - 1:02d}->{index:02d}: {shot.transition}"))
    points.append((max(0.0, project.total_duration - 0.25), "ENDING"))
    return sorted(points)


def verify_render(project: Project, ffmpeg: str | None = None) -> tuple[Path, Path]:
    """Validate the rendered file and create a timeline-indexed review sheet."""
    output = project.output
    if not output.is_file():
        raise FileNotFoundError(f"Rendered video does not exist: {output}")

    metadata = ffprobe(output)
    video = next((stream for stream in metadata.get("streams", [])
                  if stream.get("codec_type") == "video"), None)
    if video is None:
        raise RuntimeError(f"No video stream found in {output}")
    if (int(video.get("width", 0)), int(video.get("height", 0))) != (project.width, project.height):
        raise RuntimeError(
            f"Unexpected output size {video.get('width')}x{video.get('height')}; "
            f"expected {project.width}x{project.height}"
        )
    duration = float(metadata.get("format", {}).get("duration", 0))
    if abs(duration - project.total_duration) > max(0.5, 2 / project.fps):
        raise RuntimeError(
            f"Unexpected output duration {duration:.2f}s; expected about {project.total_duration:.2f}s"
        )

    binary = ffmpeg or shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError("ffmpeg is required; install FFmpeg first")

    points = review_points(project)
    frame_numbers = sorted({max(0, round(time * project.fps)) for time, _ in points})
    select = "+".join(f"eq(n\\,{frame})" for frame in frame_numbers)
    columns = 5
    rows = math.ceil(len(frame_numbers) / columns)
    graph = (
        f"[0:v]split=2[full][review];"
        f"[review]select={select},scale=640:360:force_original_aspect_ratio=decrease,"
        f"pad=640:360:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"tile={columns}x{rows}:padding=12:margin=12:color=0x181818[sheet]"
    )
    sheet = output.with_name(f"{output.stem}_contact_sheet.jpg")
    completed = subprocess.run(
        [binary, "-hide_banner", "-v", "error", "-y", "-i", str(output),
         "-filter_complex", graph,
         "-map", "[full]", "-an", "-f", "null", "-",
         "-map", "[sheet]", "-frames:v", "1", "-q:v", "2", str(sheet)],
        check=True, capture_output=True, text=True,
    )
    if completed.stderr.strip():
        raise RuntimeError("FFmpeg reported errors while decoding the render:\n" + completed.stderr.strip())

    notes = sheet.with_suffix(".txt")
    with notes.open("w", encoding="utf-8") as handle:
        handle.write("Review sheet panels, left to right and top to bottom.\n")
        for panel, (time, label) in enumerate(points, start=1):
            handle.write(f"{panel:02d}  {time:7.2f}s  {label}\n")
    return sheet, notes
