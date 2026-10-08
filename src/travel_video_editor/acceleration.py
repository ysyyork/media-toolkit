"""Report FFmpeg's acceleration capabilities without implying active GPU use."""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AccelerationReport:
    platform: str
    architecture: str
    ffmpeg: str
    hardware_accel_apis: tuple[str, ...]
    hardware_video_encoders: tuple[str, ...]
    hardware_video_filters: tuple[str, ...]
    final_render_filtering: str
    coreimage_note: str


def _output(binary: str, *args: str) -> str:
    result = subprocess.run(
        [binary, "-hide_banner", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Could not inspect FFmpeg ({' '.join(args)}): {detail}")
    return result.stdout + result.stderr


def _listed_names(output: str) -> set[str]:
    """Parse FFmpeg's aligned inventory rows, ignoring headings and prose."""
    names: set[str] = set()
    for line in output.splitlines():
        # Encoders/decoders use six capability flags; filters use three.
        match = re.match(r"^\s*[A-Z.]{3}(?:[A-Z.]{3})?\s+([A-Za-z0-9_]+)(?:\s|$)", line)
        if match:
            names.add(match.group(1))
    return names


def inspect_acceleration(ffmpeg: str | None = None) -> AccelerationReport:
    """Inspect compiled FFmpeg capabilities; this does not measure live GPU use."""
    binary = ffmpeg or shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError("FFmpeg is required; install it and ensure it is in PATH")

    version = _output(binary, "-version").splitlines()
    encoders = _listed_names(_output(binary, "-encoders"))
    filters = _listed_names(_output(binary, "-filters"))
    hwaccels = set(_output(binary, "-hwaccels").split())
    hwaccel_names = {"videotoolbox", "cuda", "vaapi", "qsv", "d3d11va", "dxva2", "vdpau", "amf"}

    known_encoders = (
        "h264_videotoolbox", "hevc_videotoolbox", "prores_videotoolbox",
        "h264_nvenc", "hevc_nvenc", "av1_nvenc", "h264_qsv", "hevc_qsv",
        "h264_vaapi", "hevc_vaapi", "h264_amf", "hevc_amf",
    )
    known_filters = ("coreimage", "scale_vt", "transpose_vt", "scale_cuda", "scale_vaapi", "scale_qsv")
    encoders_found = tuple(name for name in known_encoders if name in encoders)
    filters_found = tuple(name for name in known_filters if name in filters)
    coreimage_note = (
        "FFmpeg Core Image is available, but its wrapper uses OpenGL and copies bitmap frames "
        "back to CPU memory; hardware rendering is not guaranteed. It is not enabled by tripcut."
        if "coreimage" in filters
        else "FFmpeg Core Image filter is not present in this build."
    )
    filter_status = (
        "The current tripcut filter graph (grading, scaling/cropping, titles, transitions, and "
        "sharpening) runs through FFmpeg software filters. VideoToolbox currently accelerates "
        "encoding only; no Metal-resident filter backend is implemented."
    )
    return AccelerationReport(
        platform=sys.platform,
        architecture=platform.machine(),
        ffmpeg=version[0] if version else binary,
        hardware_accel_apis=tuple(sorted(hwaccels & hwaccel_names)),
        hardware_video_encoders=encoders_found,
        hardware_video_filters=filters_found,
        final_render_filtering=filter_status,
        coreimage_note=coreimage_note,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect FFmpeg hardware-acceleration support; this does not measure live GPU use."
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    args = parser.parse_args()
    report = inspect_acceleration()
    if args.json:
        print(json.dumps(asdict(report), indent=2))
        return

    print(f"Platform: {report.platform} ({report.architecture})")
    print(f"FFmpeg: {report.ffmpeg}")
    print("Hardware decode APIs: " + (", ".join(report.hardware_accel_apis) or "none detected"))
    print("Hardware video encoders: " + (", ".join(report.hardware_video_encoders) or "none detected"))
    print("GPU-related filters compiled in: " + (", ".join(report.hardware_video_filters) or "none detected"))
    print("Render filter stage: " + report.final_render_filtering)
    print("Core Image: " + report.coreimage_note)


if __name__ == "__main__":
    main()
