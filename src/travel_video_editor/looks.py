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
    "artistic_neutral": {
        # A soft, neutral base with visible color. Set each scene's white
        # balance separately so sunset, forest, coast, and city keep their
        # natural character without a global warm or cool cast.
        "contrast": 1.12,
        "brightness": 0.010,
        "saturation": 1.18,
        "red": 0.0,
        "green": 0.0,
        "blue": 0.0,
        "gamma": 1.03,
        "gamma_weight": 0.90,
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
    "pnw_artistic": {
        # A neutral Pacific Northwest print look: richer color, defined lower
        # mids, a gentle toe, and a soft highlight shoulder. Scene overrides
        # should still protect blue hour, sunset, and night exposure.
        "contrast": 1.17,
        "brightness": 0.006,
        "saturation": 1.21,
        "red": 0.0,
        "green": 0.0,
        "blue": 0.0,
        "shadow_red": -0.002,
        "shadow_green": 0.002,
        "shadow_blue": 0.004,
        "highlight_red": 0.008,
        "highlight_green": 0.003,
        "highlight_blue": -0.005,
        "gamma": 1.0,
        "gamma_weight": 0.9,
        "sharpness": 0.25,
        "curve": "soft_film",
    },
}


def get_look(name: str) -> dict[str, float | str]:
    """Return a copy of a known look's values, rejecting misspelled names."""
    try:
        return dict(LOOK_PRESETS[name])
    except KeyError as exc:
        choices = ", ".join(sorted(LOOK_PRESETS))
        raise ValueError(f"Unknown grade preset {name!r}; choose from: {choices}") from exc
