"""Command-line entry point."""
from __future__ import annotations
import argparse
from dataclasses import replace
from pathlib import Path
from .credits import write_credits
from .models import load_project
from .probe import ffprobe
from .qa import verify_render
from .render import FFmpegRenderer


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a travel-video project manifest with FFmpeg")
    parser.add_argument("project", type=Path, help="Path to the project JSON manifest")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--probe", action="store_true", help="Print source metadata without rendering")
    actions.add_argument("--qc", action="store_true", help="Verify the existing render and make a review contact sheet")
    actions.add_argument("--preview", action="store_true", help="Render a 720p review copy with Apple VideoToolbox on macOS")
    args = parser.parse_args()
    project = load_project(args.project)
    if args.probe:
        for shot in project.shots:
            print(shot.file, ffprobe(project.source_path(shot)).get("format", {}).get("duration"))
        return
    if args.qc:
        sheet, notes = verify_render(project)
        print(f"Verified {project.output}")
        print(f"Review sheet: {sheet}")
        print(f"Panel map: {notes}")
        return
    if args.preview:
        project = replace(
            project,
            width=1280,
            height=720,
            output=project.output.with_name(project.output.stem + "_preview.mp4"),
            encoder="h264_videotoolbox",
            video_bitrate="6M",
        )
    output = FFmpegRenderer().render(project)
    if project.music_title and not args.preview:
        write_credits(
            output.parent / "credits.txt",
            project.music_title,
            project.music_creator,
            project.music_source,
            project.music_license,
            project.music_license_url,
            project.music_start,
        )
    print(f"Rendered {output} ({project.total_duration:.2f}s)")
    sheet, notes = verify_render(project)
    print(f"Review sheet: {sheet}")
    print(f"Panel map: {notes}")

if __name__ == "__main__":
    main()
