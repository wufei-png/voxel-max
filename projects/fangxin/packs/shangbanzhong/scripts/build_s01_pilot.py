#!/usr/bin/env python3
"""Build the deterministic S01 pilot from the approved neutral RGBA master."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


CANVAS = 1024
FONT_PATH = Path.home() / "Library/Fonts/Sarasa-SuperTTC.ttc"
FONT_INDEX = 301  # Sarasa Mono SC SemiBold in the local SuperTTC.
FRAME_DURATIONS_MS = [160, 180, 220, 120, 600, 160]
FRAME_DESCRIPTIONS = [
    "中性方眼，无文字，核心常亮。",
    "核心下方左侧出现“收”。",
    "右侧出现“到”，并保留“收”。",
    "主体向下压缩约 3%，文字保持，核心短促提亮。",
    "主体向上轻弹，双眼形成实体 ^ ^，文字保持并停留。",
    "主体回到基线和常态方眼，文字淡出后衔接首帧。",
]


def normalize_master(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    return image.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)


def draw_recessed_glyph(
    layer: Image.Image,
    glyph: str,
    center: tuple[int, int],
    opacity: float,
) -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Required font not found: {FONT_PATH}")
    font = ImageFont.truetype(str(FONT_PATH), 66, index=FONT_INDEX)
    bbox = font.getbbox(glyph)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = round(center[0] - width / 2 - bbox[0])
    y = round(center[1] - height / 2 - bbox[1])
    draw = ImageDraw.Draw(layer)

    def a(value: int) -> int:
        return round(value * opacity)

    draw.text((x - 1, y - 1), glyph, font=font, fill=(4, 73, 70, a(115)))
    draw.text((x, y + 2), glyph, font=font, fill=(137, 241, 232, a(45)))
    draw.text((x, y), glyph, font=font, fill=(15, 110, 103, a(235)))


def add_status_text(
    image: Image.Image,
    show_shou: bool,
    show_dao: bool,
    opacity: float = 1.0,
) -> Image.Image:
    layer = Image.new("RGBA", image.size)
    if show_shou:
        draw_recessed_glyph(layer, "收", (417, 660), opacity)
    if show_dao:
        draw_recessed_glyph(layer, "到", (607, 660), opacity)
    return Image.alpha_composite(image, layer)


def brighten_core(image: Image.Image, strength: float) -> Image.Image:
    glow = Image.new("RGBA", image.size)
    draw = ImageDraw.Draw(glow)
    alpha = round(48 * strength)
    draw.rounded_rectangle(
        (459, 474, 577, 596),
        radius=24,
        fill=(225, 255, 252, alpha),
    )
    blurred = glow.filter(ImageFilter.GaussianBlur(18))
    result = Image.alpha_composite(image, blurred)
    return Image.alpha_composite(result, glow)


def transform_subject(
    image: Image.Image,
    scale_y: float = 1.0,
    translate_y: int = 0,
    anchor_bottom: bool = True,
) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return image.copy()
    crop = image.crop(bbox)
    new_height = max(1, round(crop.height * scale_y))
    crop = crop.resize((crop.width, new_height), Image.Resampling.LANCZOS)
    x = bbox[0]
    if anchor_bottom:
        y = bbox[3] - new_height + translate_y
    else:
        y = bbox[1] + translate_y
    canvas = Image.new("RGBA", image.size)
    canvas.alpha_composite(crop, (x, y))
    return canvas


def make_frames(master: Image.Image, happy_master: Image.Image) -> list[Image.Image]:
    frame_0 = master.copy()
    frame_1 = brighten_core(add_status_text(master, True, False), 0.45)
    frame_2 = brighten_core(add_status_text(master, True, True), 0.7)
    frame_3 = transform_subject(
        brighten_core(add_status_text(master, True, True), 0.95),
        scale_y=0.97,
    )
    frame_4 = brighten_core(add_status_text(happy_master, True, True), 1.0)
    frame_4 = transform_subject(frame_4, translate_y=-26)
    frame_5 = add_status_text(master, True, True, opacity=0.24)
    return [frame_0, frame_1, frame_2, frame_3, frame_4, frame_5]


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
        "id": "s01-shoudao",
        "prompt": "先显示“收”，再显示“到”，最后双眼变成实体 ^ ^ 并轻弹一下。",
        "reference_image": "projects/fangxin/identity/masters/fangxin-v6.png",
        "working_master": "projects/fangxin/packs/shangbanzhong/work/v6-neutral-rgba-1024.png",
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
    report = {
        "status": "pass" if all(m["border_is_transparent"] for m in metrics) else "fail",
        "checks": {
            "frame_count": len(frames),
            "all_frames_1024_rgba": all(frame.mode == "RGBA" and frame.size == (CANVAS, CANVAS) for frame in frames),
            "all_borders_transparent": all(m["border_is_transparent"] for m in metrics),
            "duration_in_default_range": 1200 <= sum(FRAME_DURATIONS_MS) <= 2000,
        },
        "frames": metrics,
        "visual_review_required": [
            "收、到的位置和顺序",
            "最终实体 ^ ^ 眼的材质与比例",
            "压缩和轻弹是否像同一角色",
            "浅色和深色背景下的 Alpha 边缘",
        ],
    }
    (qa / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build(
    master_path: Path,
    happy_master_path: Path,
    output: Path,
    normalized_master_path: Path,
) -> None:
    master = normalize_master(master_path)
    happy_master = normalize_master(happy_master_path)
    normalized_master_path.parent.mkdir(parents=True, exist_ok=True)
    master.save(normalized_master_path)

    frames = make_frames(master, happy_master)
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
        "--happy-master",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/v6-happy-rgba.png"),
    )
    parser.add_argument(
        "--master",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/v6-neutral-rgba.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/output/s01-shoudao"),
    )
    parser.add_argument(
        "--normalized-master",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/v6-neutral-rgba-1024.png"),
    )
    args = parser.parse_args()
    build(args.master, args.happy_master, args.output, args.normalized_master)


if __name__ == "__main__":
    main()
