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


def build_filtergraph(project: Project) -> str:
    width, height = project.width, project.height
    image_height = round(width / project.aspect_ratio)
    image_height -= image_height % 2
    crop_y = (height - image_height) // 2
    filters: list[str] = []
    for i, shot in enumerate(project.shots):
        grade = shot.grade
        y = crop_y if shot.crop_y is None else shot.crop_y
        filters.append(
            f"[{i}:v]setpts=PTS-STARTPTS,setpts=PTS/{_f(shot.speed)},"
            f"eq=contrast={_f(grade.contrast)}:brightness={_f(grade.brightness)}:saturation={_f(grade.saturation)},"
            f"colorbalance=rs={_f(grade.red*.6)}:gs={_f(grade.green*.6)}:bs={_f(grade.blue*.6)}:"
            f"rm={_f(grade.red*.4)}:gm={_f(grade.green*.4)}:bm={_f(grade.blue*.4)}:"
            f"rh={_f(grade.red)}:gh={_f(grade.green)}:bh={_f(grade.blue)},"
            f"scale={width}:{height}:flags=lanczos,crop={width}:{image_height}:0:{y},"
            f"pad={width}:{height}:0:{crop_y}:black,vignette=PI/5,"
            "unsharp=5:5:0.28:3:3:0.0,fps=" + str(project.fps) + ",setsar=1,format=yuv420p"
            f"[v{i}]"
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
    filters.append(
        f"[{previous}]"
        "drawtext=fontfile=/System/Library/Fonts/Supplemental/Georgia.ttf:"
        f"text='{_drawtext(project.title)}':fontcolor=white:fontsize=112:shadowcolor=black@0.65:shadowx=2:shadowy=2:"
        f"x=(w-text_w)/2:y={crop_y+round(image_height*.69)}:enable='between(t,0,4.8)',"
        "drawtext=fontfile=/System/Library/Fonts/Supplemental/Georgia.ttf:"
        f"text='{_drawtext(project.subtitle)}':fontcolor=white:fontsize=44:shadowcolor=black@0.65:shadowx=1:shadowy=1:"
        f"x=(w-text_w)/2:y={crop_y+round(image_height*.79)}:enable='between(t,0,4.8)',"
        "drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:"
        f"text='Music\\: Reunited - Kevin MacLeod | CC BY 4.0':fontcolor=white:fontsize=32:"
        f"x=108:y={height-84}:enable='between(t,{_f(credits_start)},{_f(total)})',"
        f"fade=t=in:st=0:d=1.0,fade=t=out:st={_f(fade_out)}:d=0.85,format=yuv420p[outv]"
    )
    audio_index = len(project.shots)
    filters.append(
        f"[{audio_index}:a]atrim=duration={_f(total)},asetpts=PTS-STARTPTS,"
        f"volume={_f(project.music_volume)},loudnorm=I=-19:TP=-1.5:LRA=11,"
        "afade=t=in:st=0:d=1.1,"
        f"afade=t=out:st={_f(fade_out)}:d=0.85[outa]"
    )
    return ";".join(filters)
