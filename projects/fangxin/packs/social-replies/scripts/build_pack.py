#!/usr/bin/env python3
"""Build and QA the complete 12-sticker source pack for 《方芯回你了》.

This is deliberately pack-specific. It does not call the repository's manual
animated-sticker-maker Skill and must not be treated as a generic API.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


CANVAS = 1024
FONT_PATH = Path.home() / "Library/Fonts/Sarasa-SuperTTC.ttc"
FONT_INDEX = 301  # Sarasa Mono SC SemiBold in the local SuperTTC.
CYAN_WHITE = (231, 255, 251)
SUCCESS_GREEN = (116, 242, 106)
WARNING_YELLOW = (255, 210, 74)
CORAL_RED = (255, 92, 87)
DIM_CYAN = (120, 184, 181)
TEXT_DARK = (15, 110, 103)

ROOT = Path("projects/fangxin/packs/social-replies")
ANCHORS = ROOT / "work" / "anchors" / "rgba"
OUTPUT = ROOT / "output"
PACK_QA = ROOT / "qa"

IDENTITY_LOCK = {
    "subject": "方芯 / Voxel Max",
    "fixed": [
        "右上向内缺角",
        "中央圆角方形状态核心及外框",
        "青绿色 2.5D 圆角方块本体",
        "两侧深色实体眼部模块",
        "常态无手脚、无嘴、无眉毛",
    ],
    "forbidden": [
        "缺角镜像、消失或被勾填平",
        "核心拉成长条或移出鼻位",
        "主体整体变色",
        "新增肢体、场景、第二主体或复杂 UI",
    ],
}


def normalize(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize(
        (CANVAS, CANVAS), Image.Resampling.LANCZOS
    )


def fit_subject(path: Path, target_width: int, target_height: int, center_y: int) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"anchor has no visible pixels: {path}")
    subject = image.crop(bbox)
    subject.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS))
    x = round((CANVAS - subject.width) / 2)
    y = round(center_y - subject.height / 2)
    canvas.alpha_composite(subject, (x, y))
    return canvas


def font(size: int) -> ImageFont.FreeTypeFont:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"required project font not found: {FONT_PATH}")
    return ImageFont.truetype(str(FONT_PATH), size, index=FONT_INDEX)


def subject_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("frame has no visible subject")
    return bbox


def detect_core_box(image: Image.Image) -> tuple[int, int, int, int]:
    rgb = np.asarray(image.convert("RGB"))
    alpha = np.asarray(image.getchannel("A"))
    x0, x1 = round(CANVAS * 0.38), round(CANVAS * 0.62)
    y0, y1 = round(CANVAS * 0.35), round(CANVAS * 0.70)
    roi = rgb[y0:y1, x0:x1]
    roi_alpha = alpha[y0:y1, x0:x1]
    bright = (roi.min(axis=2) > 170) & (roi_alpha > 16)
    ys, xs = np.where(bright)
    if not xs.size:
        return (458, 473, 578, 597)
    box = (
        int(xs.min() + x0),
        int(ys.min() + y0),
        int(xs.max() + x0 + 1),
        int(ys.max() + y0 + 1),
    )
    width, height = box[2] - box[0], box[3] - box[1]
    if not (55 <= width <= 170 and 55 <= height <= 170):
        return (458, 473, 578, 597)
    return box


def detect_core_face_mask(
    image: Image.Image,
    max_channel_spread: int | None = None,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Return the exact luminous inner-core mask instead of an inferred inset box."""
    rgba = np.asarray(image.convert("RGBA"))
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    x0, x1 = round(CANVAS * 0.42), round(CANVAS * 0.58)
    y0, y1 = round(CANVAS * 0.42), round(CANVAS * 0.64)
    roi = rgb[y0:y1, x0:x1]
    roi_alpha = alpha[y0:y1, x0:x1]
    face = (roi.min(axis=2) > 195) & (roi_alpha > 16)
    if max_channel_spread is not None:
        spread = roi.max(axis=2) - roi.min(axis=2)
        face &= spread < max_channel_spread
    ys, xs = np.where(face)

    if xs.size:
        box = (
            int(xs.min() + x0),
            int(ys.min() + y0),
            int(xs.max() + x0 + 1),
            int(ys.max() + y0 + 1),
        )
        width, height = box[2] - box[0], box[3] - box[1]
    else:
        width = height = 0

    if not (80 <= width <= 115 and 80 <= height <= 115):
        outer = detect_core_box(image)
        side = round(min(outer[2] - outer[0], outer[3] - outer[1]) * 0.83)
        cx = round((outer[0] + outer[2]) / 2)
        cy = round((outer[1] + outer[3]) / 2)
        box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
        mask = Image.new("L", image.size)
        ImageDraw.Draw(mask).rounded_rectangle(
            box,
            radius=max(12, round(side * 0.22)),
            fill=255,
        )
        return mask.filter(ImageFilter.GaussianBlur(0.6)), box

    if max_channel_spread is not None:
        mask = Image.new("L", image.size)
        ImageDraw.Draw(mask).rounded_rectangle(
            box,
            radius=max(12, round(min(width, height) * 0.22)),
            fill=255,
        )
        return mask.filter(ImageFilter.GaussianBlur(0.6)), box

    mask_array = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    mask_array[y0:y1, x0:x1] = face.astype(np.uint8) * 255
    mask = Image.fromarray(mask_array, "L").filter(ImageFilter.GaussianBlur(0.6))
    return mask, box


def scale_mask(
    mask: Image.Image,
    box: tuple[int, int, int, int],
    scale: float,
) -> Image.Image:
    """Scale a local mask around its own center; used only for soft glow."""
    if abs(scale - 1.0) < 0.001:
        return mask
    crop = mask.crop(box)
    width = max(1, round(crop.width * scale))
    height = max(1, round(crop.height * scale))
    crop = crop.resize((width, height), Image.Resampling.LANCZOS)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    x = round(cx - width / 2)
    y = round(cy - height / 2)
    result = Image.new("L", mask.size)
    result.paste(crop, (x, y))
    return result


def adjust_face_mask(
    mask: Image.Image,
    box: tuple[int, int, int, int],
    inset: int = 0,
    top_extend: int = 0,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Apply a restrained sticker-specific fit correction inside the core face."""
    inset = max(0, min(10, inset))
    top_extend = max(0, min(4, top_extend))
    result = mask
    if inset:
        result = result.filter(ImageFilter.MinFilter(inset * 2 + 1))
    if top_extend:
        source = np.asarray(result)
        extended = source.copy()
        extended[:-top_extend] = np.maximum(
            extended[:-top_extend], source[top_extend:]
        )
        result = Image.fromarray(extended, "L")
    adjusted_box = result.getbbox()
    return result, adjusted_box if adjusted_box is not None else box


def set_core_state(
    image: Image.Image,
    color: tuple[int, int, int],
    level: float,
    face_scale: float = 1.0,
    face_inset: int = 0,
    top_extend: int = 0,
    top_cover: int = 0,
    tint_boost: int = 0,
    glow_strength: float = 1.0,
    face_spread_max: int | None = None,
    dim_strength: float = 1.0,
) -> Image.Image:
    level = max(0.0, min(1.0, level))
    face_scale = max(0.92, min(1.08, face_scale))
    face_mask, face_box = detect_core_face_mask(
        image,
        max_channel_spread=face_spread_max,
    )
    face_mask, face_box = adjust_face_mask(
        face_mask,
        face_box,
        inset=face_inset,
        top_extend=top_extend,
    )
    result = image.copy()
    if level < 0.35:
        dim_strength = max(0.0, min(2.5, dim_strength))
        dim_alpha = face_mask.point(
            lambda value: min(
                255,
                round(
                    value
                    * 92
                    * (0.35 - level)
                    / 0.35
                    / 255
                    * dim_strength
                ),
            )
        )
        dim = Image.new("RGBA", image.size, (30, 100, 102, 0))
        dim.putalpha(dim_alpha)
        result = Image.alpha_composite(result, dim)

    tint_boost = max(0, min(100, tint_boost))
    tint_opacity = min(255, 35 + 110 * level + tint_boost)
    tint_alpha = face_mask.point(
        lambda value: round(value * tint_opacity / 255)
    )
    tint = Image.new("RGBA", image.size, (*color, 0))
    tint.putalpha(tint_alpha)
    result = Image.alpha_composite(result, tint)

    top_cover = max(0, min(8, top_cover))
    if top_cover:
        cover_mask = Image.new("L", image.size)
        cover_mask.paste(
            face_mask.crop(
                (face_box[0], face_box[1], face_box[2], face_box[1] + top_cover)
            ).point(lambda value: round(value * 105 / 255)),
            (face_box[0], face_box[1]),
        )
        cover = Image.new("RGBA", image.size, (*color, 0))
        cover.putalpha(cover_mask)
        result = Image.alpha_composite(result, cover)

    glow_mask = scale_mask(face_mask, face_box, face_scale).filter(
        ImageFilter.GaussianBlur(12)
    )
    glow_strength = max(0.0, min(1.0, glow_strength))
    glow_alpha = glow_mask.point(
        lambda value: round(value * (8 + 30 * level) * glow_strength / 255)
    )
    glow = Image.new("RGBA", image.size, (*color, 0))
    glow.putalpha(glow_alpha)
    return Image.alpha_composite(result, glow)


def transform_subject(
    image: Image.Image,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    dx: int = 0,
    dy: int = 0,
    anchor_bottom: bool = True,
) -> Image.Image:
    bbox = subject_bbox(image)
    crop = image.crop(bbox)
    size = (
        max(1, round(crop.width * scale_x)),
        max(1, round(crop.height * scale_y)),
    )
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    x = round((CANVAS - crop.width) / 2 + dx)
    y = bbox[3] - crop.height + dy if anchor_bottom else round((CANVAS - crop.height) / 2 + dy)
    canvas = Image.new("RGBA", image.size)
    canvas.alpha_composite(crop, (x, y))
    return canvas


def rotate_subject(image: Image.Image, angle: float) -> Image.Image:
    """Rotate around an approximate bottom-center pivot, not canvas center."""
    bbox = subject_bbox(image)
    crop = image.crop(bbox)
    rotated = crop.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )
    x = round((CANVAS - rotated.width) / 2)
    y = bbox[3] - rotated.height
    canvas = Image.new("RGBA", image.size)
    canvas.alpha_composite(rotated, (x, y))
    return canvas


def vertical_pose_warp(
    image: Image.Image,
    progress: float,
    top_shift: float,
) -> Image.Image:
    """Shift the upper silhouette vertically while keeping the base planted."""
    progress = max(0.0, min(1.0, progress))
    if progress == 0:
        return image.copy()
    source = np.asarray(image).astype(np.float32)
    alpha = source[..., 3]
    ys, xs = np.where(alpha > 16)
    top, bottom = int(ys.min()), int(ys.max() + 1)
    yy, xx = np.indices((CANVAS, CANVAS), dtype=np.float32)
    yn = np.clip((yy - top) / max(1, bottom - top), 0.0, 1.0)
    displacement = top_shift * progress * np.power(1.0 - yn, 1.7)
    source_y = yy - displacement
    source_x = xx

    x0 = np.floor(source_x).astype(np.int32)
    y0 = np.floor(source_y).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    valid = (x0 >= 0) & (y0 >= 0) & (x1 < CANVAS) & (y1 < CANVAS)
    x0c, x1c = np.clip(x0, 0, CANVAS - 1), np.clip(x1, 0, CANVAS - 1)
    y0c, y1c = np.clip(y0, 0, CANVAS - 1), np.clip(y1, 0, CANVAS - 1)
    wx = (source_x - x0)[..., None]
    wy = (source_y - y0)[..., None]
    top_mix = source[y0c, x0c] * (1.0 - wx) + source[y0c, x1c] * wx
    bottom_mix = source[y1c, x0c] * (1.0 - wx) + source[y1c, x1c] * wx
    output = top_mix * (1.0 - wy) + bottom_mix * wy
    output[~valid] = 0
    return Image.fromarray(np.clip(np.rint(output), 0, 255).astype(np.uint8), "RGBA")


def horizontal_wave(
    image: Image.Image,
    progress: float,
    phase: float,
    amplitude: float = 14.0,
) -> Image.Image:
    """Apply one restrained, reversible soft-body wave across horizontal rows."""
    progress = max(0.0, min(1.0, progress))
    if progress == 0:
        return image.copy()
    source = np.asarray(image).astype(np.float32)
    alpha = source[..., 3]
    ys, xs = np.where(alpha > 16)
    top, bottom = int(ys.min()), int(ys.max() + 1)
    yy, xx = np.indices((CANVAS, CANVAS), dtype=np.float32)
    yn = np.clip((yy - top) / max(1, bottom - top), 0.0, 1.0)
    row_shift = amplitude * progress * np.sin(2.0 * math.pi * yn + phase)
    source_x = xx - row_shift
    source_y = yy

    x0 = np.floor(source_x).astype(np.int32)
    y0 = np.floor(source_y).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    valid = (x0 >= 0) & (y0 >= 0) & (x1 < CANVAS) & (y1 < CANVAS)
    x0c, x1c = np.clip(x0, 0, CANVAS - 1), np.clip(x1, 0, CANVAS - 1)
    y0c, y1c = np.clip(y0, 0, CANVAS - 1), np.clip(y1, 0, CANVAS - 1)
    wx = (source_x - x0)[..., None]
    wy = (source_y - y0)[..., None]
    top_mix = source[y0c, x0c] * (1.0 - wx) + source[y0c, x1c] * wx
    bottom_mix = source[y1c, x0c] * (1.0 - wx) + source[y1c, x1c] * wx
    output = top_mix * (1.0 - wy) + bottom_mix * wy
    output[~valid] = 0
    return Image.fromarray(np.clip(np.rint(output), 0, 255).astype(np.uint8), "RGBA")


def eye_micro_wobble(
    image: Image.Image,
    amount: float,
    amplitude: float = 7.0,
) -> Image.Image:
    """Locally move both eye regions together without adding a second action."""
    amount = max(-1.0, min(1.0, amount))
    if abs(amount) < 0.001:
        return image.copy()
    source = np.asarray(image).astype(np.float32)
    yy, xx = np.indices((CANVAS, CANVAS), dtype=np.float32)
    influence = np.zeros((CANVAS, CANVAS), dtype=np.float32)
    for center_x in (310.0, 724.0):
        distance = ((xx - center_x) / 88.0) ** 2 + ((yy - 535.0) / 58.0) ** 2
        influence = np.maximum(influence, np.exp(-2.4 * distance))
    source_y = yy - amplitude * amount * influence
    source_x = xx

    x0 = np.floor(source_x).astype(np.int32)
    y0 = np.floor(source_y).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    valid = (x0 >= 0) & (y0 >= 0) & (x1 < CANVAS) & (y1 < CANVAS)
    x0c, x1c = np.clip(x0, 0, CANVAS - 1), np.clip(x1, 0, CANVAS - 1)
    y0c, y1c = np.clip(y0, 0, CANVAS - 1), np.clip(y1, 0, CANVAS - 1)
    wx = (source_x - x0)[..., None]
    wy = (source_y - y0)[..., None]
    top_mix = source[y0c, x0c] * (1.0 - wx) + source[y0c, x1c] * wx
    bottom_mix = source[y1c, x0c] * (1.0 - wx) + source[y1c, x1c] * wx
    output = top_mix * (1.0 - wy) + bottom_mix * wy
    output[~valid] = 0
    return Image.fromarray(np.clip(np.rint(output), 0, 255).astype(np.uint8), "RGBA")


def dim_subject(image: Image.Image, factor: float) -> Image.Image:
    factor = max(0.0, min(1.0, factor))
    rgba = np.asarray(image).astype(np.float32).copy()
    rgba[..., :3] *= factor
    return Image.fromarray(np.clip(np.rint(rgba), 0, 255).astype(np.uint8), "RGBA")


def add_recessed_text(image: Image.Image, text: str, opacity: float = 1.0) -> Image.Image:
    if opacity <= 0:
        return image.copy()
    text_font = font(72 if len(text) <= 2 else 64)
    layer = Image.new("RGBA", image.size)
    draw = ImageDraw.Draw(layer)
    bbox = subject_bbox(image)
    core = detect_core_box(image)
    glyph = draw.textbbox((0, 0), text, font=text_font)
    width = glyph[2] - glyph[0]
    height = glyph[3] - glyph[1]
    x = (core[0] + core[2]) / 2 - width / 2 - glyph[0]
    available_center = core[3] + (bbox[3] - core[3]) * 0.42
    y = available_center - height / 2 - glyph[1]

    def alpha(value: int) -> int:
        return round(value * opacity)

    draw.text((x - 1, y - 1), text, font=text_font, fill=(4, 73, 70, alpha(115)))
    draw.text((x, y + 2), text, font=text_font, fill=(137, 241, 232, alpha(45)))
    draw.text((x, y), text, font=text_font, fill=(*TEXT_DARK, alpha(235)))
    return Image.alpha_composite(image, layer)


def add_core_check(image: Image.Image, progress: float, opacity: float) -> Image.Image:
    if progress <= 0 or opacity <= 0:
        return image.copy()
    core = detect_core_box(image)
    core_width = core[2] - core[0]
    core_height = core[3] - core[1]
    # Dock the confirmation mark to the core's lower-right edge. Keeping it
    # off the vertical face axis avoids reading the mark as a mouth, while
    # leaving the permanent upper-right notch visually unoccupied.
    cx = core[2] + core_width * 0.20
    cy = core[3] + core_height * 0.10
    full = [
        (round(cx - core_width * 0.30), round(cy - core_height * 0.03)),
        (round(cx - core_width * 0.07), round(cy + core_height * 0.20)),
        (round(cx + core_width * 0.40), round(cy - core_height * 0.31)),
    ]
    first_fraction = min(1.0, progress * 2.0)
    second_fraction = max(0.0, min(1.0, progress * 2.0 - 1.0))
    points = [full[0]]
    points.append(
        (
            round(full[0][0] + (full[1][0] - full[0][0]) * first_fraction),
            round(full[0][1] + (full[1][1] - full[0][1]) * first_fraction),
        )
    )
    if second_fraction > 0:
        points.append(
            (
                round(full[1][0] + (full[2][0] - full[1][0]) * second_fraction),
                round(full[1][1] + (full[2][1] - full[1][1]) * second_fraction),
            )
        )
    layer = Image.new("RGBA", image.size)
    glow = Image.new("RGBA", image.size)
    if len(points) >= 2:
        ImageDraw.Draw(glow).line(points, fill=(*SUCCESS_GREEN, round(90 * opacity)), width=30, joint="curve")
        layer = Image.alpha_composite(layer, glow.filter(ImageFilter.GaussianBlur(12)))
        draw = ImageDraw.Draw(layer)
        draw.line(points, fill=(25, 116, 75, round(220 * opacity)), width=24, joint="curve")
        draw.line(points, fill=(165, 255, 145, round(255 * opacity)), width=14, joint="curve")
        for point in (points[0], points[-1]):
            draw.ellipse(
                (point[0] - 7, point[1] - 7, point[0] + 7, point[1] + 7),
                fill=(165, 255, 145, round(255 * opacity)),
            )
    return Image.alpha_composite(image, layer)


def asymmetric_slump(
    image: Image.Image,
    top_progress: float,
    bottom_progress: float,
) -> Image.Image:
    top_progress = max(0.0, min(1.0, top_progress))
    bottom_progress = max(0.0, min(1.0, bottom_progress))
    if top_progress == 0 and bottom_progress == 0:
        return image.copy()
    source = np.asarray(image).astype(np.float32)
    alpha = source[..., 3]
    ys, xs = np.where(alpha > 16)
    top, bottom = int(ys.min()), int(ys.max() + 1)
    left, right = int(xs.min()), int(xs.max() + 1)

    yy, xx = np.indices((CANVAS, CANVAS), dtype=np.float32)
    xn = np.clip((xx - left) / max(1, right - left), 0.0, 1.0)
    yn = np.clip((yy - top) / max(1, bottom - top), 0.0, 1.0)
    # The viewer-left upper corner loses support first and drops farther. The
    # lower-left corner follows with less displacement; the right edge and the
    # upper-right notch stay nearly fixed. Different top/bottom amplitudes keep
    # the result from reading as a rigid rotation or a tilted floor plane.
    left_weight = np.power(1.0 - xn, 2.2)
    displacement = left_weight * (
        (1.0 - yn) * 52.0 * top_progress
        + yn * 28.0 * bottom_progress
    )
    source_y = yy - displacement
    inward_shift = left_weight * (1.0 - 0.45 * yn) * 9.0 * top_progress
    source_x = xx - inward_shift

    x0 = np.floor(source_x).astype(np.int32)
    y0 = np.floor(source_y).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1
    valid = (x0 >= 0) & (y0 >= 0) & (x1 < CANVAS) & (y1 < CANVAS)
    x0c, x1c = np.clip(x0, 0, CANVAS - 1), np.clip(x1, 0, CANVAS - 1)
    y0c, y1c = np.clip(y0, 0, CANVAS - 1), np.clip(y1, 0, CANVAS - 1)
    wx = (source_x - x0)[..., None]
    wy = (source_y - y0)[..., None]
    top_mix = source[y0c, x0c] * (1.0 - wx) + source[y0c, x1c] * wx
    bottom_mix = source[y1c, x0c] * (1.0 - wx) + source[y1c, x1c] * wx
    output = top_mix * (1.0 - wy) + bottom_mix * wy
    output[~valid] = 0
    return Image.fromarray(np.clip(np.rint(output), 0, 255).astype(np.uint8), "RGBA")


def s01_frames(neutral: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    frames = [
        set_core_state(neutral, CYAN_WHITE, 0.30, top_extend=2, top_cover=6),
        add_core_check(
            transform_subject(
                set_core_state(
                    neutral, SUCCESS_GREEN, 0.55, top_extend=2, top_cover=6
                ),
                scale_y=0.98,
            ),
            0.42,
            0.70,
        ),
        add_core_check(
            transform_subject(
                set_core_state(
                    neutral, SUCCESS_GREEN, 0.90, top_extend=2, top_cover=6
                ),
                dy=-13,
            ),
            1.0,
            1.0,
        ),
        add_core_check(
            set_core_state(
                neutral, SUCCESS_GREEN, 0.82, top_extend=2, top_cover=6
            ),
            1.0,
            1.0,
        ),
        add_core_check(
            set_core_state(
                neutral, CYAN_WHITE, 0.26, top_extend=2, top_cover=6
            ),
            1.0,
            0.18,
        ),
    ]
    durations = [180, 160, 160, 580, 180]
    descriptions = [
        "常态方芯与青白核心，右上缺角保持清楚。",
        "主体轻压，核心右下缘开始画出绿色小勾，核心转绿。",
        "主体短促回弹，小勾完整，核心达到绿色高亮。",
        "贴合核心右下缘的完整小勾、绿色核心和常态眼稳定停留，表达同意或许可。",
        "小勾淡出，核心回到青白后衔接首帧。",
    ]
    return frames, durations, descriptions


def s03_frames(half_eyes: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    slump_levels = [
        (0.18, 0.03),
        (0.55, 0.22),
        (0.88, 0.62),
        (1.00, 1.00),
        (0.22, 0.05),
    ]
    text_opacity = [0.25, 0.60, 0.90, 1.00, 0.30]
    frames = []
    for (top_level, bottom_level), opacity in zip(slump_levels, text_opacity):
        core_level = 0.12 + 0.10 * (1.0 - top_level)
        base = set_core_state(half_eyes, (120, 184, 181), core_level)
        frames.append(
            add_recessed_text(
                asymmetric_slump(base, top_level, bottom_level),
                "无语",
                opacity,
            )
        )
    durations = [180, 180, 180, 600, 180]
    descriptions = [
        "半闭横眼，左上先失去支撑，文字低透明度出现。",
        "左上明显下塌，左下稍后轻微跟随，核心降亮。",
        "左上主塌、左下跟随的非对称软塌接近峰值，文字基本可读。",
        "左上降幅约为左下两倍，右侧与缺角稳定；半闭眼、低亮核心和“无语”停留。",
        "左上先回弹、左下轻微软塌，文字淡出后衔接首帧。",
    ]
    return frames, durations, descriptions


def s07_frames(forward_anchor: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.98, 0.95, 0, 10, 0.35, 0.35),
        (1.00, 0.92, 0, 24, 0.65, 0.70),
        (1.015, 1.00, 0, -20, 1.00, 1.00),
        (1.00, 0.985, 0, -8, 0.92, 1.00),
        (0.99, 0.96, 0, 12, 0.42, 0.42),
    ]
    frames = []
    for sx, sy, dx, dy, core_level, text_opacity in specs:
        frame = set_core_state(forward_anchor, CYAN_WHITE, core_level)
        frame = transform_subject(frame, scale_x=sx, scale_y=sy, dx=dx, dy=dy)
        frames.append(add_recessed_text(frame, "加油", text_opacity))
    durations = [180, 140, 160, 600, 180]
    descriptions = [
        "前倾锚点轻微压缩，核心低亮，“加油”低透明度出现。",
        "主体继续蓄力压缩，核心和文字同步提亮。",
        "主体向前上方推进并抬升，核心达到高亮。",
        "前倾推进姿态、青白核心和“加油”稳定停留。",
        "主体回到轻压状态，核心和文字回落后衔接首帧。",
    ]
    return frames, durations, descriptions


def s02_frames(half_eyes: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    base_low = set_core_state(
        half_eyes,
        CORAL_RED,
        0.32,
        tint_boost=55,
        glow_strength=0.25,
        face_spread_max=45,
    )
    base_high = set_core_state(
        half_eyes,
        CORAL_RED,
        0.78,
        tint_boost=55,
        glow_strength=0.25,
        face_spread_max=45,
    )
    frames = [
        add_recessed_text(base_low, "NO", 0.38),
        add_recessed_text(
            rotate_subject(
                set_core_state(
                    half_eyes,
                    CORAL_RED,
                    0.52,
                    tint_boost=55,
                    glow_strength=0.25,
                    face_spread_max=45,
                ),
                7.0,
            ),
            "NO",
            0.68,
        ),
        add_recessed_text(rotate_subject(base_high, -7.0), "NO", 0.92),
        add_recessed_text(
            set_core_state(
                half_eyes,
                CORAL_RED,
                0.70,
                tint_boost=55,
                glow_strength=0.25,
                face_spread_max=45,
            ),
            "NO",
            1.0,
        ),
        add_recessed_text(base_low, "NO", 0.38),
    ]
    durations = [180, 150, 150, 580, 180]
    descriptions = [
        "半闭横眼、低亮珊瑚红核心，核心下方机身文字“NO”低透明度出现。",
        "主体以底部中心为支点向画面左侧转约 7°，机身文字“NO”同步显现。",
        "主体越过中线向画面右侧转约 7°，核心和机身文字“NO”同步提亮。",
        "主体回到中线，半闭横眼、红色核心和核心下方“NO”稳定停留，表达拒绝。",
        "回到与首帧一致的低亮拒绝态，机身文字“NO”回落后循环。",
    ]
    return frames, durations, descriptions


def s04_frames(happy_eyes: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.36, 0.00, 0.0, 1.00, 1.00, 0.00, 0.18),
        (0.58, 1.00, 0.0, 1.00, 1.00, 1.00, 0.48),
        (0.82, 1.00, math.pi, 1.00, 1.00, -1.00, 0.86),
        (0.74, 0.00, 0.0, 1.01, 0.99, 0.00, 1.00),
        (0.36, 0.10, 0.0, 1.00, 1.00, 0.10, 0.24),
    ]
    frames = []
    for core_level, wave, phase, scale_x, scale_y, eye_wobble, text_opacity in specs:
        frame = set_core_state(happy_eyes, CYAN_WHITE, core_level)
        if wave > 0:
            frame = horizontal_wave(frame, wave, phase)
        frame = eye_micro_wobble(frame, eye_wobble)
        if abs(scale_x - 1.0) > 0.001 or abs(scale_y - 1.0) > 0.001:
            frame = transform_subject(frame, scale_x=scale_x, scale_y=scale_y)
        frames.append(add_recessed_text(frame, "hhh!", text_opacity))
    durations = [200, 220, 220, 740, 200]
    descriptions = [
        "实体开心眼、低亮青白核心，机身文字“hhh!”低透明度出现。",
        "主体形成第一相位的柔软横向波浪，双眼随波局部上移，文字继续显现。",
        "波浪反相，双眼同步向相反方向轻移，核心和“hhh!”提亮。",
        "主体恢复为略微舒展的开心姿态，开心眼、青白核心和“hhh!”稳定停留。",
        "回到接近首帧的轻微余震，眼部和文字同步回落后循环。",
    ]
    return frames, durations, descriptions


def s05_frames(neutral: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.32, 1.00, 0.25),
        (0.58, 1.03, 0.55),
        (0.96, 1.06, 0.88),
        (0.82, 1.04, 1.00),
        (0.34, 1.00, 0.30),
    ]
    frames = [
        add_recessed_text(
            set_core_state(neutral, CYAN_WHITE, core_level, face_scale=face_scale),
            "谢谢",
            text_opacity,
        )
        for core_level, face_scale, text_opacity in specs
    ]
    durations = [180, 180, 180, 620, 180]
    descriptions = [
        "核心低亮，文字“谢谢”低透明度出现。",
        "核心光场柔和扩张约 3%，亮度上升。",
        "核心光场扩张到约 6% 并达到峰值，文字基本可读。",
        "核心回落到约 4% 的温和高亮，文字“谢谢”稳定停留。",
        "核心和文字回落到接近首帧后循环。",
    ]
    return frames, durations, descriptions


def s06_frames(neutral: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.965, 0.965, 0.30, 0.28),
        (0.985, 0.985, 0.52, 0.58),
        (1.01, 1.01, 0.78, 0.88),
        (1.00, 1.00, 0.72, 1.00),
        (0.97, 0.97, 0.34, 0.34),
    ]
    frames = []
    for scale_x, scale_y, core_level, text_opacity in specs:
        frame = set_core_state(neutral, CYAN_WHITE, core_level)
        frame = transform_subject(frame, scale_x=scale_x, scale_y=scale_y)
        frames.append(add_recessed_text(frame, "没事", text_opacity))
    durations = [180, 180, 180, 600, 180]
    descriptions = [
        "主体轻微内缩约 3.5%，核心低亮，文字开始出现。",
        "主体恢复到约 98.5%，核心逐渐稳定。",
        "主体轻微越过基线约 1%，形成柔和释然回弹。",
        "主体回到常态，青白核心和“没事”稳定停留。",
        "回到接近首帧的轻微内缩态后循环。",
    ]
    return frames, durations, descriptions


def s08_frames(neutral: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.12, 0.28, 0.25),
        (0.45, 0.42, 0.55),
        (0.85, 0.60, 0.88),
        (1.00, 0.56, 1.00),
        (0.18, 0.30, 0.30),
    ]
    frames = []
    for progress, core_level, text_opacity in specs:
        frame = set_core_state(neutral, CYAN_WHITE, core_level)
        frame = vertical_pose_warp(frame, progress, top_shift=30.0)
        frames.append(add_recessed_text(frame, "辛苦了", text_opacity))
    durations = [200, 200, 200, 620, 200]
    descriptions = [
        "主体保持直立，文字“辛苦了”低透明度出现。",
        "上部轮廓开始缓慢前压，核心略降。",
        "前倾致意接近峰值，文字基本可读。",
        "上部下移约 3%、底部稳定，形成克制致意并停留。",
        "主体开始恢复直立，文字淡出并循环。",
    ]
    return frames, durations, descriptions


def s09_frames(
    neutral: Image.Image,
    half_eyes: Image.Image,
) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (half_eyes, 0.10, 0.30, 0.25),
        (neutral, 0.42, 0.56, 0.58),
        (neutral, 1.00, 0.92, 0.90),
        (neutral, 0.85, 0.82, 1.00),
        (half_eyes, 0.15, 0.34, 0.30),
    ]
    frames = []
    for anchor, progress, core_level, text_opacity in specs:
        frame = set_core_state(anchor, CYAN_WHITE, core_level)
        frame = vertical_pose_warp(frame, progress, top_shift=-22.0)
        frames.append(add_recessed_text(frame, "厉害", text_opacity))
    durations = [160, 140, 160, 600, 160]
    descriptions = [
        "半闭前态、核心低亮，文字“厉害”开始出现。",
        "双眼睁回常态方眼，主体开始后仰。",
        "上部向后打开并上提约 2%，核心快速提亮。",
        "常态最大眼形、短促后仰姿态和“厉害”稳定停留。",
        "回到接近首帧的半闭前态后循环。",
    ]
    return frames, durations, descriptions


def s10_frames(neutral: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.12, 0.28, 0.25),
        (0.50, 0.22, 0.55),
        (0.85, 0.16, 0.88),
        (1.00, 0.14, 1.00),
        (0.18, 0.26, 0.30),
    ]
    frames = []
    for progress, core_level, text_opacity in specs:
        frame = set_core_state(neutral, DIM_CYAN, core_level)
        frame = transform_subject(
            frame,
            scale_x=1.0 - 0.04 * progress,
            scale_y=1.0 - 0.035 * progress,
            dy=round(18 * progress),
        )
        frames.append(add_recessed_text(frame, "抱歉", text_opacity))
    durations = [200, 200, 200, 620, 200]
    descriptions = [
        "主体接近常态，核心偏低亮，文字“抱歉”开始出现。",
        "主体向内收缩约 2% 并轻微下沉。",
        "内收接近 4%，下沉接近峰值，文字基本可读。",
        "克制的内收下沉姿态、低亮核心和“抱歉”稳定停留。",
        "主体开始恢复，文字淡出并循环。",
    ]
    return frames, durations, descriptions


def s11_frames(focus_eyes: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.08, 0.26, 0.25),
        (0.35, 0.42, 0.55),
        (0.75, 0.64, 0.88),
        (1.00, 0.58, 1.00),
        (0.12, 0.28, 0.30),
    ]
    frames = []
    for progress, core_level, text_opacity in specs:
        frame = set_core_state(
            focus_eyes,
            WARNING_YELLOW,
            core_level,
            top_extend=2,
            top_cover=6,
        )
        frame = rotate_subject(frame, -7.0 * progress)
        frames.append(add_recessed_text(frame, "真的假的", text_opacity))
    durations = [180, 200, 200, 620, 180]
    descriptions = [
        "专注眼、低亮黄色核心，文字“真的假的”开始出现。",
        "主体围绕底部中心向画面右侧慢倾约 2.5°。",
        "慢倾加深到约 5.5°，核心提亮。",
        "向单侧倾斜约 7° 的审视姿态和“真的假的”稳定停留。",
        "回到接近首帧的小角度倾斜后循环。",
    ]
    return frames, durations, descriptions


def s12_frames(half_eyes: Image.Image) -> tuple[list[Image.Image], list[int], list[str]]:
    specs = [
        (0.10, 0.20, 0.25),
        (0.40, 0.14, 0.55),
        (0.75, 0.08, 0.88),
        (1.00, 0.05, 1.00),
        (0.15, 0.18, 0.30),
    ]
    frames = []
    for progress, core_level, text_opacity in specs:
        frame = set_core_state(
            half_eyes,
            DIM_CYAN,
            core_level,
            face_spread_max=45,
            dim_strength=1.8,
            glow_strength=0.35,
        )
        frame = transform_subject(frame, dy=round(26 * progress))
        frame = dim_subject(frame, 1.0 - 0.16 * progress)
        frames.append(add_recessed_text(frame, "晚安", text_opacity))
    durations = [220, 240, 240, 640, 220]
    descriptions = [
        "半闭横眼、低亮核心，文字“晚安”开始出现。",
        "主体保持直立并缓慢下沉约 8 px，整体略微降亮。",
        "主体下沉到约 18 px，核心继续熄暗，文字基本可读。",
        "主体下沉约 26 px、横眼和暗灰青核心稳定，文字“晚安”停留。",
        "主体回到接近首帧的浅下沉状态后循环。",
    ]
    return frames, durations, descriptions


def checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    image = Image.new("RGB", size, (238, 242, 242))
    draw = ImageDraw.Draw(image)
    alt = (211, 220, 220)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=alt)
    return image


def composite_on(frame: Image.Image, color: tuple[int, int, int], size: int) -> Image.Image:
    background = Image.new("RGB", (size, size), color)
    preview = frame.resize((size, size), Image.Resampling.LANCZOS)
    background.paste(preview, mask=preview.getchannel("A"))
    return background


def make_contact_sheet(frames: list[Image.Image], durations: list[int], path: Path) -> None:
    tile, label_height = 360, 42
    rows = math.ceil(len(frames) / 3)
    sheet = Image.new("RGB", (tile * 3, (tile + label_height) * rows), "white")
    label_font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 22)
    for index, frame in enumerate(frames):
        x = (index % 3) * tile
        y = (index // 3) * (tile + label_height)
        bg = checkerboard((tile, tile))
        preview = frame.resize((tile, tile), Image.Resampling.LANCZOS)
        bg.paste(preview, mask=preview.getchannel("A"))
        sheet.paste(bg, (x, y))
        ImageDraw.Draw(sheet).text(
            (x + 12, y + tile + 8),
            f"F{index + 1}  {durations[index]} ms",
            font=label_font,
            fill=(20, 55, 53),
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def make_review_sheet(hold: Image.Image, path: Path) -> None:
    canvas = Image.new("RGB", (1080, 620), (245, 247, 247))
    draw = ImageDraw.Draw(canvas)
    label_font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 22)
    items = [
        ("240 light", composite_on(hold, (248, 248, 248), 240), (40, 60)),
        ("240 dark", composite_on(hold, (25, 31, 34), 240), (310, 60)),
        ("50 light actual", composite_on(hold, (248, 248, 248), 50), (655, 155)),
        ("50 dark actual", composite_on(hold, (25, 31, 34), 50), (875, 155)),
    ]
    for label, preview, position in items:
        canvas.paste(preview, position)
        draw.text((position[0], position[1] - 34), label, font=label_font, fill=(20, 55, 53))
    # Enlarged nearest-neighbour copies make the actual 50 px raster inspectable.
    for color, position, label in [
        ((248, 248, 248), (610, 300), "50 light x4"),
        ((25, 31, 34), (850, 300), "50 dark x4"),
    ]:
        small = composite_on(hold, color, 50).resize((200, 200), Image.Resampling.NEAREST)
        canvas.paste(small, position)
        draw.text((position[0], position[1] - 34), label, font=label_font, fill=(20, 55, 53))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def make_preview_gif(
    frame_dir: Path,
    durations: list[int],
    output: Path,
) -> None:
    manifest = output.with_suffix(".concat.txt")
    lines: list[str] = []
    paths = [frame_dir / f"{index:03d}.png" for index in range(len(durations))]
    for path, duration in zip(paths, durations):
        lines.append(f"file '{path.resolve()}'")
        lines.append(f"duration {duration / 1000:.3f}")
    # The concat demuxer applies the final duration only when the last frame is
    # repeated. This file is QA-only; the source of timing truth remains JSON.
    lines.append(f"file '{paths[-1].resolve()}'")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(manifest),
                "-filter_complex",
                "color=c=0xEEF2F2:s=512x512:r=20[bg];"
                "[0:v]fps=20,scale=512:512:flags=lanczos[fg];"
                "[bg][fg]overlay=shortest=1:format=auto,split[s0][s1];"
                "[s0]palettegen[p];[s1][p]paletteuse",
                str(output),
            ],
            check=True,
        )
    finally:
        manifest.unlink(missing_ok=True)


def alpha_metrics(frame: Image.Image) -> dict[str, object]:
    alpha = np.asarray(frame.getchannel("A"))
    ys, xs = np.where(alpha > 16)
    return {
        "size": list(frame.size),
        "mode": frame.mode,
        "alpha_bbox": [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)],
        "border_is_transparent": bool(
            np.all(alpha[0] == 0)
            and np.all(alpha[-1] == 0)
            and np.all(alpha[:, 0] == 0)
            and np.all(alpha[:, -1] == 0)
        ),
        "partial_alpha_pixels": int(np.count_nonzero((alpha > 0) & (alpha < 255))),
    }


def loop_endpoint_delta(first: Image.Image, last: Image.Image) -> float:
    a = np.asarray(first.convert("RGBA"), dtype=np.float32)
    b = np.asarray(last.convert("RGBA"), dtype=np.float32)
    mask = (a[..., 3] > 16) | (b[..., 3] > 16)
    if not np.any(mask):
        return 0.0
    return float(np.abs(a - b)[mask].mean())


def load_frame(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGBA")


def make_semantic_comparison() -> None:
    rows = [
        (
            "同意 vs 接收",
            [
                ("新包 S01 OK", OUTPUT / "s01-ok/source/frames/003.png"),
                ("首包 S01 收到", Path("projects/fangxin/packs/shangbanzhong/output/s01-shoudao/source/frames/004.png")),
            ],
        ),
        (
            "无语 vs 过热 / 装死",
            [
                ("新包 S03 无语", OUTPUT / "s03-wuyu/source/frames/003.png"),
                ("首包 S06 CPU 烧了", Path("projects/fangxin/packs/shangbanzhong/output/s06-cpushaole/source/frames/003.png")),
                ("首包 S07 已读装死", Path("projects/fangxin/packs/shangbanzhong/output/s07-yiduzhuangsi/source/frames/002.png")),
            ],
        ),
        (
            "鼓励对方 vs 自己完成",
            [
                ("新包 S07 加油", OUTPUT / "s07-jiayou/source/frames/003.png"),
                ("首包 S04 跑通了", Path("projects/fangxin/packs/shangbanzhong/output/s04-paotongle/source/frames/004.png")),
            ],
        ),
    ]
    if not all(path.exists() for _, items in rows for _, path in items):
        return
    tile = 250
    row_height = 330
    canvas = Image.new("RGB", (tile * 3, row_height * len(rows)), (246, 248, 248))
    title_font = font(30)
    label_font = font(24)
    for row_index, (title, items) in enumerate(rows):
        y0 = row_index * row_height
        ImageDraw.Draw(canvas).text((18, y0 + 12), title, font=title_font, fill=(20, 75, 71))
        for column, (label, path) in enumerate(items):
            x = column * tile
            preview = composite_on(load_frame(path), (248, 248, 248), 220)
            canvas.paste(preview, (x + 15, y0 + 58))
            draw = ImageDraw.Draw(canvas)
            label_box = draw.textbbox((0, 0), label, font=label_font)
            label_width = label_box[2] - label_box[0]
            draw.text(
                (x + (tile - label_width) / 2, y0 + 286),
                label,
                font=label_font,
                fill=(20, 75, 71),
            )
    PACK_QA.mkdir(parents=True, exist_ok=True)
    canvas.save(PACK_QA / "semantic-comparison.png")


def make_pack_contact_sheet() -> None:
    stickers = [
        ("S01 OK", "s01-ok"),
        ("S02 不行", "s02-buxing"),
        ("S03 无语", "s03-wuyu"),
        ("S04 笑死", "s04-xiaosi"),
        ("S05 谢谢", "s05-xiexie"),
        ("S06 没事", "s06-meishi"),
        ("S07 加油", "s07-jiayou"),
        ("S08 辛苦了", "s08-xinkule"),
        ("S09 厉害", "s09-lihai"),
        ("S10 抱歉", "s10-baoqian"),
        ("S11 真的假的", "s11-zhendejiade"),
        ("S12 晚安", "s12-wanan"),
    ]
    paths = [(label, OUTPUT / sticker_id / "source/frames/003.png") for label, sticker_id in stickers]
    if not all(path.exists() for _, path in paths):
        return
    tile, label_height, columns = 260, 48, 4
    rows = math.ceil(len(paths) / columns)
    canvas = Image.new("RGB", (tile * columns, (tile + label_height) * rows), (246, 248, 248))
    label_font = font(25)
    draw = ImageDraw.Draw(canvas)
    for index, (label, path) in enumerate(paths):
        x = (index % columns) * tile
        y = (index // columns) * (tile + label_height)
        preview = composite_on(load_frame(path), (248, 248, 248), 240)
        canvas.paste(preview, (x + 10, y + 4))
        label_box = draw.textbbox((0, 0), label, font=label_font)
        label_width = label_box[2] - label_box[0]
        draw.text(
            (x + (tile - label_width) / 2, y + tile + 6),
            label,
            font=label_font,
            fill=(20, 75, 71),
        )
    PACK_QA.mkdir(parents=True, exist_ok=True)
    canvas.save(PACK_QA / "pack-contact-sheet.png")


def write_package(
    sticker_id: str,
    prompt: str,
    frames: list[Image.Image],
    durations: list[int],
    descriptions: list[str],
    generation_plan: dict[str, object],
    semantic_hold_index: int = 3,
) -> None:
    output = OUTPUT / sticker_id
    frame_dir = output / "source" / "frames"
    qa = output / "qa"
    frame_dir.mkdir(parents=True, exist_ok=True)
    qa.mkdir(parents=True, exist_ok=True)
    for stale in frame_dir.glob("*.png"):
        stale.unlink()
    for index, frame in enumerate(frames):
        frame.save(frame_dir / f"{index:03d}.png")

    frames[0].save(
        output / "sticker.webp",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        lossless=False,
        quality=92,
        method=6,
        minimize_size=True,
        allow_mixed=True,
    )

    motion = {
        "id": sticker_id,
        "prompt": prompt,
        "reference_image": "projects/fangxin/identity/masters/fangxin-v6.png",
        "canvas": [CANVAS, CANVAS],
        "loop": True,
        "total_duration_ms": sum(durations),
        "identity_lock": IDENTITY_LOCK,
        "generation_plan": generation_plan,
        "semantic_hold_frame": f"frames/{semantic_hold_index:03d}.png",
        "frames": [
            {
                "file": f"frames/{index:03d}.png",
                "duration_ms": duration,
                "description": description,
            }
            for index, (duration, description) in enumerate(zip(durations, descriptions))
        ],
    }
    (output / "source" / "motion.json").write_text(
        json.dumps(motion, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics = [alpha_metrics(frame) for frame in frames]
    endpoint_delta = loop_endpoint_delta(frames[0], frames[-1])
    checks = {
        "frame_count_is_5": len(frames) == 5,
        "all_frames_1024_rgba": all(frame.mode == "RGBA" and frame.size == (CANVAS, CANVAS) for frame in frames),
        "all_borders_transparent": all(item["border_is_transparent"] for item in metrics),
        "duration_in_pack_range": 1200 <= sum(durations) <= 2000,
        "semantic_hold_at_least_500_ms": durations[semantic_hold_index] >= 500,
        "loop_endpoint_mean_rgba_delta_below_8": endpoint_delta < 8.0,
    }
    report = {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "frames": metrics,
        "loop_endpoint_mean_rgba_delta": round(endpoint_delta, 4),
        "visual_review": {"status": "pending"},
    }
    (qa / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    make_contact_sheet(frames, durations, qa / "contact-sheet.png")
    make_review_sheet(frames[semantic_hold_index], qa / "small-size-review.png")
    make_preview_gif(frame_dir, durations, qa / "preview.gif")


def build(selected: set[str]) -> None:
    neutral = normalize(ANCHORS / "neutral-rgba.png")
    half_eyes = normalize(ANCHORS / "half-eyes-rgba.png")
    happy_eyes = normalize(ANCHORS / "happy-eyes-rgba.png")
    focus_eyes = normalize(ANCHORS / "focus-eyes-rgba.png")
    forward = fit_subject(
        ANCHORS / "s07-jiayou-generated-v1-rgba.png",
        target_width=825,
        target_height=825,
        center_y=510,
    )

    if "s01" in selected:
        frames, durations, descriptions = s01_frames(neutral)
        write_package(
            "s01-ok",
            "绿色小勾从核心右下缘短促弹出，核心转绿，表达同意或许可。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/neutral-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["core tint", "core-docked check", "vertical squash and rebound", "timing"],
            },
        )
    if "s02" in selected:
        frames, durations, descriptions = s02_frames(half_eyes)
        write_package(
            "s02-buxing",
            "主体围绕底部中心完成一次左右拒绝摇摆，半闭横眼、珊瑚红核心和核心下方机身文字“NO”表达不接受。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/half-eyes-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["bottom-pivot rotation", "exact core tint", "recessed body text NO", "coral core pulse", "timing"],
            },
        )
    if "s03" in selected:
        frames, durations, descriptions = s03_frames(half_eyes)
        write_package(
            "s03-wuyu",
            "主体左上先主塌、左下稍后轻跟随，半闭横眼和低亮核心配合确定性文字“无语”。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/half-eyes-rgba.png",
                "generated_attempt": "work/anchors/rgba/s03-wuyu-generated-v2-rgba.png",
                "generated_attempt_status": "rejected_as_full_anchor",
                "rejection_reason": "核心比例漂移且形变不足以稳定区分困倦；只作轮廓方向参考",
                "deterministic": ["top-led asymmetric body warp", "dim cyan-gray core", "exact recessed text", "timing"],
            },
        )
    if "s04" in selected:
        frames, durations, descriptions = s04_frames(happy_eyes)
        write_package(
            "s04-xiaosi",
            "主体以放慢的左右反相柔软波浪抖动表达强烈好笑，实体开心眼随主体局部微晃，机身文字“hhh!”同步浮现。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/happy-eyes-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["slowed horizontal row wave", "synchronized eye micro wobble", "cyan core pulse", "exact recessed text", "slight settle stretch", "timing"],
            },
        )
    if "s05" in selected:
        frames, durations, descriptions = s05_frames(neutral)
        write_package(
            "s05-xiexie",
            "状态核心完成一次柔和扩亮，配合确定性文字“谢谢”表达感谢。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/neutral-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["core face expansion within 6 percent", "cyan core pulse", "exact recessed text", "timing"],
            },
        )
    if "s06" in selected:
        frames, durations, descriptions = s06_frames(neutral)
        write_package(
            "s06-meishi",
            "主体从轻微内缩平滑恢复稳定，配合青白核心和确定性文字“没事”表达安抚。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/neutral-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["uniform inward scale and recovery", "cyan core stabilization", "exact recessed text", "timing"],
            },
        )
    if "s07" in selected:
        frames, durations, descriptions = s07_frames(forward)
        write_package(
            "s07-jiayou",
            "前倾锚点蓄力压缩后向前上方推进，青白核心和确定性文字“加油”共同表达鼓励。",
            frames,
            durations,
            descriptions,
            {
                "pilot_anchor": "work/anchors/rgba/s07-jiayou-generated-v1-rgba.png",
                "pilot_anchor_source": "work/anchors/source-chroma/s07-jiayou-generated-v1.png",
                "pilot_anchor_status": "approved_for_pilot_after_visual_review",
                "deterministic": ["subject fit", "vertical squash and lift", "cyan core pulse", "exact recessed text", "timing"],
            },
        )
    if "s08" in selected:
        frames, durations, descriptions = s08_frames(neutral)
        write_package(
            "s08-xinkule",
            "主体保持底部稳定并缓慢前倾致意，配合确定性文字“辛苦了”认可对方投入。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/neutral-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["top-led forward bow warp", "cyan core dim", "exact recessed text", "timing"],
            },
        )
    if "s09" in selected:
        frames, durations, descriptions = s09_frames(neutral, half_eyes)
        write_package(
            "s09-lihai",
            "主体短促后仰，双眼从半闭前态睁回常态最大包围框，配合“厉害”表达赞赏。",
            frames,
            durations,
            descriptions,
            {
                "approved_bases": ["work/anchors/rgba/half-eyes-rgba.png", "work/anchors/rgba/neutral-rgba.png"],
                "new_generated_anchor": False,
                "deterministic": ["approved eye-anchor switch", "top-led recoil warp", "cyan core pulse", "exact recessed text", "timing"],
            },
        )
    if "s10" in selected:
        frames, durations, descriptions = s10_frames(neutral)
        write_package(
            "s10-baoqian",
            "主体克制地内收并轻微下沉，配合低亮核心和确定性文字“抱歉”主动修复关系。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/neutral-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["uniform inward scale", "downward translation", "dim cyan core", "exact recessed text", "timing"],
            },
        )
    if "s11" in selected:
        frames, durations, descriptions = s11_frames(focus_eyes)
        write_package(
            "s11-zhendejiade",
            "主体围绕底部中心缓慢向一侧倾斜审视，配合专注眼、黄色核心和“真的假的”。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/focus-eyes-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["single-direction bottom-pivot rotation", "yellow core pulse", "exact recessed text", "timing"],
            },
        )
    if "s12" in selected:
        frames, durations, descriptions = s12_frames(half_eyes)
        write_package(
            "s12-wanan",
            "主体保持直立并缓慢下沉、降亮，横眼和参照 S10 明显加深的暗灰青核心配合“晚安”完成聊天收尾。",
            frames,
            durations,
            descriptions,
            {
                "approved_base": "work/anchors/rgba/half-eyes-rgba.png",
                "new_generated_anchor": False,
                "deterministic": ["vertical translation", "global dimming", "strengthened dim cyan core", "exact recessed text", "timing"],
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        default="s01,s02,s03,s04,s05,s06,s07,s08,s09,s10,s11,s12",
        help="Comma-separated stickers: s01 through s12",
    )
    args = parser.parse_args()
    selected = {item.strip() for item in args.only.split(",") if item.strip()}
    valid = {f"s{index:02d}" for index in range(1, 13)}
    unknown = selected - valid
    if unknown:
        raise ValueError(f"unknown pilot(s): {', '.join(sorted(unknown))}")
    build(selected)
    make_semantic_comparison()
    make_pack_contact_sheet()


if __name__ == "__main__":
    main()
