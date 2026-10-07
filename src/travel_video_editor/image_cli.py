"""CLI for mask-guided image adjustments."""
from __future__ import annotations

import argparse
from pathlib import Path

from .image_processing import ImageAdjustments, process_image


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply mask-guided local sharpening and highlight adjustments"
    )
    parser.add_argument("input", type=Path, help="Source image")
    parser.add_argument("output", type=Path, help="Output image (source is never changed)")
    parser.add_argument("--land-mask", type=Path, help="Painted grayscale mask for land detail")
    parser.add_argument("--water-mask", type=Path, help="Painted grayscale mask for water texture")
    parser.add_argument("--sky-mask", type=Path, help="Painted grayscale sky mask (preview/protection)")
    parser.add_argument("--boat-mask", type=Path, help="Painted grayscale mask for objects to protect")
    parser.add_argument("--detail-mask", type=Path, help="Additional mask limiting sharpening")
    parser.add_argument("--highlight-mask", type=Path, help="Painted grayscale mask for local highlight lift")
    parser.add_argument("--highlight-lightness", type=float, default=0.0,
                        help="Highlight lift in perceptual lightness units; requires --highlight-mask")
    parser.add_argument("--land-sharpness", type=float, default=3.8,
                        help="Texture sharpening strength inside land mask (default: 3.8)")
    parser.add_argument("--water-sharpness", type=float, default=1.8,
                        help="Gentler texture sharpening strength inside water mask (default: 1.8)")
    parser.add_argument("--detail-radius", type=float, default=2.0,
                        help="Fine-detail scale in pixels (default: 2.0)")
    parser.add_argument("--semantic-model", type=Path,
                        help="Optional MaskFormer ADE20K ONNX model for automatic region masks")
    parser.add_argument("--semantic-labels", type=Path,
                        help="JSON id2label file paired with --semantic-model")
    parser.add_argument("--mask-preview", type=Path,
                        help="Write a translucent color overlay to inspect active masks")
    args = parser.parse_args()

    mask_paths = {
        name: path
        for name, path in {
            "land": args.land_mask,
            "water": args.water_mask,
            "sky": args.sky_mask,
            "boat": args.boat_mask,
            "detail": args.detail_mask,
            "highlight": args.highlight_mask,
        }.items()
        if path is not None
    }
    process_image(
        args.input,
        args.output,
        mask_paths=mask_paths,
        model_path=args.semantic_model,
        labels_path=args.semantic_labels,
        adjustments=ImageAdjustments(
            land_sharpness=args.land_sharpness,
            water_sharpness=args.water_sharpness,
            detail_radius=args.detail_radius,
            highlight_lightness=args.highlight_lightness,
        ),
        mask_preview_path=args.mask_preview,
    )
    print(f"Processed {args.input} -> {args.output}")


if __name__ == "__main__":
    main()
