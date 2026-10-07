# Project instructions

## Keep photo and video workflows separate

- Treat still-photo editing and video editing as separate workflows, interfaces, manifests, and outputs. Do not send stills through the video grade pipeline or describe `tripimage` as a complete photo editor.
- Read `docs/image-workflow.md` before changing photo processing or producing edited photo deliverables. Keep it current when user steering changes the workflow.
- Preserve the source image as the authority. Use pixel-based processing; never use generative image editing unless the user explicitly asks for it. Do not add, remove, or invent scene content.
- Never overwrite originals. Distinguish camera originals, approved references, and prior exports before processing. Preserve image dimensions and orientation; carry metadata and color profiles when feasible.

## Non-negotiable visual acceptance: do not optimize one thing by sacrificing another

For every image and every iteration, check the complete set of user goals together. An improvement to one criterion does not count if another regresses. In particular, deepening or shifting the lake toward blue/teal must not remove the small island's warm, golden sunlit foliage and rocks. Keep both qualities in the same finished frame.

Before calling a batch finished, review each frame at fit-to-screen and inspect high-resolution crops. The following must all pass at once:

1. User-approved warm/golden light remains visible on the island's sun-facing trees and rock; shadows keep detail.
2. Deep water stays rich blue/teal and shallow shoreline water stays clear turquoise, without turning red or muddy.
3. The image reads clean, crisp, and dimensional, without haze, glow, or a washed-out veil.
4. Local sharpening is visible where requested and texture-aware; it does not make noise, water, or foliage brittle.
5. No bright/dark halos, mask seams, color fringes, or abrupt transitions appear along ridges, trees, or shorelines.
6. Highlights retain texture and tonal separation; increased light does not flatten the island or clip important detail.

If any criterion fails, revise and inspect again. Do not trade away an approved quality to improve another. Check an overall contact sheet and 100% crops of the important regions (island/gold, water/reflection, shore/ridge edges, and fine detail). Inspect mask overlays before export; automatic segmentation is a starting point, not proof that a mask is correct. Keep a small number of clearly named deliverables, not a sprawl of near-duplicate versions.

## Photo look and implementation

- Treat Apple-style and Fuji-style edits as separate looks. Follow the chosen reference rather than applying one global recipe to every scene. Adapt masks and strengths per photo.
- For the Apple reference used in this project, aim for clean, clear, detailed contrast; controlled vivid blue/teal water; readable natural shadows; and warm highlights on sunlit land. Keep warmth pleasant and saturation controlled.
- For Fuji-inspired work, keep the requested warm color response and pronounced but natural detail without introducing haze or halos.
- Use explicit local masks for distinct regions (sky/clouds, deep water, shallow water, land/foliage, existing highlights, and protected subjects). Do not paint synthetic light or add a radial glow. Brighten only light/reflections already present in the capture.
- Sharpen as a deliberate final detail step at delivery resolution. Separate land from water, protect smooth areas and subjects, and inspect the result at 100% for edge ringing.
- Use reproducible code/configuration for repeatable processing. Record source files, look/reference, output paths, dimensions, and applied operations. Be clear when an image was created by a one-off script versus the repository's `tripimage` command.
