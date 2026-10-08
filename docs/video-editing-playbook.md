# Video editing playbook

Use this workflow for travel films made with `tripcut`. It captures the practical review lessons from the Pacific Northwest edit and keeps shot selection, image treatment, and delivery checks reproducible. Photo processing has its own workflow in [image-workflow.md](image-workflow.md).

## 1. Inventory before editing

1. Keep camera originals read-only and put the manifest, music, previews, and exports in a separate project folder.
2. Run `tripcut project.json --probe` and note each clip's duration, frame size, frame rate, and capture time.
3. Run `tripcut project.json --source-audit --sample-interval 2 --jobs 4`. Read every contact-sheet page, including unused clips. Use the CSV to filter by capture time, duration, and resolution.
4. Treat the audit as an index, not a substitute for viewing motion. Open promising unused clips and inspect the complete candidate range at normal speed and at full source resolution. For drone clips, check whether the movement really rises, tilts, pans, or simply translates; similar-looking stills can hide very different motion.
5. Keep a short candidate log with source filename, in/out points, story purpose, strengths, and rejection reason. Revisit it when a requested beat is missing.

## 2. Build a story from varied material

- Start with a clear visual hook, then alternate establishing views with closer details, moving shots, wildlife, and human-scale moments. Avoid long runs of interchangeable wide aerials.
- Preserve user-requested highlights in `required_shots`. After every timeline change, check that the required moments remain and that their selected ranges actually show the requested subject.
- Choose in/out points around the useful action, not just the prettiest still. Watch a few seconds before and after the proposed cut.
- Use speed changes to improve rhythm or make a real camera move read more clearly. Check that faster motion still looks intentional and does not make the shot feel like a mistake.
- Prefer a short `fade` for ordinary scene changes. FFmpeg's `dissolve` uses a speckled pixel reveal, which can look like noise when used for a very short transition; reserve it for a deliberate stylized beat. Use `fadeblack` when moving between very different lighting or time-of-day scenes. Review transition midpoints for clutter, ghosted titles, or a subject that briefly disappears.
- Match the edit length and ending to the music. Do not leave picture running after the music has ended; inspect the actual last frames and listen through the fade.

### When the soundtrack comes from a video or screen recording

- Extract the requested audio range into a project-local audio file before rendering. Keep the original recording untouched and keep extracted media out of the public repository. For example: `ffmpeg -i screen-recording.mp4 -map 0:a:0 -vn -t 78 -c:a copy soundtrack.m4a`.
- Check for leading silence and confirm the useful start/end of the track. Set `music_start` to the chosen source offset and make the timeline end at the intended audio endpoint; do not assume the source video's duration is the music duration.
- Calculate runtime from the actual shot durations after speed changes, minus transition overlaps. To extend a cut, first look for useful additional motion in selected clips or strong unused shots. Lengthen only shots whose movement can sustain it; do not freeze frames or slow every shot to fill the track.
- Set the video and audio fades to land together, then play the full preview with sound. Check that the music is not clipped at the start, that its ending feels deliberate, and that the last image does not outlive the requested audio segment.
- Record the source recording, extracted audio range, timeline duration, and soundtrack credit/provenance in the project manifest or delivery notes.

## 3. Grade each shot against its own exposure

- Establish a coherent overall look, then make shot-level corrections. Do not apply one brightness or contrast value blindly across sunny coast, forest shadows, daylight city, and night footage.
- For an artistic but still natural Pacific Northwest look, try the `pnw_artistic` preset: it adds a defined S curve with a gentle black toe and soft highlight shoulder, richer saturation, restrained cyan shadows, and a slight amber bias in highlights. Keep the shadow/highlight split subtle; preserve each scene's real white balance and tune exposure shot by shot.
- For a soft-neutral, colorful travel-film look, use a restrained shared saturation/contrast base, then judge white balance by scene: keep sunset highlights warm, forest greens natural, blue-hour ocean cool, and daylight city scenes close to neutral. Remove unwanted cyan/blue casts without turning sky or water brown; never force every shot to the same warmth.
- When the user asks for a visible adjustment, compare before/after frames at the same size and display conditions. The requested change should be plainly visible while important highlight and shadow detail remains.
- If a shot still looks veiled after exposure and contrast are balanced, treat haze as a separate, shot-level problem. Try `tripdehaze` on only the selected source range; inspect the sky, warm highlights, distant ridges, and forest shadows for clipped whites, color shifts, halos, or flicker before keeping it.
- Recheck haze across the whole cut, including distant ridgelines, coastal headlands, and city skylines. Apply dehaze only where the source has a real atmospheric veil; a naturally cool blue-hour coast or clear blue sky should not be “corrected” into a warm look. If dehaze darkens the land, use a small local midtone lift after it and recheck highlights.
- Check skies and clouds for clipping, forests for crushed shadows, coast foam for lost texture, water for unnatural cyan/blue shifts, and night scenes for noise and brittle sharpening.
- Use moderate, source-aware sharpening. A small wildlife subject may benefit from a modest push-in, but sharpening cannot restore detail that the source never captured. Do not enlarge a distant subject until it looks soft or pixelated.
- Tune nearby shots as a sequence. Check exposure, white balance, saturation, and contrast across the cut so the grade feels consistent without flattening different lighting conditions.
- Make a representative contact sheet after grading. Inspect high-resolution crops of small subjects, fine foliage, city edges, and bright water before delivery.

## 4. Titles and location slates

- Use a small type system: an expressive display face for the main location, a legible sans serif for supporting text, and consistent margins and divider rules.
- Confirm the exact font is installed and available to FFmpeg before rendering. Check glyph coverage, kerning, stroke weight, and readability over both bright and dark footage.
- Design titles at the delivery aspect ratio and resolution. Preview scaling must preserve relative size, placement, and stroke sharpness; inspect the 720p preview and final 4K frames.
- Review the opening title, every location slate, and credits over moving footage. Keep labels clear of the subject and away from crop-safe edges.

## 5. Preview, inspect, revise, deliver

1. Render a 720p preview with `tripcut project.json --preview`. On supported Macs, use `h264_videotoolbox` for faster hardware encoding. This accelerates encoding; FFmpeg's color, scale, title, and transition filters may still run on the CPU.
   - On macOS, check `ffmpeg -filters` for `coreimage` before planning GPU color work. Core Image can provide Apple-native color operations, but its presence alone does not prove a given filter runs on the GPU or that the full graph gets faster. Benchmark the same representative 4K shot with matched CPU and Core Image grades, compare the frames for color/tonal differences, and measure the complete pipeline. CPU-only steps and transfers between system and GPU memory can erase the gain. Keep VideoToolbox encoding and GPU filtering documented as separate acceleration stages.
   - A short 4K Olympic Peninsula check on this Mac found the CPU `eq` path at about 2.9× realtime and the Core Image `CIColorControls` path at about 1.5× for the same 2.5-second range. This is a local result, not a universal ranking; retain VideoToolbox encoding, and use CPU grading for this workflow until a better GPU-resident graph demonstrates an end-to-end win.
2. Open the generated contact sheet and map. Check every shot midpoint, transition midpoint, title, wildlife/highlight moment, and final frame for exposure, focus, crop, subject visibility, title quality, and artifacts.
3. Play the complete preview with sound. Check real motion, pacing, speed changes, transition feel, and that the music fade lands with the picture. A contact sheet alone cannot establish motion quality.
4. If a requested change is hard to see, or any shot looks wrong, revise the manifest and render another preview. Do not describe an unverified change as complete.
5. Only after the preview passes, render 3840×2160 at 30 fps with a high hardware-encoder bitrate appropriate to the source. Keep the manifest next to the project deliverables.
6. Verify the finished file with `ffprobe`, decode the whole file, inspect the final contact sheet and full-resolution detail frames, and play the beginning, transitions, key subjects, and ending. Confirm codec, dimensions, frame rate, runtime, audio presence, and a clean audio fade.
7. Keep one clearly named approved final and any explicitly useful preview. Preserve camera originals; keep large media and licensed music out of the public code repository.

## 6. Reporting accurately

- Say how footage was reviewed (for example, two-second source samples plus full-motion checks of finalists); do not imply every frame of every source was watched if it was not.
- Distinguish a true camera tilt from a rising/forward reveal, a pan, or a static aerial. Describe the motion the source actually contains.
- Report the actual output resolution and encoder used. Hardware acceleration does not mean every filter ran on the GPU.
- Link the selected final by full path and identify it as the final version. Summarize major choices and mention any visible limitation, such as distant wildlife detail.
