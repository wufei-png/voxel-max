#!/usr/bin/env python3
"""Validate RGBA frames and build the default animated-sticker package."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


DEFAULT_SIZE = (1024, 1024)
DEFAULT_FRAME_RANGE = (4, 8)
DEFAULT_DURATION_RANGE_MS = (1200, 2000)


def is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def parse_size(value: str) -> tuple[int, int]:
    parts = value.lower().split("x", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("expected size must look like 1024x1024")
    try:
        width, height = (int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected size must look like 1024x1024") from exc
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("expected size must be positive")
    return width, height


def load_motion(path: Path) -> dict[str, object]:
    motion = json.loads(path.read_text(encoding="utf-8"))
    frames = motion.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("motion.json must contain a non-empty frames array")
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError(f"frames[{index}] must be an object")
        if not isinstance(frame.get("file"), str) or not frame["file"]:
            raise ValueError(f"frames[{index}].file must be a path string")
        duration = frame.get("duration_ms")
        if not is_positive_int(duration):
            raise ValueError(f"frames[{index}].duration_ms must be a positive integer")
    return motion


def resolve_frame(frames_dir: Path, file_value: str) -> Path:
    relative = Path(file_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("motion frame paths must stay beneath the frames directory")
    candidates = [frames_dir / relative, frames_dir / relative.name]
    for candidate in candidates:
        if (
            candidate.is_file()
            and candidate.resolve().is_relative_to(frames_dir.resolve())
        ):
            return candidate
    raise FileNotFoundError(f"frame not found for {file_value!r} in {frames_dir}")


def alpha_metrics(image: Image.Image) -> dict[str, object]:
    alpha = np.asarray(image.getchannel("A"))
    visible = np.where(alpha > 16)
    bbox = None
    if visible[0].size:
        bbox = [
            int(visible[1].min()),
            int(visible[0].min()),
            int(visible[1].max() + 1),
            int(visible[0].max() + 1),
        ]
    border_is_transparent = bool(
        np.all(alpha[0] == 0)
        and np.all(alpha[-1] == 0)
        and np.all(alpha[:, 0] == 0)
        and np.all(alpha[:, -1] == 0)
    )
    return {
        "size": list(image.size),
        "mode": image.mode,
        "alpha_bbox": bbox,
        "transparent_pixels": int(np.count_nonzero(alpha == 0)),
        "partial_alpha_pixels": int(np.count_nonzero((alpha > 0) & (alpha < 255))),
        "border_is_transparent": border_is_transparent,
        "pixel_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
    }


def checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, (238, 242, 242))
    draw = ImageDraw.Draw(image)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(211, 220, 220))
    return image


def label_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def make_contact_sheet(
    frames: list[Image.Image], durations: list[int], path: Path
) -> None:
    columns = min(4, math.ceil(math.sqrt(len(frames))))
    rows = math.ceil(len(frames) / columns)
    tile = 320
    label_height = 38
    sheet = Image.new("RGB", (columns * tile, rows * (tile + label_height)), "white")
    font = label_font(18)
    for index, frame in enumerate(frames):
        x = (index % columns) * tile
        y = (index // columns) * (tile + label_height)
        background = checkerboard((tile, tile))
        preview = frame.copy()
        preview.thumbnail((tile, tile), Image.Resampling.LANCZOS)
        px = (tile - preview.width) // 2
        py = (tile - preview.height) // 2
        background.paste(preview, (px, py), preview.getchannel("A"))
        sheet.paste(background, (x, y))
        ImageDraw.Draw(sheet).text(
            (x + 10, y + tile + 8),
            f"F{index + 1}  {durations[index]} ms",
            font=font,
            fill=(20, 55, 53),
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def clean_output(output: Path) -> tuple[Path, Path]:
    source = output / "source"
    qa = output / "qa"
    frame_output = source / "frames"
    if frame_output.exists():
        shutil.rmtree(frame_output)
    stale_sticker = output / "sticker.webp"
    if stale_sticker.exists():
        stale_sticker.unlink()
    frame_output.mkdir(parents=True, exist_ok=True)
    qa.mkdir(parents=True, exist_ok=True)
    return frame_output, qa


def package(args: argparse.Namespace) -> int:
    motion = load_motion(args.motion)
    frame_entries = motion["frames"]
    frame_paths = [resolve_frame(args.frames_dir, entry["file"]) for entry in frame_entries]
    frames: list[Image.Image] = []
    source_modes: list[str] = []
    for path in frame_paths:
        with Image.open(path) as source:
            source_modes.append(source.mode)
            frames.append(source.convert("RGBA"))
    durations = [entry["duration_ms"] for entry in frame_entries]
    total_duration = sum(durations)
    metrics = [alpha_metrics(frame) for frame in frames]

    checks = {
        "frame_count_in_default_range": args.allow_nonstandard_frame_count
        or DEFAULT_FRAME_RANGE[0] <= len(frames) <= DEFAULT_FRAME_RANGE[1],
        "source_frames_are_rgba": all(mode == "RGBA" for mode in source_modes),
        "all_frames_match_expected_size": all(frame.size == args.expected_size for frame in frames),
        "all_borders_transparent": all(metric["border_is_transparent"] for metric in metrics),
        "all_frames_have_visible_pixels": all(metric["alpha_bbox"] is not None for metric in metrics),
        "all_frames_are_unique": len({metric["pixel_sha256"] for metric in metrics}) == len(frames),
        "duration_in_default_range": args.allow_nonstandard_timing
        or DEFAULT_DURATION_RANGE_MS[0] <= total_duration <= DEFAULT_DURATION_RANGE_MS[1],
    }
    automatic_pass = all(checks.values())

    frame_output, qa = clean_output(args.output)
    packaged_motion = copy.deepcopy(motion)
    frame_name_map: dict[str, str] = {}
    for index, (path, entry) in enumerate(zip(frame_paths, packaged_motion["frames"])):
        normalized_name = f"{index:03d}.png"
        original_name = entry["file"]
        shutil.copy2(path, frame_output / normalized_name)
        canonical_name = f"frames/{normalized_name}"
        entry["file"] = canonical_name
        frame_name_map[original_name] = canonical_name
    semantic_hold = packaged_motion.get("semantic_hold_frame")
    if isinstance(semantic_hold, str) and semantic_hold in frame_name_map:
        packaged_motion["semantic_hold_frame"] = frame_name_map[semantic_hold]
    (args.output / "source" / "motion.json").write_text(
        json.dumps(packaged_motion, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    make_contact_sheet(frames, durations, qa / "contact-sheet.png")

    report = {
        "status": "pending_visual_review" if automatic_pass else "automatic_fail",
        "automatic_review": {"status": "pass" if automatic_pass else "fail", "checks": checks},
        "visual_review": {
            "status": "pending",
            "required": ["identity", "meaning", "loop", "alpha", "small_size"],
            "notes": {},
        },
        "canvas": list(args.expected_size),
        "frame_count": len(frames),
        "total_duration_ms": total_duration,
        "frames": metrics,
    }
    (qa / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if not automatic_pass:
        print(f"Automatic QA failed; inspect {qa / 'report.json'}")
        return 2

    loop_count = 0 if bool(motion.get("loop", True)) else 1
    frames[0].save(
        args.output / "sticker.webp",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop_count,
        lossless=False,
        quality=args.quality,
        method=6,
        minimize_size=True,
        allow_mixed=True,
    )
    print(f"Wrote {args.output / 'sticker.webp'}")
    print(f"Automatic QA passed; visual review remains: {qa / 'report.json'}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-dir", type=Path, required=True)
    parser.add_argument("--motion", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-size", type=parse_size, default=DEFAULT_SIZE)
    parser.add_argument("--quality", type=int, default=92, choices=range(1, 101))
    parser.add_argument("--allow-nonstandard-frame-count", action="store_true")
    parser.add_argument("--allow-nonstandard-timing", action="store_true")
    args = parser.parse_args()
    raise SystemExit(package(args))


if __name__ == "__main__":
    main()
