# Media Toolkit

A small Python toolkit with two distinct workflows: cinematic video assembly through FFmpeg (`tripcut`) and mask-guided still-photo detail work (`tripimage`). Photo and video manifests, processing, and outputs stay separate. `tripimage` currently provides selective sharpening and masked lightness lift; it is not a full photo color-grading editor. See [the photo workflow](docs/image-workflow.md) for the end-to-end process, quality gates, and current limits. Project-level editing instructions live in `AGENTS.md`.

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

The same optional dependencies provide `tripdehaze`, a restrained preprocessing command for reducing haze in one selected video range. It uses OpenCV and FFmpeg; on supported Macs, the intermediate is encoded with VideoToolbox.

```sh
tripdehaze source.mp4 output/dehazed-range.mp4 --start 16 --duration 3.5
```

Use the resulting intermediate for that shot in the edit manifest, then make a preview and inspect sky, sunlit detail, dark foliage, and motion for halos or frame-to-frame pumping. This is a shot-level correction, not a global filter; lower `--strength` if it looks harsh.

For automatic ADE20K region masks with a compatible MaskFormer ONNX export, also install:

```sh
python3 -m pip install '.[image,semantic]'
```

## Project manifest

Create a JSON project file that points at your own footage and soundtrack. Paths are relative to the manifest unless absolute. Each shot uses a source in-point and source duration; `speed` affects playback duration. The transition on each shot describes how it enters (the first shot's value is ignored). Optional `location_title`, `location_subtitle`, and `location_duration` fields add a timed lower-left place slate. Set `vertical_layout` to `portrait_blur` to preserve a portrait clip in a landscape edit with a softened full-frame background. Set `zoom` between 1.0 and 2.0 to center-crop a shot when a distant subject needs a modest emphasis.

Set a project-level `grade_preset` to `artistic_neutral` for a soft-neutral, colorful base, or `summer_film_pop` for a warmer, punchier travel look. Judge white balance and exposure per shot: a sunset can stay warm, forest greens should stay natural, and a blue-hour coast can remain cool. Use per-shot `grade` overrides when one shot needs haze reduction, highlight recovery, shadow lift, a temperature correction, or gentler sharpening. `shadow_*`, `midtone_*`, and `highlight_*` RGB fields allow more selective color shaping. Add important filenames to `required_shots`; loading the project fails if any of those highlights are later removed from the timeline. This keeps must-have moments such as takeoff, wildlife, or a city aerial from being dropped during revisions.

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
  "encoder": "libx264",
  "video_bitrate": "45M",
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

`grade` supports per-shot contrast, brightness, saturation, base RGB balance, separate shadow/midtone/highlight RGB balance, gamma, `gamma_weight` (to favor midtones and shadows while limiting highlight changes), sharpening, and optional contrast-curve presets (`medium_contrast` or `strong_contrast`) so bright landscapes and night footage can be tuned separately. For each finished export, inspect representative frames from every shot, transitions, and the ending at full display size; then play the whole cut and confirm the soundtrack does not end before the picture. The renderer applies a widescreen crop with letterbox bars, a subtle vignette, title/location/credit overlays, audio fades, and H.264/AAC output. The optional `music_title`, `music_creator`, `music_source`, `music_license`, and `music_license_url` fields produce a credits sidecar next to the render. Keep source assets and rendered videos outside the public code repository.

`examples/seattle-road-trip.json` and `examples/seattle-road-trip-indie-rock.json` are complete edit recipes with varied pacing, English location slates, a portrait Rainier insert, a Space Needle flyover at night, and a Bellevue aerial. The indie-rock recipe also demonstrates per-shot corrections for an overbright coast, a shadow-heavy mountain pass, and detailed city footage, plus the required-highlight guard. Both reference footage and music that are intentionally not included; place your own files under the configured media folders or edit the paths before rendering.

## Video editing workflow

Use the [video editing playbook](docs/video-editing-playbook.md) for the complete source-audit, shot-selection, grading, preview, visual-QA, and delivery process. The [Seattle road-trip brief](docs/seattle-road-trip-edit-brief.md) records that project's specific creative requirements. Keep the video and image workflows separate.

## Usage

```sh
tripcut project.json --probe
tripcut project.json --source-audit --sample-interval 2 --jobs 4
tripcut project.json
tripcut project.json --qc
tripcut project.json --preview
```

Use `--probe` to review clip metadata first. Use `--preview` while adjusting the edit: it renders a 720p review copy and uses Apple VideoToolbox H.264 encoding on macOS, keeping the color and framing filters in the same pipeline. Inspect the contact sheet and play the preview; after approval, render the full-resolution manifest. Set `encoder` to `h264_videotoolbox` and `video_bitrate` to a suitable target such as `45M` for a hardware-encoded final on supported Macs. The default `libx264` uses CPU encoding and CRF quality control; VideoToolbox uses bitrate control, so confirm detail and file size on a short preview before choosing it for delivery. Hardware encoding speeds only the encode stage; current FFmpeg color, scaling, overlays, and transitions still run through software filters.

Install `python3 -m pip install '.[video-review]'` to use `--source-audit`. It samples every source video under `media_root` at the requested interval, attempts VideoToolbox decoding on macOS, and creates paged contact sheets with each source filename, source time, and a `USED`/`UNUSED` marker. The CSV records duration, resolution, codec, capture time, and timeline use. Review unused candidates against the timeline before deciding a shot is best; use the sheets to find moments, then inspect promising clips at full motion and resolution.

A normal render writes to a temporary sibling and renames it into place only after FFmpeg succeeds. It then checks output resolution and duration, decodes the complete export, and creates a contact sheet containing a midpoint from every shot, the midpoint of every transition, and the ending. The adjacent `.txt` file maps each panel to its source clip and timeline time. Open the contact sheet and inspect every panel for exposure, subject visibility, focus, crop, and transition artifacts; then play the full export to check motion and music sync. `--qc` repeats those checks for an existing render without rendering again.

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

Photo edits must pass a multi-criteria review together: preserve approved golden highlights while adjusting water color, retain clarity and texture, and check for halos and mask seams. A gain in one region does not justify losing another approved quality. A separate [photo workflow](docs/image-workflow.md) describes the quality gate and current limits.

## Attribution

If your soundtrack requires attribution, include its license and source details in your project and delivered credits sidecar. The example Tahoe soundtrack mentioned in project files is Kevin MacLeod's “Reunited” under CC BY 4.0; this repository does not redistribute that audio.

## License

MIT. FFmpeg and the media you choose remain subject to their own licenses.
