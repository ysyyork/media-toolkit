# Architecture

The edit manifest is the source of truth. Parsing and validation convert it into immutable `Project`, `Shot`, and `Grade` values. The timeline module calculates playback durations and overlap offsets without depending on FFmpeg. The filter-graph builder turns the project into filter syntax, while `FFmpegRenderer` handles input validation, command assembly, process execution, and atomic delivery. `probe` provides a read-only adapter for FFprobe; `credits` writes the soundtrack attribution alongside the render.

This keeps editing decisions (clip in-points, speed, grade, transitions) separate from rendering mechanics. A future NLE or alternate encoder can consume the same project data without changing the project format. FFmpeg calls use argument arrays rather than a shell command string, and rendered files are promoted into place only after a successful encode.
