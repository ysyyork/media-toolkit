"""Build the FFmpeg filter graph from the typed edit timeline."""
from __future__ import annotations
from .models import Project, Shot
from .timeline import transition_offsets

_DISPLAY_FONT = "/System/Library/Fonts/Supplemental/Didot.ttc"
_TEXT_FONT = "/System/Library/Fonts/Avenir.ttc"


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
    scale_factor = min(width / 3840, height / 2160)
    px = lambda value: max(1, round(value * scale_factor))
    image_height = round(width / project.aspect_ratio)
    image_height -= image_height % 2
    crop_y = (height - image_height) // 2
    filters: list[str] = []
    for i, shot in enumerate(project.shots):
        grade = shot.grade
        y = crop_y if shot.crop_y is None else shot.crop_y
        if grade.curve == "soft_film":
            # A restrained print-style S curve: deepen lower mids, give the
            # landscape midtones more separation, and roll off the top end.
            curve_filter = ",curves=master='0/0.012 0.10/0.085 0.25/0.23 0.50/0.50 0.75/0.82 0.90/0.94 1/0.985'"
        else:
            curve_filter = "" if grade.curve == "none" else f",curves=preset={grade.curve}"
        timed_grade = (
            f"setpts=PTS-STARTPTS,setpts=PTS/{_f(shot.speed)},"
            f"eq=contrast={_f(grade.contrast)}:brightness={_f(grade.brightness)}:saturation={_f(grade.saturation)}:gamma={_f(grade.gamma)}:gamma_weight={_f(grade.gamma_weight)}{curve_filter},"
            f"colorbalance=rs={_f(grade.red*.6+grade.shadow_red)}:gs={_f(grade.green*.6+grade.shadow_green)}:bs={_f(grade.blue*.6+grade.shadow_blue)}:"
            f"rm={_f(grade.red*.4+grade.midtone_red)}:gm={_f(grade.green*.4+grade.midtone_green)}:bm={_f(grade.blue*.4+grade.midtone_blue)}:"
            f"rh={_f(grade.red+grade.highlight_red)}:gh={_f(grade.green+grade.highlight_green)}:bh={_f(grade.blue+grade.highlight_blue)}"
        )
        if shot.vertical_layout == "portrait_blur":
            filters.extend([
                f"[{i}:v]{timed_grade},split=2[bgraw{i}][fgraw{i}]",
                f"[bgraw{i}]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},boxblur=28:10,eq=brightness=-0.10:saturation=0.72[bg{i}]",
                f"[fgraw{i}]scale={px(1440)}:-2:flags=lanczos,crop={px(1440)}:{height}:0:(in_h-{height})/2[fg{i}]",
                f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2,vignette=PI/8,"
                f"unsharp=5:5:{_f(grade.sharpness)}:3:3:0.0,fps={project.fps},setsar=1,format=yuv420p[v{i}]",
            ])
        else:
            if shot.zoom_end is not None and shot.zoom_end != shot.zoom:
                clip_duration = shot.duration / shot.speed
                zoom = f"{_f(shot.zoom)}+{_f(shot.zoom_end-shot.zoom)}*t/{_f(clip_duration)}"
                center_end = shot.center_x if shot.center_x_end is None else shot.center_x_end
                center = f"{_f(shot.center_x)}+{_f(center_end-shot.center_x)}*t/{_f(clip_duration)}"
                scale_crop = (
                    f"scale=w='trunc({width}*({zoom})/2)*2':"
                    f"h='trunc({height}*({zoom})/2)*2':eval=frame:flags=lanczos,"
                    f"crop={width}:{image_height}:'(iw-{width})*({center})':(ih-{image_height})/2"
                )
            elif shot.zoom > 1.0:
                scaled_width = round(width * shot.zoom)
                scaled_height = round(height * shot.zoom)
                scale_crop = (
                    f"scale={scaled_width}:{scaled_height}:flags=lanczos,"
                    f"crop={width}:{image_height}:(iw-{width})/2:(ih-{image_height})/2"
                )
            else:
                scale_crop = (
                    f"scale={width}:{height}:flags=lanczos,"
                    f"crop={width}:{image_height}:0:{y}"
                )
            filters.append(
                f"[{i}:v]{timed_grade},{scale_crop},pad={width}:{height}:0:{crop_y}:black,"
                f"vignette=PI/8,unsharp=5:5:{_f(grade.sharpness)}:3:3:0.0,fps={project.fps},setsar=1,format=yuv420p[v{i}]"
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
        f"drawtext=fontfile={_DISPLAY_FONT}:"
        f"text='{_drawtext(project.title)}':fontcolor=0xF8F4EC:fontsize={px(108)}:shadowcolor=black@0.48:shadowx={px(2)}:shadowy={px(2)}:"
        f"x={title_x}:y={title_y}:enable='between(t,0,4.0)',"
        f"drawtext=fontfile={_TEXT_FONT}:"
        f"text='{_drawtext(project.subtitle)}':fontcolor=0xF3E9D5:fontsize={px(34)}:shadowcolor=black@0.48:shadowx={px(1)}:shadowy={px(1)}:"
        f"x={title_x}:y={title_y+px(100)}:enable='between(t,0,4.0)'"
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
            f"drawbox=x={px(108)}:y={height-px(278)}:w={px(5)}:h={px(88)}:color=0xD7B978@0.96:t=fill:enable='{cue}'",
            f"drawtext=fontfile={_DISPLAY_FONT}:"
            f"text='{_drawtext(shot.location_title)}':fontcolor=0xFFF9EF:fontsize={px(66)}:"
            f"shadowcolor=black@0.52:shadowx={px(2)}:shadowy={px(2)}:x={px(137)}:y={height-px(280)}:enable='{cue}',"
            f"drawtext=fontfile={_TEXT_FONT}:"
            f"text='{_drawtext(shot.location_subtitle)}':fontcolor=0xF3E9D5@0.92:fontsize={px(30)}:"
            f"shadowcolor=black@0.52:shadowx={px(1)}:shadowy={px(2)}:x={px(137)}:y={height-px(202)}:enable='{cue}'"
        ])

    overlays.append(
        f"drawtext=fontfile={_TEXT_FONT}:"
        f"text='{_drawtext(music_credit)}':fontcolor=0xF3E9D5:fontsize={px(28)}:"
        f"x={px(108)}:y={height-px(84)}:enable='between(t,{_f(credits_start)},{_f(total)})'"
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
