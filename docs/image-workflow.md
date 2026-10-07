# Photo workflow

This is a still-photo workflow. It is intentionally separate from the video workflow in `tripcut`; photo edits should not be routed through video manifests or FFmpeg shot grades.

## Current capability and limits

`tripimage` currently provides mask-guided local sharpening and optional masked lightness lift. It is useful for selective detail work, but it is **not** a complete Lightroom/Photoshop-style workflow: it has no Apple/Fuji look profiles, full color-grading pipeline, dehaze control, interactive mask painting, batch sidecar format, or contact-sheet reviewer. The recent Apple-reference Tahoe exports were made with a one-off OpenCV/Pillow script, not by `tripimage`. Do not imply otherwise.

Install the photo extras with `python3 -m pip install '.[image]'`. For the optional ADE20K MaskFormer ONNX masks, install `python3 -m pip install '.[image,semantic]'`. Painted grayscale masks remain the preferred way to get precise local selections:

```sh
tripimage source.jpg output.jpg \
  --land-mask masks/land.png \
  --water-mask masks/water.png \
  --boat-mask masks/boat.png \
  --highlight-mask masks/reflection.png \
  --highlight-lightness 40 \
  --land-sharpness 3.8 \
  --water-sharpness 1.8 \
  --mask-preview preview-masks.jpg
```

White selects; black protects; gray blends. Inspect `--mask-preview` before relying on a selection. A `sky` mask currently appears in the preview/protection workflow but does not apply a sky adjustment. The CLI is single-image and detail-focused.

## Repeatable end-to-end editing workflow

1. **Inventory and protect sources.** List camera originals, RAW files, approved reference edits, and previous exports separately. Never overwrite originals. Prefer RAW only when available and appropriate; do not mistake an earlier JPEG edit for the source.
2. **Choose the look and reference.** State whether this set is Apple-style or Fuji-inspired and identify the exact approved reference. Record the traits the user liked. For this Tahoe Apple look, the approved combination is clear detail, deep blue/teal water, turquoise shallows, and visible golden light on sun-facing island vegetation and rocks.
3. **Make a baseline and define regions.** Inspect the unedited image at fit and at 100%. Plan separate masks for sky/cloud, deep water, shallow water, land/foliage, existing bright reflections, and subjects to protect. Automatic masks can propose regions, but inspect their overlays and repair them before use.
4. **Grade globally with restraint.** Set white balance, tonal curve, contrast, and overall saturation first. Keep shadow detail and highlight texture. Avoid a global cast that turns water red, foliage fluorescent, or the whole frame hazy.
5. **Tune local color and light.** Shape deep water and shallow turquoise independently from land. Keep approved golden highlights on the island while changing lake color. Lift only real captured highlights/reflections; never synthesize a sun, flare, or glow. Feather masks inward from boundaries and inspect shorelines for color spill.
6. **Add local clarity and sharpening.** Work at final output dimensions. Apply distinct, texture-aware sharpening to land and water, protect smooth regions and important subjects, and avoid broad edge suppression that makes sharpening invisible. Review ridge, island, and shoreline edges for halos.
7. **Run the no-tradeoff review before export.** Compare original, approved reference, and candidate side by side. Inspect a full-frame contact sheet plus 100% crops of golden island highlights, water/reflections, shoreline/ridge edges, and fine texture. Verify *all* required qualities in the same image: gold remains, water remains blue/teal, shallows remain clear, detail is crisp, lighting has depth, highlights retain texture, and there is no haze or halo. If one improved while another regressed, the image is not done.
8. **Export and account for it.** Save one clear final set in one predictable folder. Preserve pixel dimensions and orientation; retain EXIF/ICC metadata when possible. Reopen exported files and check them again, since JPEG encoding and color management can change appearance. Keep one current contact sheet and, if needed, one detail sheet; remove stale previews from the handoff folder.
9. **Report what actually ran.** Identify the exact source, final path, dimensions, whether the change used pixel processing or generation, which tool/script ran, and what was reviewed. State known limitations rather than claiming quality checks the current tool cannot perform.

## Required quality gate: no single-axis optimization

An image does not pass because the water is bluer, the island is warmer, or the sharpening is stronger in isolation. It passes only when those user-approved qualities coexist and the image remains clear and natural. In particular, never let a water-grade update erase the island's approved golden highlights. Never let halo suppression flatten the light or make the detail disappear. After every material edit, repeat the whole-image and crop review across the entire batch.

## Video workflow remains separate

Use `tripcut` and the project JSON for footage: inspect sources with `tripcut project.json --probe`, review timing and grades, render with `tripcut project.json`, then check the render and its credits sidecar. Use `tripimage` only for still-photo detail operations its CLI actually supports. Photo style grading should use its own future photo-specific module, per-image adjustment sidecar/profile, local masks, and preview/export path rather than expanding the video manifest to contain photo controls.
