"""Mask-guided local photo adjustments.

Masks are grayscale images: black protects a pixel, white enables the adjustment.
They can be painted in an editor such as Photoshop, or generated from an optional
ADE20K MaskFormer ONNX model. Adjustments operate on existing pixels only.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

import cv2
import numpy as np
from PIL import Image


REGION_CLASSES = {
    "land": {
        "tree", "grass", "mountain, mount", "plant, flora, plant life",
        "rock, stone", "forest", "palm, palm tree", "trunk, tree trunk, bole",
        "rocky formation",
    },
    "water": {"sea", "water", "lake"},
    "sky": {"sky"},
    "boat": {"boat", "motorboat"},
}
REGION_COLORS = {
    "land": (255, 40, 180),
    "water": (20, 210, 255),
    "sky": (255, 180, 30),
    "boat": (255, 235, 0),
    "detail": (50, 255, 80),
    "highlight": (255, 255, 255),
}


@dataclass(frozen=True)
class ImageAdjustments:
    """Per-region controls. Sharpening is applied only inside supplied masks."""

    land_sharpness: float = 3.8
    water_sharpness: float = 1.8
    detail_radius: float = 2.0
    highlight_lightness: float = 0.0


def _read_mask(path: Path, size: tuple[int, int]) -> np.ndarray:
    """Load a painted grayscale mask and resize it to the source image."""
    with Image.open(path) as im:
        mask = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    width, height = size
    if mask.shape != (height, width):
        mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_LINEAR)
    return np.clip(mask, 0.0, 1.0)


def semantic_masks(
    rgb: np.ndarray,
    model_path: Path,
    labels_path: Path,
) -> dict[str, np.ndarray]:
    """Create soft ADE20K region masks with a MaskFormer ONNX export.

    The ONNX model must expose `class_queries_logits` and
    `masks_queries_logits` outputs and accept normalized `pixel_values`.
    """
    try:
        import onnxruntime as ort
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Automatic masks need the optional semantic dependencies; install "
            "media-toolkit[image,semantic]."
        ) from exc

    labels_raw = json.loads(labels_path.read_text(encoding="utf-8"))
    label_names = {
        int(key): str(value).lower()
        for key, value in labels_raw.get("id2label", labels_raw).items()
    }
    height, width = rgb.shape[:2]
    scale = 1344 / max(height, width)
    resized_width = max(32, round(width * scale))
    resized_height = max(32, round(height * scale))
    resized = Image.fromarray(rgb).resize(
        (resized_width, resized_height), Image.Resampling.BILINEAR
    )
    values = np.asarray(resized, dtype=np.float32) / 255.0
    values = (values - np.array([0.485, 0.456, 0.406], np.float32)) / np.array(
        [0.229, 0.224, 0.225], np.float32
    )
    padded_height = ((resized_height + 31) // 32) * 32
    padded_width = ((resized_width + 31) // 32) * 32
    padded = np.zeros((padded_height, padded_width, 3), np.float32)
    padded[:resized_height, :resized_width] = values

    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    class_logits, mask_logits = session.run(
        None, {"pixel_values": padded.transpose(2, 0, 1)[None]}
    )
    class_logits = class_logits[0]
    mask_logits = mask_logits[0]
    class_logits -= class_logits.max(axis=1, keepdims=True)
    class_probs = np.exp(np.clip(class_logits, -60, 60))
    class_probs /= class_probs.sum(axis=1, keepdims=True)
    mask_probs = 1.0 / (1.0 + np.exp(-np.clip(mask_logits, -30, 30)))
    denominator = mask_probs.sum(axis=0) + 1e-6

    raw: dict[str, np.ndarray] = {}
    for region, names in REGION_CLASSES.items():
        class_ids = [idx for idx, name in label_names.items() if name in names]
        if not class_ids:
            raw[region] = np.zeros((height, width), np.float32)
            continue
        probability = np.einsum(
            "q,qhw->hw",
            class_probs[:, class_ids].sum(axis=1),
            mask_probs,
            optimize=True,
        ) / denominator
        raw[region] = cv2.resize(
            probability, (width, height), interpolation=cv2.INTER_LINEAR
        ).astype(np.float32)

    total = np.maximum(sum(raw.values()), 1e-6)
    return {name: np.clip(mask / total, 0.0, 1.0) for name, mask in raw.items()}


def render_mask_preview(rgb: np.ndarray, masks: Mapping[str, np.ndarray]) -> np.ndarray:
    """Return a translucent, Photoshop-like visualization of the active masks."""
    preview = rgb.astype(np.float32).copy()
    for name, mask in masks.items():
        if name not in REGION_COLORS:
            continue
        amount = np.clip(mask, 0.0, 1.0)[..., None] * 0.45
        color = np.asarray(REGION_COLORS[name], dtype=np.float32)
        preview = preview * (1.0 - amount) + color * amount
    return np.uint8(np.clip(preview + 0.5, 0, 255))


def process_image(
    input_path: Path,
    output_path: Path,
    *,
    mask_paths: Mapping[str, Path] | None = None,
    model_path: Path | None = None,
    labels_path: Path | None = None,
    adjustments: ImageAdjustments = ImageAdjustments(),
    mask_preview_path: Path | None = None,
) -> None:
    """Apply local texture sharpening and optional highlight lift.

    Explicit user masks override matching automatically predicted masks. `detail`
    further restricts sharpening, while `highlight` selects pixels for a local
    lightness lift. No pixels are synthesized or removed.
    """
    if (model_path is None) != (labels_path is None):
        raise ValueError("Pass both --semantic-model and --semantic-labels together")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Choose a separate output path; the source image is kept intact")
    with Image.open(input_path) as source:
        rgb = np.asarray(source.convert("RGB"))
        image_info = dict(source.info)
    height, width = rgb.shape[:2]
    masks = semantic_masks(rgb, model_path, labels_path) if model_path else {}
    for name, path in (mask_paths or {}).items():
        masks[name] = _read_mask(path, (width, height))
    if not any(name in masks for name in ("land", "water", "detail", "highlight")):
        raise ValueError(
            "Provide a land, water, detail, or highlight mask, or enable automatic masks."
        )

    if mask_preview_path:
        mask_preview_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(render_mask_preview(rgb, masks)).save(mask_preview_path)

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    lightness = lab[:, :, 0].astype(np.float32)
    detail = lightness - cv2.GaussianBlur(
        lightness, (0, 0), adjustments.detail_radius
    )
    # Bound the high-pass layer so a rare hard edge cannot create a bright/dark rim.
    detail = np.clip(detail, -8.0, 8.0)
    local_mean = cv2.boxFilter(lightness, cv2.CV_32F, (11, 11))
    local_square = cv2.boxFilter(lightness * lightness, cv2.CV_32F, (11, 11))
    texture = np.sqrt(np.maximum(local_square - local_mean * local_mean, 0.0))
    texture_activity = np.clip((texture - 1.2) / 4.0, 0.0, 1.0)
    detail_signal = np.clip((np.abs(detail) - 0.25) / 0.9, 0.0, 1.0)

    land = masks.get("land", np.zeros((height, width), np.float32))
    water = masks.get("water", np.zeros((height, width), np.float32))
    explicit_detail = masks.get("detail")
    if explicit_detail is not None:
        if "land" in masks or "water" in masks:
            land *= explicit_detail
            water *= explicit_detail
        else:
            land = explicit_detail

    # Fade sharpening inward from mask boundaries to keep shorelines halo-free.
    def interior(mask: np.ndarray) -> np.ndarray:
        binary = (mask > 0.30).astype(np.uint8)
        binary = cv2.morphologyEx(
            binary,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        distance = cv2.distanceTransform(binary, cv2.DIST_L2, 3)
        return mask * np.clip(distance / 8.0, 0.0, 1.0)

    land = interior(land)
    water = interior(water)
    boat = masks.get("boat", np.zeros((height, width), np.float32))
    boat_guard = 1.0 - cv2.GaussianBlur(
        (boat > 0.18).astype(np.float32), (0, 0), 4.0
    )

    strength = (
        adjustments.land_sharpness * land
        + adjustments.water_sharpness * water
    )
    # The eroded semantic masks protect shorelines; only the selected interiors sharpen.
    sharpen_mask = strength * texture_activity * detail_signal * boat_guard
    result_l = np.clip(lightness + detail * sharpen_mask, 0, 255)

    highlight = masks.get("highlight")
    if highlight is not None and adjustments.highlight_lightness:
        highlight_mask = np.clip(highlight, 0.0, 1.0)
        mid_high = np.clip((result_l - 52.0) / 55.0, 0.0, 1.0)
        rolloff = np.clip((242.0 - result_l) / 45.0, 0.0, 1.0)
        lift = adjustments.highlight_lightness * mid_high * rolloff * highlight_mask
        result_l = np.clip(result_l + lift, 0.0, 255.0)

    lab[:, :, 0] = np.uint8(result_l + 0.5)
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_options = {}
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        save_options.update(quality=97, subsampling=0, optimize=True)
    if image_info.get("exif"):
        save_options["exif"] = image_info["exif"]
    if image_info.get("icc_profile"):
        save_options["icc_profile"] = image_info["icc_profile"]
    Image.fromarray(result).save(output_path, **save_options)
