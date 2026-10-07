"""Timeline math, kept independent of FFmpeg command construction."""
from .models import Project


def transition_offsets(project: Project) -> list[float]:
    offsets: list[float] = []
    durations = project.output_durations
    elapsed = durations[0]
    for i in range(1, len(project.shots)):
        elapsed -= project.shots[i].transition_duration
        offsets.append(elapsed)
        elapsed += durations[i]
    return offsets
