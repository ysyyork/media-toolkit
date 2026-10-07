# Travel Media Toolkit

A small Python toolkit for assembling cinematic travel edits with FFmpeg and making mask-guided photo adjustments. Video project data (`models`), timeline math (`timeline`), filter-graph construction (`filtergraph`), rendering (`render`), media inspection (`probe`), attribution (`credits`), and the video CLI (`cli`) stay separate from image processing (`image_processing`, `image_cli`). FFmpeg invocations use argument lists, so filenames with spaces are handled safely.

## Requirements

- Python 3.11+
- FFmpeg and ffprobe in `PATH` (macOS: `brew install ffmpeg`)
- No Python dependencies are needed for video-only use

## Install

```sh
python3 -m pip install .
```

Install the optional photo-processing dependencies when using `tripimage`:

```sh
python3 -m pip install '.[image]'
```

For automatic ADE20K region masks with a compatible MaskFormer ONNX export, also install:

```sh
python3 -m pip install '.[image,semantic]'
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

## Mask-guided image processing

`tripimage` applies local detail sharpening and an optional highlight lift to existing pixels. It never creates, removes, or relocates image content. Land and water use separate sharpening strengths; smooth regions and strong boundaries are protected to reduce noise and halos.

The most precise workflow is to paint grayscale masks in an image editor such as Photoshop and export them at any size. White selects the adjustment area, black protects it, and gray gives a soft blend. Use a land mask for trees and rocks, a water mask for ripples, a boat mask to protect a subject, and a highlight mask to lift only reflected light:

```sh
tripimage source.jpg preview.jpg \
  --land-mask masks/land.png \
  --water-mask masks/water.png \
  --boat-mask masks/boat.png \
  --highlight-mask masks/reflection.png \
  --highlight-lightness 40 \
  --land-sharpness 3.8 \
  --water-sharpness 1.8 \
  --mask-preview preview-masks.jpg
```

`--mask-preview` writes a color overlay so selections can be checked before using the processed image. Automatic region masks are available with a compatible MaskFormer ADE20K ONNX model and its `id2label` JSON file:

```sh
tripimage source.jpg preview.jpg \
  --semantic-model models/maskformer-ade20k.onnx \
  --semantic-labels models/ade20k-config.json \
  --mask-preview preview-masks.jpg
```

Painted masks override matching automatic masks. The input is never overwritten. Model files are not bundled; keep downloaded models outside the repository and follow their license terms.

## Attribution

If your soundtrack requires attribution, include its license and source details in your project and delivered credits sidecar. The example Tahoe soundtrack mentioned in project files is Kevin MacLeod's “Reunited” under CC BY 4.0; this repository does not redistribute that audio.

## License

MIT. FFmpeg and the media you choose remain subject to their own licenses.
