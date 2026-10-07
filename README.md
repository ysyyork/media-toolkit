# Travel Video Toolkit

A small, manifest-driven Python toolkit for assembling cinematic travel edits with FFmpeg. The design separates project data (`models`), timeline math (`timeline`), filter-graph construction (`filtergraph`), rendering (`render`), media inspection (`probe`), attribution (`credits`), and the CLI (`cli`). The FFmpeg invocation is built as an argument list, so filenames with spaces are handled safely.

## Requirements

- Python 3.11+
- FFmpeg and ffprobe in `PATH` (macOS: `brew install ffmpeg`)
- No Python runtime dependencies

## Install

```sh
python3 -m pip install .
```

## Project manifest

Create a JSON project file that points at your own footage and soundtrack. Paths are relative to the manifest unless absolute. Each shot uses a source in-point and source duration; `speed` affects playback duration. The transition on each shot describes how it enters (the first shot's value is ignored).

```json
{
  "title": "A Summer Journey",
  "subtitle": "SUMMER 2026",
  "media_root": "../media",
  "music": "music/reunited.mp3",
  "output": "output/final.mp4",
  "music_title": "Track title",
  "music_creator": "Creator name",
  "music_source": "https://example.com/track",
  "music_license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
  "music_license_url": "https://creativecommons.org/licenses/by/4.0/",
  "width": 3840,
  "height": 2160,
  "fps": 30,
  "aspect_ratio": 2.39,
  "music_start": 10,
  "music_volume": 0.45,
  "threads": 18,
  "preset": "fast",
  "crf": 17,
  "shots": [
    {"file": "lake.mp4", "start": 12.0, "duration": 7.0, "speed": 1.0,
     "grade": {"contrast": 1.1, "brightness": 0, "saturation": 1.06,
                "red": 0.012, "green": 0.008, "blue": -0.018},
     "transition": "fade", "transition_duration": 0.45}
  ]
}
```

`grade` is a restrained per-shot Rec.709 adjustment. The renderer applies a widescreen crop with letterbox bars, a subtle vignette and sharpening, title/credit overlays, audio fades, and H.264/AAC output. The optional `music_title`, `music_creator`, `music_source`, `music_license`, and `music_license_url` fields produce a credits sidecar next to the render. Keep source assets and rendered videos outside the public code repository.

## Usage

```sh
tripcut project.json --probe
tripcut project.json
```

Use `--probe` to review clip metadata first. The output is written to a temporary sibling and renamed into place only after FFmpeg succeeds.

## Attribution

If your soundtrack requires attribution, include its license and source details in your project and delivered credits sidecar. The example Tahoe soundtrack mentioned in project files is Kevin MacLeod's “Reunited” under CC BY 4.0; this repository does not redistribute that audio.

## License

MIT. FFmpeg and the media you choose remain subject to their own licenses.
