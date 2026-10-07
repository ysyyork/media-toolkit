"""Named, reusable color looks for travel-video projects."""
from __future__ import annotations


LOOK_PRESETS: dict[str, dict[str, float | str]] = {
    "neutral": {
        "contrast": 1.10,
        "brightness": 0.0,
        "saturation": 1.06,
        "red": 0.012,
        "green": 0.008,
        "blue": -0.018,
        "gamma": 1.0,
        "sharpness": 0.24,
        "curve": "none",
    },
    "summer_film_pop": {
        "contrast": 1.28,
        "brightness": 0.045,
        "saturation": 1.24,
        "red": 0.018,
        "green": 0.026,
        "blue": -0.012,
        "gamma": 0.90,
        "sharpness": 0.52,
        "curve": "strong_contrast",
    },
}


def get_look(name: str) -> dict[str, float | str]:
    """Return a copy of a known look's values, rejecting misspelled names."""
    try:
        return dict(LOOK_PRESETS[name])
    except KeyError as exc:
        choices = ", ".join(sorted(LOOK_PRESETS))
        raise ValueError(f"Unknown grade preset {name!r}; choose from: {choices}") from exc
