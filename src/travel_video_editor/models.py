"""Typed project configuration and validation."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Grade:
    contrast: float = 1.10
    brightness: float = 0.0
    saturation: float = 1.06
    red: float = 0.012
    green: float = 0.008
    blue: float = -0.018


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

    def __post_init__(self) -> None:
        if not self.shots:
            raise ValueError("Project must contain at least one shot")
        if self.width < 2 or self.height < 2 or self.fps < 1:
            raise ValueError("Output dimensions and frame rate must be positive")
        for shot in self.shots:
            if shot.start < 0 or shot.duration <= 0 or shot.speed <= 0:
                raise ValueError(f"Invalid timing in shot {shot.file}")
            if shot.transition_duration < 0 or shot.transition not in {
                "fade", "dissolve", "smoothleft", "smoothright", "fadeblack"
            }:
                raise ValueError(f"Unsupported transition in shot {shot.file}")
        if self.threads < 1 or not 0 <= self.crf <= 51:
            raise ValueError("Invalid encoder settings")

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
    shots = tuple(
        Shot(
            file=item["file"],
            start=float(item["start"]),
            duration=float(item["duration"]),
            speed=float(item.get("speed", 1.0)),
            grade=Grade(**item.get("grade", {})),
            transition=item.get("transition", "fade"),
            transition_duration=float(item.get("transition_duration", 0.45)),
            crop_y=item.get("crop_y"),
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
    )
