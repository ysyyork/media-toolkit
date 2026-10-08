"""FFmpeg rendering service with validation and atomic output replacement."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from .filtergraph import build_filtergraph
from .models import Project
from .probe import verify_inputs


class FFmpegRenderer:
    def __init__(self, ffmpeg: str | None = None) -> None:
        self.ffmpeg = ffmpeg or shutil.which("ffmpeg") or ""
        if not self.ffmpeg:
            raise RuntimeError("ffmpeg is required; install FFmpeg first")

    def command(self, project: Project, destination: Path) -> list[str]:
        verify_inputs([*(project.source_path(s) for s in project.shots), project.music])
        args = [self.ffmpeg, "-hide_banner", "-y", "-filter_complex_threads", str(project.threads), "-filter_threads", str(project.threads)]
        for shot in project.shots:
            args += ["-threads", "3", "-ss", str(shot.start), "-t", str(shot.duration), "-i", str(project.source_path(shot))]
        args += ["-ss", str(project.music_start), "-i", str(project.music)]
        if project.encoder == "h264_videotoolbox":
            # Never silently fall back to software when a manifest explicitly
            # requests Apple's hardware encoder.
            encoder_args = ["-c:v", project.encoder, "-allow_sw", "0", "-b:v", project.video_bitrate,
                            "-maxrate", project.video_bitrate, "-profile:v", "high", "-level:v", "5.1"]
        else:
            encoder_args = ["-c:v", project.encoder, "-preset", project.preset, "-crf", str(project.crf),
                            "-threads", str(project.threads), "-profile:v", "high", "-level:v", "5.1"]
        args += [
            "-filter_complex", build_filtergraph(project),
            "-map", "[outv]", "-map", "[outa]",
            *encoder_args,
            "-tag:v", "avc1", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-metadata", f"title={project.title}",
            "-metadata", "artist=Travel edit",
            "-shortest", str(destination),
        ]
        return args

    def render(self, project: Project) -> Path:
        project.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = project.output.with_name(project.output.stem + ".rendering" + project.output.suffix)
        temporary.unlink(missing_ok=True)
        subprocess.run(self.command(project, temporary), check=True)
        temporary.replace(project.output)
        return project.output
