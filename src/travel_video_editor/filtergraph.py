"""Build the FFmpeg filter graph from the typed edit timeline."""
from __future__ import annotations
from .models import Project, Shot
from .timeline import transition_offsets


def _f(value: float) -> str:
    return f"{value:.5f}".rstrip("0").rstrip(".")


def _drawtext(value: str) -> str:
    """Escape text values for FFmpeg's filtergraph/drawtext parser."""
    return (value.replace("\\", "\\\\").replace("'", "\\'")
            .replace(":", "\\:").replace(",", "\\,"))


def _license_credit(value: str) -> str:
    """Return a compact on-screen label for common Creative Commons licenses."""
    normalized = value.casefold()
    if "noncommercial" in normalized and "4.0" in normalized:
        return "CC BY-NC 4.0"
    if "attribution 4.0" in normalized:
        return "CC BY 4.0"
    return value


def build_filtergraph(project: Project) -> str:
    width, height = project.width, project.height
    image_height = round(width / project.aspect_ratio)
    image_height -= image_height % 2
    crop_y = (height - image_height) // 2
    filters: list[str] = []
    for i, shot in enumerate(project.shots):
        grade = shot.grade
        y = crop_y if shot.crop_y is None else shot.crop_y
        timed_grade = (
            f"setpts=PTS-STARTPTS,setpts=PTS/{_f(shot.speed)},"
            f"eq=contrast={_f(grade.contrast)}:brightness={_f(grade.brightness)}:saturation={_f(grade.saturation)},"
            f"colorbalance=rs={_f(grade.red*.6)}:gs={_f(grade.green*.6)}:bs={_f(grade.blue*.6)}:"
            f"rm={_f(grade.red*.4)}:gm={_f(grade.green*.4)}:bm={_f(grade.blue*.4)}:"
            f"rh={_f(grade.red)}:gh={_f(grade.green)}:bh={_f(grade.blue)}"
        )
        if shot.vertical_layout == "portrait_blur":
            filters.extend([
                f"[{i}:v]{timed_grade},split=2[bgraw{i}][fgraw{i}]",
                f"[bgraw{i}]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},boxblur=28:10,eq=brightness=-0.10:saturation=0.72[bg{i}]",
                f"[fgraw{i}]scale=1440:-2:flags=lanczos,crop=1440:{height}:0:(in_h-{height})/2[fg{i}]",
                f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2,vignette=PI/8,"
                f"unsharp=5:5:0.20:3:3:0.0,fps={project.fps},setsar=1,format=yuv420p[v{i}]",
            ])
        else:
            filters.append(
                f"[{i}:v]{timed_grade},scale={width}:{height}:flags=lanczos,"
                f"crop={width}:{image_height}:0:{y},pad={width}:{height}:0:{crop_y}:black,"
                f"vignette=PI/8,unsharp=5:5:0.20:3:3:0.0,fps={project.fps},setsar=1,format=yuv420p[v{i}]"
            )

    previous = "v0"
    for i in range(1, len(project.shots)):
        shot = project.shots[i]
        filters.append(
            f"[{previous}][v{i}]xfade=transition={shot.transition}:"
            f"duration={_f(shot.transition_duration)}:offset={_f(transition_offsets(project)[i-1])}[x{i}]"
        )
        previous = f"x{i}"

    total = project.total_duration
    fade_out = max(0.0, total - 0.85)
    credits_start = max(0.0, total - 4.2)
    title_x = round(width * 0.065)
    title_y = crop_y + round(image_height * 0.11)
    music_credit = (
        "Music: " + project.music_title + " - " + project.music_creator
        + " | " + _license_credit(project.music_license)
    )
    overlays = [
        "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:"
        f"text='{_drawtext(project.title)}':fontcolor=white:fontsize=82:shadowcolor=black@0.48:shadowx=2:shadowy=2:"
        f"x={title_x}:y={title_y}:enable='between(t,0,4.0)',"
        "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:"
        f"text='{_drawtext(project.subtitle)}':fontcolor=white:fontsize=38:shadowcolor=black@0.48:shadowx=1:shadowy=1:"
        f"x={title_x}:y={title_y+100}:enable='between(t,0,4.0)'"
    ]

    # Place restrained location slates in the lower left, timed to each selected shot.
    shot_starts = [0.0, *transition_offsets(project)]
    for shot, start in zip(project.shots, shot_starts):
        if not shot.location_title:
            continue
        cue_start = start + (0.18 if start else 0.22)
        cue_end = min(start + shot.location_duration, start + shot.duration / shot.speed - 0.18)
        if cue_end <= cue_start:
            continue
        cue = f"between(t,{_f(cue_start)},{_f(cue_end)})"
        overlays.extend([
            f"drawbox=x=108:y={height-258}:w=5:h=78:color=0xD7B978@0.92:t=fill:enable='{cue}'",
            "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:"
            f"text='{_drawtext(shot.location_title)}':fontcolor=white:fontsize=48:"
            f"shadowcolor=black@0.38:shadowx=1:shadowy=2:x=137:y={height-258}:enable='{cue}',"
            "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:"
            f"text='{_drawtext(shot.location_subtitle)}':fontcolor=white@0.88:fontsize=26:"
            f"shadowcolor=black@0.38:shadowx=1:shadowy=2:x=137:y={height-194}:enable='{cue}'"
        ])

    overlays.append(
        "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:"
        f"text='{_drawtext(music_credit)}':fontcolor=white:fontsize=32:"
        f"x=108:y={height-84}:enable='between(t,{_f(credits_start)},{_f(total)})'"
    )
    filters.append(
        f"[{previous}]" + ",".join(overlays)
        + f",fade=t=in:st=0:d=1.0,fade=t=out:st={_f(fade_out)}:d=0.85,format=yuv420p[outv]"
    )
    audio_index = len(project.shots)
    filters.append(
        f"[{audio_index}:a]atrim=duration={_f(total)},asetpts=PTS-STARTPTS,"
        f"volume={_f(project.music_volume)},loudnorm=I=-19:TP=-1.5:LRA=11,"
        "afade=t=in:st=0:d=1.1,"
        f"afade=t=out:st={_f(fade_out)}:d=0.85[outa]"
    )
    return ";".join(filters)
