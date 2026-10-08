# Seattle and Pacific Northwest edit brief

Carry this brief into every revision of the Seattle / Olympic / North Cascades travel film.

## Story and pacing

- Make this feel like a summer road-trip documentary with its own identity, not a copy of the Lake Tahoe edit.
- Keep the rhythm lively and varied: aerial reveals, moving road and city shots, close details, wildlife, and scenic holds. Avoid both sluggish runs of wide shots and a frantic montage.
- Keep the real takeoff moment, Space Needle night flyover, Bellevue aerial, Olympic Coast sea otters, Lake Crescent, a horizontal bay pan with the sea stack, and Mount Rainier / Seattle-area views when the source footage supports them.
- Match picture length to the selected upbeat indie-rock track. Avoid a silent tail or credits after the music ends. Final duration is editorially flexible.
- Sea-only texture shots should lead into a tilt-up / reveal when the source contains one. Prefer the footage's real camera move; do not fake a large pan or tilt by cropping.

## Picture and grade

- Aim for warm, vivid, artistic summer color with a restrained cinematic finish. Avoid the cold-blue cast and the flat, grey look.
- Grade each shot for its actual exposure. Keep highlights textured, open shadows enough to read, and retain contrast without crushing forests or clipping sunlit ground, clouds, or surf.
- Make visible, reviewable changes when asked to lift brightness, contrast, saturation, or detail. Compare before/after frames at the same output size; do not claim a change that is imperceptible.
- Keep water naturally blue/teal, forests green, and sunlit land warm. Use moderate sharpening, especially on night footage, water, foliage, and wildlife; sharpening must not create brittle texture or halos.
- For wildlife, start with a readable wider composition, then make a smooth, modest push-in if the source detail supports it. Do not imply sharpening can restore detail absent from the source.
- Prefer native widescreen shots for the ending when available. Avoid an awkward portrait strip with heavily blurred side panels as the hero ending.

## Type and titles

- Use the restrained editorial serif title style with clean sans-serif supporting text. Keep location labels elegant, readable, and clear of the subject.
- Scale font sizes, margins, dividers, and portrait layouts proportionally with render resolution. A 720p preview must preserve the same composition and relative typography as the 4K delivery.
- Check the opening title and location slate together, all location labels, and end credits for overlap, clipping, or overly large text.

## Review and delivery workflow

1. Inventory every source clip and create a source-audit contact sheet at two-second intervals. Review every page, including clips not yet used, and mark the strongest alternatives for each story beat.
2. Inspect promising unused candidates at full motion and resolution; use source-audit contact sheets as an index, not as a substitute for watching a clip.
3. Render a 720p preview first using Apple VideoToolbox H.264 encoding on supported Macs. The FFmpeg color, crop, text, and transition filters still run on CPU.
4. Inspect every shot midpoint, every transition, opening titles, wildlife, highlights/shadows, and the ending. Play the preview for real motion, framing, and music sync.
5. Make another preview if any requested visual change is not clearly visible or a shot still feels wrong.
6. Only after the visual review passes, render the delivery at 3840x2160. Use hardware H.264 encoding at a high bitrate where available, verify the resulting codec/resolution/duration, decode the whole file, and inspect the final review sheet and full-resolution detail frames.
7. Keep source footage untouched, preserve each revision under a descriptive name, and retain the project manifest alongside the reproducible toolkit workflow.

## Review findings and later corrections

- The source review covered 102 MP4s with a two-second sampling interval (2,455 sampled frames across 44 contact sheets); finalists were checked at full motion before their ranges were selected.
- The v11 cut keeps the road-level takeoff from `DJI_20260619185954_0035_D.MP4`, the Space Needle night flyover, Bellevue, Olympic Coast otters and sea stacks, the horizontal bay movement, and the Mount Rainier view.
- The otter source is distant and has limited fine detail. Review adjacent clips before choosing it; in this edit, clip 0189 is the only nearby clip with visible otters (0188 is mostly open water and 0190 is surf/rocks). Use the interaction range around 12.8s, a modest 1.24× push-in, and a brighter local grade. Preserve the source texture; sharpening cannot restore detail the camera did not capture.
- The golden-hour North Cascades valley needed a clearly visible lift in brightness and contrast. Its indie-rock example now includes a local grade (contrast 1.22, brightness 0.045) while preserving the sunset highlights and forest texture; compare the same frame before and after rather than assuming a numeric adjustment will be visible on every display.
- That lift alone did not remove the capture's atmospheric veil. The current revision runs `tripdehaze` on only the 3.5-second source range, protects sky/highlights, and adds a local gamma lift afterward so the forest does not become too dark. Review the whole range for temporal consistency and check the same frame before/after; reduce dehaze strength if the ridge or foliage develops halos.
- Avoid FFmpeg's very short `dissolve` transitions: its pixel-speckled reveal can look like a brief glitch. Use a smooth `fade` for normal cuts and `fadeblack` between the golden-hour valley and Seattle night skyline.
- The earlier v17 render was checked at 3840×2160, 30 fps, 62.1 seconds, H.264/AAC via VideoToolbox. The later artistic-neutral grade uses per-scene temperature decisions: sunset warmth stays in highlights, forest greens remain natural, the blue-hour coast remains cool, and daylight Seattle/Bellevue are kept closer to neutral.
- The earlier v21 reviewed render was `Seattle_Summer_Road_Trip_Artistic_Neutral_v21.mp4` (3840×2160, 30 fps, 62.1 seconds, H.264/AAC via VideoToolbox, about 41 Mb/s). Haze reduction is limited to the veiled Olympic Peninsula and golden-hour valley; the coast uses milder treatment to preserve marine atmosphere. Full-resolution key frames and the full-file decode were checked before delivery.
- The earlier sequence held the Mount Rainier view, then used the opening five seconds of `DJI_20260621144304_0247_D.MP4` at 1.75× for a quicker Lake Washington aerial reveal. This is a rising/forward reveal, not a strong gimbal tilt-up; the cut description should remain accurate.
- The original v11 render was 3840×2160, 30 fps H.264/AAC, about 64 seconds, encoded with Apple VideoToolbox. The current preview uses the same composition and grade at 720p for review.

## Motion and regional color revision (v28)

- North Cascades daylight should have a perceptible yellow-green summer warmth. Keep snow neutral and grade Seattle night and Olympic coast independently.
- Keep both the closer Olympic snowy peaks (0137) and wider summit panorama (0142).
- Inspect every selected range with at least one second of source handles; dense half-second sheets locate candidate boundaries, followed by preview playback. Use `tripcut project.json --motion-review --jobs 3`.
- Preserve actual action: Space Needle flyover should pass the tower, otter interaction should finish its dive, and sunset tilt should get a scenic hold after the peaks emerge. The sunset source range now extends from 16–19.5s to 16–21.5s.
- Avoid the early fast yaw in 0247; use a later stable lake view. Shift 0214 past the initial cropped tower roof. Keep the real takeoff and complete Lake Crescent tilt.
- Fund important motion by trimming scenic holds, while matching the user-provided audio to approximately 78 seconds. Reduce the otter push-in to 1.24x to preserve source detail.

## Dynamic selection revision (v29)

- Subsequent subtitle preference: omit calendar dates and years from on-screen text. Keep place names and useful descriptions; the summer theme can remain. This applies to opening text as well as location slates.
- Subsequent motion preference: stabilize only shots with actual jitter, with matched playback review. Keep intentional pans and rotations. Reject takeoff stabilization when foreground parallax worsens the result; apply bounded translation only to the Space Needle flyover and Seattle city close view.
- Subsequent wildlife preference: use the sea-otter source's actual approach from 2.4–17.4 seconds over six output seconds, keep its dive, and remove the added digital zoom. Do not claim sharpening can restore missing source detail.

- A shot can satisfy subject coverage and still fail pacing. The nearly fixed 0142 panorama was rejected after preview feedback; speed alone cannot create a camera move in a stationary source. Preserve wide Olympic summit coverage using 0137 source 132–141s at 1.5x, a real horizontal sweep into the snowy chain, alongside the closer peaks.
- Recompare all four nighttime originals: 0080, 0081, 0083, and 0087. 0081 is a short, blurred turn; 0087 has a broad skyline similar to 0080; 0083 offers a distinct rotating street-grid-to-oblique-city reveal. Use 0083 source 26–40s over 6.5 output seconds before the complete Space Needle pass over six seconds.
- The user subsequently allowed a longer edit: use the full 85.2-second recording for an approximately 84.2-second film. Maintain the extended sunset, regional warmth, takeoff, coast, wildlife, Bellevue, and the other accepted decisions. Fund new night coverage from scenic holds, not unfinished actions.
