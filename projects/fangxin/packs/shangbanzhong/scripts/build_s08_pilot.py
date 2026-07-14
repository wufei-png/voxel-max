#!/usr/bin/env python3
"""Build the S08 bug-squash pilot from approved transparent anchors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


CANVAS = 1024
FRAME_DURATIONS_MS = [160, 180, 120, 560, 220, 180]
FRAME_DESCRIPTIONS = [
    "主体保持警觉，头顶没有 Bug。",
    "带两只发光眼的 Bug 从上方进入。",
    "Bug 接触头顶，主体尚未发生最大形变。",
    "Bug 猛然下压，主体变宽变扁并停留。",
    "Bug 微微抬起，主体仍保持最大受压形态。",
    "Bug 向上离开，主体弹回初始比例并衔接首帧。",
]


def normalize(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize(
        (CANVAS, CANVAS), Image.Resampling.LANCZOS
    )


def alpha_crop(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("Anchor image has no visible pixels")
    return image.crop(bbox)


def place_subject(
    anchor: Image.Image,
    scale: float,
    baseline: int = 970,
    center_x: int = CANVAS // 2,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    subject = alpha_crop(anchor)
    size = (
        max(1, round(subject.width * scale)),
        max(1, round(subject.height * scale)),
    )
    subject = subject.resize(size, Image.Resampling.LANCZOS)
    x = round(center_x - subject.width / 2)
    y = baseline - subject.height
    canvas = Image.new("RGBA", (CANVAS, CANVAS))
    canvas.alpha_composite(subject, (x, y))
    return canvas, (x, y, x + subject.width, y + subject.height)


def prepare_bug(anchor: Image.Image, width: int = 270) -> Image.Image:
    bug = alpha_crop(anchor)
    height = round(bug.height * width / bug.width)
    return bug.resize((width, height), Image.Resampling.LANCZOS)


def add_bug(
    frame: Image.Image,
    bug: Image.Image,
    top: int,
    center_x: int = CANVAS // 2,
    scale_y: float = 1.0,
) -> Image.Image:
    if scale_y != 1.0:
        bug = bug.resize(
            (bug.width, max(1, round(bug.height * scale_y))),
            Image.Resampling.LANCZOS,
        )
    result = frame.copy()
    x = round(center_x - bug.width / 2)
    result.alpha_composite(bug, (x, top))
    return result


def local_contact_top(
    body: Image.Image,
    companion: Image.Image,
    center_x: int = CANVAS // 2,
    overlap: int = 4,
) -> int:
    """Align a companion to the body's local surface beneath its footprint."""
    body_alpha = np.asarray(body.getchannel("A"))
    companion_alpha = np.asarray(companion.getchannel("A"))
    x0 = round(center_x - companion.width / 2)
    offsets: list[int] = []
    for companion_x in range(companion.width):
        canvas_x = x0 + companion_x
        if not 0 <= canvas_x < CANVAS:
            continue
        companion_ys = np.flatnonzero(companion_alpha[:, companion_x] > 16)
        body_ys = np.flatnonzero(body_alpha[:, canvas_x] > 16)
        if companion_ys.size and body_ys.size:
            offsets.append(int(body_ys[0]) - int(companion_ys[-1]))
    if not offsets:
        raise ValueError("Body and companion have no shared horizontal contact range")
    return round(float(np.median(offsets))) + overlap


def make_frames(
    neutral_anchor: Image.Image,
    squash_anchor: Image.Image,
    bug_anchor: Image.Image,
) -> list[Image.Image]:
    # Scale both generated body anchors uniformly so the luminous core remains square.
    neutral, neutral_bbox = place_subject(neutral_anchor, scale=0.88)
    squash, squash_bbox = place_subject(squash_anchor, scale=0.96)
    bug = prepare_bug(bug_anchor)

    neutral_top = neutral_bbox[1]
    approach_top = max(20, neutral_top - bug.height - 16)
    neutral_contact_top = neutral_top - bug.height + 12
    squash_contact_top = local_contact_top(squash, bug)

    return [
        neutral.copy(),
        add_bug(neutral, bug, approach_top),
        add_bug(neutral, bug, neutral_contact_top),
        add_bug(squash, bug, squash_contact_top, scale_y=0.96),
        add_bug(squash, bug, squash_contact_top - 18),
        add_bug(neutral, bug, max(20, approach_top - 20)),
    ]


def checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, (238, 242, 242))
    draw = ImageDraw.Draw(image)
    alt = (211, 220, 220)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=alt)
    return image


def make_contact_sheet(frames: list[Image.Image], path: Path) -> None:
    tile = 360
    label_height = 42
    sheet = Image.new("RGB", (tile * 3, (tile + label_height) * 2), "white")
    label_font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 22)
    for index, frame in enumerate(frames):
        x = (index % 3) * tile
        y = (index // 3) * (tile + label_height)
        bg = checkerboard((tile, tile))
        preview = frame.resize((tile, tile), Image.Resampling.LANCZOS)
        bg.paste(preview, mask=preview.getchannel("A"))
        sheet.paste(bg, (x, y))
        draw = ImageDraw.Draw(sheet)
        draw.text(
            (x + 12, y + tile + 8),
            f"F{index + 1}  {FRAME_DURATIONS_MS[index]} ms",
            font=label_font,
            fill=(20, 55, 53),
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def alpha_metrics(image: Image.Image) -> dict[str, object]:
    alpha = np.array(image.getchannel("A"))
    ys, xs = np.where(alpha > 16)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]
    return {
        "size": list(image.size),
        "alpha_bbox": bbox,
        "transparent_pixels": int(np.count_nonzero(alpha == 0)),
        "partial_alpha_pixels": int(np.count_nonzero((alpha > 0) & (alpha < 255))),
        "border_is_transparent": bool(
            np.all(alpha[0] == 0)
            and np.all(alpha[-1] == 0)
            and np.all(alpha[:, 0] == 0)
            and np.all(alpha[:, -1] == 0)
        ),
    }


def write_metadata(output: Path, frames: list[Image.Image]) -> None:
    source = output / "source"
    qa = output / "qa"
    motion = {
        "id": "s08-bug-squash",
        "prompt": "一只有两只小眼睛的 Bug 从上方落下，把主体压扁后再抬起。",
        "reference_image": "projects/fangxin/identity/masters/fangxin-v6.png",
        "working_anchors": {
            "neutral": "projects/fangxin/packs/shangbanzhong/work/v6-neutral-rgba.png",
            "max_squash": "projects/fangxin/packs/shangbanzhong/work/s08-squash-approved-rgba.png",
            "bug": "projects/fangxin/packs/shangbanzhong/work/s08-bug-rgba.png",
        },
        "canvas": [CANVAS, CANVAS],
        "loop": True,
        "total_duration_ms": sum(FRAME_DURATIONS_MS),
        "frames": [
            {
                "file": f"frames/{index:03d}.png",
                "duration_ms": FRAME_DURATIONS_MS[index],
                "description": FRAME_DESCRIPTIONS[index],
            }
            for index in range(len(frames))
        ],
    }
    (source / "motion.json").write_text(
        json.dumps(motion, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics = [alpha_metrics(frame) for frame in frames]
    checks = {
        "frame_count_is_six": len(frames) == 6,
        "all_frames_1024_rgba": all(
            frame.mode == "RGBA" and frame.size == (CANVAS, CANVAS)
            for frame in frames
        ),
        "all_borders_transparent": all(m["border_is_transparent"] for m in metrics),
        "duration_in_default_range": 1200 <= sum(FRAME_DURATIONS_MS) <= 2000,
    }
    report = {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "frames": metrics,
        "visual_review_required": [
            "最大受压帧保留母版的右上缺角；缺口左侧上沿允许因挤压圆润隆起",
            "Bug 的两只小眼睛清楚可见且视觉权重低于主体",
            "核心在最大受压帧仍接近正方形",
            "Bug 的落下、停留和抬起顺序无需文字也能读懂",
            "浅色和深色背景下的 Alpha 边缘",
        ],
    }
    (qa / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build(neutral_path: Path, squash_path: Path, bug_path: Path, output: Path) -> None:
    neutral = normalize(neutral_path)
    squash = normalize(squash_path)
    bug = normalize(bug_path)
    frames = make_frames(neutral, squash, bug)

    frame_dir = output / "source" / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    (output / "qa").mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        frame.save(frame_dir / f"{index:03d}.png")

    frames[0].save(
        output / "sticker.webp",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATIONS_MS,
        loop=0,
        lossless=False,
        quality=92,
        method=6,
        minimize_size=True,
        allow_mixed=True,
    )
    make_contact_sheet(frames, output / "qa" / "contact-sheet.png")
    write_metadata(output, frames)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--neutral",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/v6-neutral-rgba.png"),
    )
    parser.add_argument(
        "--squash",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/s08-squash-approved-rgba.png"),
    )
    parser.add_argument(
        "--bug",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/s08-bug-rgba.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/output/s08-bug-squash"),
    )
    args = parser.parse_args()
    build(args.neutral, args.squash, args.bug, args.output)


if __name__ == "__main__":
    main()
