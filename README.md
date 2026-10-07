# Media Toolkit

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

Create a JSON project file that points at your own footage and soundtrack. Paths are relative to the manifest unless absolute. Each shot uses a source in-point and source duration; `speed` affects playback duration. The transition on each shot describes how it enters (the first shot's value is ignored). Optional `location_title`, `location_subtitle`, and `location_duration` fields add a timed lower-left place slate. Set `vertical_layout` to `portrait_blur` to preserve a portrait clip in a landscape edit with a softened full-frame background. Set `zoom` between 1.0 and 2.0 to center-crop a shot when a distant subject needs a modest emphasis.

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
     "transition": "fade", "transition_duration": 0.45,
     "location_title": "LAKE CRESCENT", "location_subtitle": "WASHINGTON",
     "location_duration": 2.6, "vertical_layout": "fill"}
  ]
}
```

`grade` supports per-shot contrast, brightness, saturation, RGB color balance, gamma, sharpening, and optional contrast-curve presets (`medium_contrast` or `strong_contrast`) so bright landscapes and night footage can be tuned separately. The renderer applies a widescreen crop with letterbox bars, a subtle vignette, title/location/credit overlays, audio fades, and H.264/AAC output. The optional `music_title`, `music_creator`, `music_source`, `music_license`, and `music_license_url` fields produce a credits sidecar next to the render. Keep source assets and rendered videos outside the public code repository.

`examples/seattle-road-trip.json` is a complete edit recipe with varied pacing, per-shot color, English location slates, a portrait Rainier insert, a Space Needle flyover at night, and clip-specific contrast, gamma, and sharpness. It references footage and music that are intentionally not included; place your own files under the configured media folders or edit the paths before rendering.

## Usage

```sh
tripcut project.json --probe
tripcut project.json
```

Use `--probe` to review clip metadata first. The output is written to a temporary sibling and renamed into place only after FFmpeg succeeds.

## Mask-guided image processing

`tripimage` applies mask-guided local sharpening and an optional lightness lift to existing pixels. It does not synthesize or move scene content, though the edited pixels and JPEG encoding can change their values. Land and water use separate sharpening strengths. A local texture gate leaves smooth areas alone, masks fade inward from their edges to protect shorelines, and the high-pass detail is clipped to limit ringing and halos. This is a detail-enhancement tool, not a dehaze or color-grading filter.

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

`--mask-preview` writes a color overlay so selections can be checked before using the processed image. `--detail-mask` can restrict sharpening to a hand-painted area; `--sky-mask` can also be included in the mask preview. Automatic region masks are available with a compatible MaskFormer ADE20K ONNX model and its `id2label` JSON file:

```sh
tripimage source.jpg preview.jpg \
  --semantic-model models/maskformer-ade20k.onnx \
  --semantic-labels models/ade20k-config.json \
  --mask-preview preview-masks.jpg
```

Painted masks override matching automatic masks. Sharpening defaults are 3.8 for land, 1.8 for water, and a 2 px detail radius; tune them per image and inspect the mask preview, especially around shorelines and small subjects. The input is never overwritten; output dimensions are preserved and available EXIF/ICC metadata is carried forward. Model files are not bundled; keep downloaded models outside the repository and follow their license terms.

## Attribution

If your soundtrack requires attribution, include its license and source details in your project and delivered credits sidecar. The example Tahoe soundtrack mentioned in project files is Kevin MacLeod's “Reunited” under CC BY 4.0; this repository does not redistribute that audio.

## License

MIT. FFmpeg and the media you choose remain subject to their own licenses.
