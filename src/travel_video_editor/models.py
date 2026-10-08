"""Typed project configuration and validation."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any
from .looks import get_look


@dataclass(frozen=True)
class Grade:
    contrast: float = 1.10
    brightness: float = 0.0
    saturation: float = 1.06
    red: float = 0.012
    green: float = 0.008
    blue: float = -0.018
    shadow_red: float = 0.0
    shadow_green: float = 0.0
    shadow_blue: float = 0.0
    midtone_red: float = 0.0
    midtone_green: float = 0.0
    midtone_blue: float = 0.0
    highlight_red: float = 0.0
    highlight_green: float = 0.0
    highlight_blue: float = 0.0
    gamma: float = 1.0
    gamma_weight: float = 1.0
    sharpness: float = 0.24
    curve: str = "none"

    def __post_init__(self) -> None:
        if self.curve not in {"none", "medium_contrast", "strong_contrast", "soft_film"}:
            raise ValueError(f"Unsupported curve preset: {self.curve}")


@dataclass(frozen=True)
class Shot:
    file: str
    start: float
    duration: float
    speed: float = 1.0
    grade: Grade = field(default_factory=Grade)
    transition: str = "fade"
    transition_duration: float = 0.45
    crop_y: int | None = None
    location_title: str = ""
    location_subtitle: str = ""
    location_duration: float = 2.6
    vertical_layout: str = "fill"
    zoom: float = 1.0
    zoom_end: float | None = None
    center_x: float = 0.5
    center_x_end: float | None = None
    source_file: str = ""


@dataclass(frozen=True)
class Project:
    title: str
    subtitle: str
    media_root: Path
    music: Path
    output: Path
    shots: tuple[Shot, ...]
    music_title: str = ""
    music_creator: str = ""
    music_source: str = ""
    music_license: str = ""
    music_license_url: str = ""
    width: int = 3840
    height: int = 2160
    fps: int = 30
    aspect_ratio: float = 2.39
    music_start: float = 10.0
    music_volume: float = 0.45
    threads: int = 18
    preset: str = "fast"
    crf: int = 17
    encoder: str = "libx264"
    video_bitrate: str = "45M"
    grade_preset: str = "neutral"
    required_shots: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.shots:
            raise ValueError("Project must contain at least one shot")
        included = {name for shot in self.shots for name in (shot.file, shot.source_file) if name}
        missing = sorted(set(self.required_shots) - included)
        if missing:
            raise ValueError("Required highlight shot(s) missing from timeline: " + ", ".join(missing))
        if self.width < 2 or self.height < 2 or self.fps < 1:
            raise ValueError("Output dimensions and frame rate must be positive")
        for shot in self.shots:
            if shot.start < 0 or shot.duration <= 0 or shot.speed <= 0:
                raise ValueError(f"Invalid timing in shot {shot.file}")
            if shot.transition_duration < 0 or shot.transition not in {
                "fade", "dissolve", "smoothleft", "smoothright", "fadeblack"
            }:
                raise ValueError(f"Unsupported transition in shot {shot.file}")
            if shot.vertical_layout not in {"fill", "portrait_blur"}:
                raise ValueError(f"Unsupported vertical layout in shot {shot.file}")
            if not 1.0 <= shot.zoom <= 2.0:
                raise ValueError(f"Zoom must be between 1.0 and 2.0 in shot {shot.file}")
            if shot.zoom_end is not None and not 1.0 <= shot.zoom_end <= 2.0:
                raise ValueError(f"Ending zoom must be between 1.0 and 2.0 in shot {shot.file}")
            if not 0.0 <= shot.center_x <= 1.0 or (
                shot.center_x_end is not None and not 0.0 <= shot.center_x_end <= 1.0
            ):
                raise ValueError(f"Crop center must be between 0 and 1 in shot {shot.file}")
        if self.threads < 1 or not 0 <= self.crf <= 51:
            raise ValueError("Invalid encoder settings")
        if self.encoder not in {"libx264", "h264_videotoolbox"}:
            raise ValueError("Unsupported video encoder; choose libx264 or h264_videotoolbox")

    @property
    def output_durations(self) -> list[float]:
        return [shot.duration / shot.speed for shot in self.shots]

    @property
    def total_duration(self) -> float:
        return sum(self.output_durations) - sum(
            shot.transition_duration for shot in self.shots[1:]
        )

    def source_path(self, shot: Shot) -> Path:
        return self.media_root / shot.file


def load_project(path: Path) -> Project:
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    base = path.resolve().parent
    media_root = (base / raw.get("media_root", "..")).resolve()
    music = (base / raw["music"]).resolve()
    output = (base / raw["output"]).resolve()
    grade_preset = raw.get("grade_preset", "neutral")
    base_grade = get_look(grade_preset)
    shots = tuple(
        Shot(
            file=item["file"],
            start=float(item["start"]),
            duration=float(item["duration"]),
            speed=float(item.get("speed", 1.0)),
            grade=Grade(**{**base_grade, **item.get("grade", {})}),
            transition=item.get("transition", "fade"),
            transition_duration=float(item.get("transition_duration", 0.45)),
            crop_y=item.get("crop_y"),
            location_title=item.get("location_title", ""),
            location_subtitle=item.get("location_subtitle", ""),
            location_duration=float(item.get("location_duration", 2.6)),
            vertical_layout=item.get("vertical_layout", "fill"),
            zoom=float(item.get("zoom", 1.0)),
            zoom_end=(float(item["zoom_end"]) if item.get("zoom_end") is not None else None),
            center_x=float(item.get("center_x", 0.5)),
            center_x_end=(float(item["center_x_end"]) if item.get("center_x_end") is not None else None),
            source_file=item.get("source_file", ""),
        )
        for item in raw["shots"]
    )
    return Project(
        title=raw.get("title", "A Summer Journey"),
        subtitle=raw.get("subtitle", "SUMMER 2026"),
        media_root=media_root,
        music=music,
        output=output,
        shots=shots,
        music_title=raw.get("music_title", ""),
        music_creator=raw.get("music_creator", ""),
        music_source=raw.get("music_source", ""),
        music_license=raw.get("music_license", ""),
        music_license_url=raw.get("music_license_url", ""),
        width=int(raw.get("width", 3840)),
        height=int(raw.get("height", 2160)),
        fps=int(raw.get("fps", 30)),
        aspect_ratio=float(raw.get("aspect_ratio", 2.39)),
        music_start=float(raw.get("music_start", 10)),
        music_volume=float(raw.get("music_volume", 0.45)),
        threads=int(raw.get("threads", 18)),
        preset=raw.get("preset", "fast"),
        crf=int(raw.get("crf", 17)),
        encoder=raw.get("encoder", "libx264"),
        video_bitrate=raw.get("video_bitrate", "45M"),
        grade_preset=grade_preset,
        required_shots=tuple(raw.get("required_shots", ())),
    )
