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
        # Keep the summer warmth and color while preserving highlight and
        # shadow detail across mixed daylight footage.
        "contrast": 1.18,
        "brightness": 0.012,
        "saturation": 1.22,
        "red": 0.015,
        "green": 0.020,
        "blue": -0.008,
        "shadow_red": 0.002,
        "shadow_green": 0.016,
        "shadow_blue": 0.003,
        "midtone_red": 0.035,
        "midtone_green": 0.028,
        "midtone_blue": -0.028,
        "highlight_red": 0.085,
        "highlight_green": 0.048,
        "highlight_blue": -0.042,
        "gamma": 1.0,
        "sharpness": 0.24,
        "curve": "medium_contrast",
    },
}


def get_look(name: str) -> dict[str, float | str]:
    """Return a copy of a known look's values, rejecting misspelled names."""
    try:
        return dict(LOOK_PRESETS[name])
    except KeyError as exc:
        choices = ", ".join(sorted(LOOK_PRESETS))
        raise ValueError(f"Unknown grade preset {name!r}; choose from: {choices}") from exc
