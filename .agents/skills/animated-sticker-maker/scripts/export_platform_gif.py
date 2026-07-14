#!/usr/bin/env python3
"""Export a reviewed sticker package as a constrained GIF and preview PNG."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image


COLOR_CANDIDATES = (255, 224, 192, 160, 128, 96, 64, 48, 32)
MAX_PALETTE_SAMPLES = 500_000
TRANSPARENT_INDEX = 255


def parse_size(value: str) -> tuple[int, int]:
    parts = value.lower().split("x", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("size must look like 400x400")
    try:
        width, height = (int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("size must look like 400x400") from exc
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("size must be positive")
    return width, height


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_reviewed_package(
    package: Path, allow_unreviewed: bool
) -> tuple[list[Image.Image], list[int], dict[str, object], dict[str, str | None]]:
    motion_path = package / "source" / "motion.json"
    report_path = package / "qa" / "report.json"
    frames_dir = package / "source" / "frames"
    if not motion_path.is_file() or not report_path.is_file() or not frames_dir.is_dir():
        raise FileNotFoundError("package must contain source/motion.json, source/frames, and qa/report.json")

    motion = json.loads(motion_path.read_text(encoding="utf-8"))
    entries = motion.get("frames")
    if not isinstance(entries, list) or not entries:
        raise ValueError("source/motion.json must contain a non-empty frames array")
    durations = [entry.get("duration_ms") for entry in entries if isinstance(entry, dict)]
    if len(durations) != len(entries) or not all(isinstance(value, int) and value > 0 for value in durations):
        raise ValueError("every motion frame must have a positive integer duration_ms")

    frame_paths = sorted(frames_dir.glob("*.png"))
    if len(frame_paths) != len(entries):
        raise ValueError(
            f"source frame count {len(frame_paths)} does not match motion frame count {len(entries)}"
        )
    frames = [Image.open(path).convert("RGBA") for path in frame_paths]

    report = json.loads(report_path.read_text(encoding="utf-8"))
    review_status = report.get("status")
    automatic_review = report.get("automatic_review")
    visual_review = report.get("visual_review")
    automatic_status = (
        automatic_review.get("status") if isinstance(automatic_review, dict) else None
    )
    visual_status = visual_review.get("status") if isinstance(visual_review, dict) else None
    review_complete = (
        review_status == "pass"
        and automatic_status == "pass"
        and visual_status == "pass"
    )
    if not review_complete and not allow_unreviewed:
        raise ValueError(
            "package review is incomplete "
            f"(aggregate={review_status!r}, automatic={automatic_status!r}, "
            f"visual={visual_status!r}); pass both reviews first or use "
            "--allow-unreviewed explicitly"
        )
    return frames, durations, motion, {
        "aggregate": review_status if isinstance(review_status, str) else None,
        "automatic": automatic_status if isinstance(automatic_status, str) else None,
        "visual": visual_status if isinstance(visual_status, str) else None,
    }


def fit_frame(frame: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = frame.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def make_global_palette(
    frames: list[Image.Image], colors: int, alpha_threshold: int
) -> Image.Image:
    samples: list[np.ndarray] = []
    for frame in frames:
        rgba = np.asarray(frame)
        visible = rgba[..., :3][rgba[..., 3] >= alpha_threshold]
        if visible.size:
            samples.append(visible)
    if not samples:
        raise ValueError("frames contain no visible pixels at the selected alpha threshold")
    rgb = np.concatenate(samples, axis=0)
    if len(rgb) > MAX_PALETTE_SAMPLES:
        step = max(1, len(rgb) // MAX_PALETTE_SAMPLES)
        rgb = rgb[::step][:MAX_PALETTE_SAMPLES]
    sample_image = Image.fromarray(rgb.reshape(1, len(rgb), 3), mode="RGB")
    palette = sample_image.quantize(
        colors=colors,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    palette_data = palette.getpalette()
    palette_data[TRANSPARENT_INDEX * 3 : TRANSPARENT_INDEX * 3 + 3] = [0, 0, 0]
    palette.putpalette(palette_data)
    return palette


def quantize_frames(
    frames: list[Image.Image], colors: int, alpha_threshold: int
) -> list[Image.Image]:
    palette = make_global_palette(frames, colors, alpha_threshold)
    palette_data = palette.getpalette()
    result: list[Image.Image] = []
    for frame in frames:
        indexed = frame.convert("RGB").quantize(
            palette=palette,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        indices = np.asarray(indexed).copy()
        indices[np.asarray(frame.getchannel("A")) < alpha_threshold] = TRANSPARENT_INDEX
        indexed = Image.fromarray(indices, mode="P")
        indexed.putpalette(palette_data)
        indexed.info["transparency"] = TRANSPARENT_INDEX
        result.append(indexed)
    return result


def write_gif(
    frames: list[Image.Image],
    durations: list[int],
    path: Path,
    colors: int,
    alpha_threshold: int,
    loop: bool,
) -> None:
    indexed = quantize_frames(frames, colors, alpha_threshold)
    indexed[0].save(
        path,
        format="GIF",
        save_all=True,
        append_images=indexed[1:],
        duration=durations,
        loop=0 if loop else 1,
        disposal=2,
        transparency=TRANSPARENT_INDEX,
        optimize=True,
    )


def export_gif(
    frames: list[Image.Image],
    durations: list[int],
    output: Path,
    max_bytes: int | None,
    alpha_threshold: int,
    loop: bool,
) -> tuple[int, int]:
    candidate = output.with_suffix(output.suffix + ".candidate")
    smallest: tuple[int, int] | None = None
    try:
        for colors in COLOR_CANDIDATES:
            write_gif(frames, durations, candidate, colors, alpha_threshold, loop)
            byte_size = candidate.stat().st_size
            if smallest is None or byte_size < smallest[1]:
                smallest = (colors, byte_size)
            if max_bytes is None or byte_size <= max_bytes:
                candidate.replace(output)
                return colors, byte_size
    finally:
        candidate.unlink(missing_ok=True)
    assert smallest is not None
    raise ValueError(
        f"GIF cannot meet {max_bytes} bytes without changing size or frames; "
        f"smallest palette candidate is {smallest[1]} bytes at {smallest[0]} colors"
    )


def write_preview(
    frame: Image.Image, output: Path, max_bytes: int | None
) -> tuple[str, int, int | None]:
    frame.save(output, format="PNG", optimize=True, compress_level=9)
    byte_size = output.stat().st_size
    if max_bytes is None or byte_size <= max_bytes:
        return "rgba", byte_size, None

    smallest: tuple[int, int] | None = None
    candidate = output.with_suffix(output.suffix + ".candidate")
    try:
        for colors in (256, 192, 128, 96, 64, 48, 32, 24, 16):
            indexed = frame.quantize(
                colors=colors,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
            indexed.save(candidate, format="PNG", optimize=True, compress_level=9)
            candidate_size = candidate.stat().st_size
            if smallest is None or candidate_size < smallest[1]:
                smallest = (colors, candidate_size)
            if candidate_size <= max_bytes:
                candidate.replace(output)
                return "indexed", candidate_size, colors
    finally:
        candidate.unlink(missing_ok=True)
    output.unlink(missing_ok=True)
    assert smallest is not None
    raise ValueError(
        f"preview PNG cannot meet {max_bytes} bytes at the requested size; "
        f"smallest candidate is {smallest[1]} bytes at {smallest[0]} colors"
    )


def validate_gif(
    path: Path,
    size: tuple[int, int],
    frame_count: int,
    durations: list[int],
    loop: bool,
) -> dict[str, object]:
    image = Image.open(path)
    expected_loop = 0 if loop else 1
    actual_durations: list[int | None] = []
    transparent_borders: list[bool] = []
    for index in range(getattr(image, "n_frames", 1)):
        image.seek(index)
        actual_durations.append(image.info.get("duration"))
        alpha = np.asarray(image.convert("RGBA").getchannel("A"))
        transparent_borders.append(
            bool(
                np.all(alpha[0] == 0)
                and np.all(alpha[-1] == 0)
                and np.all(alpha[:, 0] == 0)
                and np.all(alpha[:, -1] == 0)
            )
        )
    checks = {
        "size_matches": image.size == size,
        "frame_count_matches": getattr(image, "n_frames", 1) == frame_count,
        "durations_preserved": len(actual_durations) == len(durations)
        and all(
            isinstance(actual, int) and abs(actual - expected) <= 10
            for actual, expected in zip(actual_durations, durations)
        ),
        "loop_matches": image.info.get("loop") == expected_loop,
        "all_borders_transparent": all(transparent_borders),
    }
    if not all(checks.values()):
        raise ValueError(f"exported GIF validation failed: {checks}")
    return {"checks": checks, "durations_ms": actual_durations}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--size", type=parse_size, required=True)
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-output", type=Path)
    parser.add_argument("--preview-max-bytes", type=int)
    parser.add_argument("--preview-frame", default="auto", help="'auto' or a 1-based frame number")
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--alpha-threshold", type=int, default=96, choices=range(1, 255))
    parser.add_argument("--spec-url")
    parser.add_argument("--verified-on", default=date.today().isoformat())
    parser.add_argument("--allow-unreviewed", action="store_true")
    args = parser.parse_args()
    if args.max_bytes is not None and args.max_bytes <= 0:
        parser.error("--max-bytes must be positive")
    if args.preview_max_bytes is not None and args.preview_max_bytes <= 0:
        parser.error("--preview-max-bytes must be positive")

    frames, durations, motion, source_review = load_reviewed_package(
        args.package, args.allow_unreviewed
    )
    resized = [fit_frame(frame, args.size) for frame in frames]
    export_dir = args.package / "exports" / args.platform
    output = args.output or export_dir / "sticker.gif"
    output.parent.mkdir(parents=True, exist_ok=True)
    loop = bool(motion.get("loop", True))
    colors, gif_bytes = export_gif(
        resized,
        durations,
        output,
        args.max_bytes,
        args.alpha_threshold,
        loop,
    )
    validation = validate_gif(output, args.size, len(resized), durations, loop)

    preview_record = None
    if args.preview_output:
        if args.preview_frame == "auto":
            preview_index = max(range(len(durations)), key=durations.__getitem__)
        else:
            try:
                preview_index = int(args.preview_frame) - 1
            except ValueError as exc:
                raise ValueError("--preview-frame must be 'auto' or a 1-based frame number") from exc
            if not 0 <= preview_index < len(resized):
                raise ValueError("--preview-frame is outside the source frame range")
        args.preview_output.parent.mkdir(parents=True, exist_ok=True)
        mode, preview_bytes, preview_colors = write_preview(
            resized[preview_index], args.preview_output, args.preview_max_bytes
        )
        preview_record = {
            "path": str(args.preview_output),
            "frame": preview_index + 1,
            "mode": mode,
            "colors": preview_colors,
            "bytes": preview_bytes,
            "sha256": sha256(args.preview_output),
        }

    report = {
        "status": "pass",
        "platform": args.platform,
        "verified_on": args.verified_on,
        "spec_url": args.spec_url,
        "source_package": str(args.package),
        "source_review_status": source_review["aggregate"],
        "source_review": source_review,
        "canvas": list(args.size),
        "frame_count": len(resized),
        "total_duration_ms": sum(durations),
        "gif": {
            "path": str(output),
            "bytes": gif_bytes,
            "max_bytes": args.max_bytes,
            "colors": colors,
            "alpha_threshold": args.alpha_threshold,
            "sha256": sha256(output),
            "validation": validation,
        },
        "preview": preview_record,
    }
    report_path = args.report_output or output.with_name(f"{output.stem}.export-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output} ({gif_bytes} bytes, {colors} colors)")
    if preview_record:
        print(f"Wrote {args.preview_output} ({preview_record['bytes']} bytes)")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
