"""Command-line entry point."""
from __future__ import annotations
import argparse
from pathlib import Path
from .credits import write_credits
from .models import load_project
from .probe import ffprobe
from .render import FFmpegRenderer


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a travel-video project manifest with FFmpeg")
    parser.add_argument("project", type=Path, help="Path to the project JSON manifest")
    parser.add_argument("--probe", action="store_true", help="Print source metadata without rendering")
    args = parser.parse_args()
    project = load_project(args.project)
    if args.probe:
        for shot in project.shots:
            print(shot.file, ffprobe(project.source_path(shot)).get("format", {}).get("duration"))
        return
    output = FFmpegRenderer().render(project)
    if project.music_title:
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

if __name__ == "__main__":
    main()
