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

1. Render a 720p preview first using Apple VideoToolbox H.264 encoding on supported Macs. The FFmpeg color, crop, text, and transition filters still run on CPU.
2. Inspect every shot midpoint, every transition, opening titles, wildlife, highlights/shadows, and the ending. Play the preview for real motion, framing, and music sync.
3. Make another preview if any requested visual change is not clearly visible or a shot still feels wrong.
4. Only after the visual review passes, render the delivery at 3840x2160. Use hardware H.264 encoding at a high bitrate where available, verify the resulting codec/resolution/duration, decode the whole file, and inspect the final review sheet and full-resolution detail frames.
5. Keep source footage untouched, preserve each revision under a descriptive name, and retain the project manifest alongside the reproducible toolkit workflow.
