#!/usr/bin/env python3
"""Build deterministic S04-S07 animated-sticker packages from approved anchors."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from build_s02_s03 import (
    CANVAS,
    CORE_BOX,
    draw_recessed_run,
    font,
    motion_plan,
    normalize,
    package,
    write_working_set,
)


GREEN = (116, 242, 106)
YELLOW = (255, 210, 74)
RED = (255, 92, 87)
CYAN_WHITE = (231, 255, 251)


def alpha_crop(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("image has no visible pixels")
    return image.crop(bbox)


def transform_subject(
    image: Image.Image,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    dx: int = 0,
    dy: int = 0,
    anchor_bottom: bool = True,
) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return image.copy()
    crop = image.crop(bbox)
    size = (
        max(1, round(crop.width * scale_x)),
        max(1, round(crop.height * scale_y)),
    )
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    x = round((CANVAS - crop.width) / 2) + dx
    y = (bbox[3] - crop.height if anchor_bottom else round((CANVAS - crop.height) / 2)) + dy
    canvas = Image.new("RGBA", image.size)
    canvas.alpha_composite(crop, (x, y))
    return canvas


def detect_core_box(image: Image.Image) -> tuple[int, int, int, int]:
    rgb = np.asarray(image.convert("RGB"))
    alpha = np.asarray(image.getchannel("A"))
    visible_y, _ = np.where(alpha > 16)
    if not visible_y.size:
        return CORE_BOX
    body_top = int(visible_y.min())
    body_bottom = int(visible_y.max()) + 1
    body_height = body_bottom - body_top
    # The core is the centered, near-square bright component. Derive its
    # vertical search band from the subject bbox so this also works for a
    # flattened pose whose core sits much lower than on the neutral anchor.
    y0 = round(body_top + body_height * 0.28)
    y1 = round(body_top + body_height * 0.68)
    x0, x1 = round(CANVAS * 0.39), round(CANVAS * 0.61)
    roi = rgb[y0:y1, x0:x1]
    roi_alpha = alpha[y0:y1, x0:x1]
    bright = (roi.min(axis=2) > 178) & (roi_alpha > 16)
    ys, xs = np.where(bright)
    if not xs.size:
        return CORE_BOX
    candidate = (
        int(xs.min() + x0),
        int(ys.min() + y0),
        int(xs.max() + x0 + 1),
        int(ys.max() + y0 + 1),
    )
    width = candidate[2] - candidate[0]
    height = candidate[3] - candidate[1]
    if not (20 <= width <= 220 and 20 <= height <= 220 and 0.5 <= width / height <= 2.0):
        return CORE_BOX
    if body_height >= 840 and width <= 135:
        # Neutral, happy, and half-eye anchors share the approved master
        # geometry. Their asymmetric 3D highlight biases a luminance bbox
        # down and right, so use the locked core face instead.
        return CORE_BOX
    if width > 135 or height > 135:
        # Generated deformation anchors may spread the highlight beyond the
        # physical face. Preserve their local center but cap the colored face
        # to the approved core dimensions.
        center_x = (candidate[0] + candidate[2]) / 2
        center_y = (candidate[1] + candidate[3]) / 2
        target_width = min(width, CORE_BOX[2] - CORE_BOX[0])
        target_height = min(height, CORE_BOX[3] - CORE_BOX[1])
        return (
            round(center_x - target_width / 2),
            round(center_y - target_height / 2),
            round(center_x + target_width / 2),
            round(center_y + target_height / 2),
        )
    return candidate


def set_core_state(
    image: Image.Image,
    color: tuple[int, int, int],
    level: float,
    dark: bool = False,
    face_shift_y: int = 0,
    face_top_trim: int = 0,
) -> Image.Image:
    level = max(0.0, min(1.0, level))
    box = detect_core_box(image)
    overlay = Image.new("RGBA", image.size)
    draw = ImageDraw.Draw(overlay)
    if dark:
        radius = max(14, round(min(box[2] - box[0], box[3] - box[1]) * 0.22))
        draw.rounded_rectangle(
            box,
            radius=radius,
            fill=(5, 66, 68, round(150 + 70 * (1.0 - level))),
        )
        result = Image.alpha_composite(image, overlay)
        shadow_glow = Image.new("RGBA", image.size)
        ImageDraw.Draw(shadow_glow).rounded_rectangle(
            box,
            radius=radius,
            fill=(5, 66, 68, 14),
        )
        return Image.alpha_composite(result, shadow_glow.filter(ImageFilter.GaussianBlur(5)))

    inset = max(6, round(min(box[2] - box[0], box[3] - box[1]) * 0.065))
    face_box = (
        box[0] + inset,
        box[1] + inset + face_shift_y + face_top_trim,
        box[2] - inset,
        box[3] - inset + face_shift_y,
    )
    radius = max(12, round(min(face_box[2] - face_box[0], face_box[3] - face_box[1]) * 0.22))
    draw.rounded_rectangle(
        face_box,
        radius=radius,
        fill=(*color, round(72 + 88 * level)),
    )
    result = Image.alpha_composite(image, overlay)
    glow = Image.new("RGBA", image.size)
    ImageDraw.Draw(glow).rounded_rectangle(
        face_box,
        radius=radius,
        fill=(*color, round(8 + 18 * level)),
    )
    return Image.alpha_composite(result, glow.filter(ImageFilter.GaussianBlur(9)))


def add_done_text(image: Image.Image, opacity: float) -> Image.Image:
    layer = Image.new("RGBA", image.size)
    text_font = font(80)
    word = "DONE"
    core_center_x = (CORE_BOX[0] + CORE_BOX[2]) / 2
    word_width = ImageDraw.Draw(layer).textlength(word, font=text_font)
    glyph_bbox = text_font.getbbox(word)
    lower_region_center_y = (CORE_BOX[3] + 952) / 2
    glyph_center_offset_y = (glyph_bbox[1] + glyph_bbox[3]) / 2
    draw_recessed_run(
        layer,
        word,
        (core_center_x - word_width / 2, lower_region_center_y - glyph_center_offset_y),
        text_font,
        opacity,
    )
    return Image.alpha_composite(image, layer)


def s04_frames(neutral: Image.Image, happy: Image.Image) -> list[Image.Image]:
    frame_0 = neutral.copy()
    frame_1 = transform_subject(set_core_state(neutral, GREEN, 0.55, face_top_trim=10), scale_y=0.97)
    frame_2 = transform_subject(
        add_done_text(set_core_state(happy, GREEN, 0.78, face_top_trim=10), 0.40),
        scale_y=0.99,
        dy=-10,
    )
    frame_3 = transform_subject(
        add_done_text(set_core_state(happy, GREEN, 1.00, face_top_trim=10), 1.00),
        dy=-28,
    )
    frame_4 = add_done_text(set_core_state(happy, GREEN, 0.90, face_top_trim=10), 1.00)
    frame_5 = add_done_text(set_core_state(neutral, CYAN_WHITE, 0.20), 0.18)
    return [frame_0, frame_1, frame_2, frame_3, frame_4, frame_5]


def rails_layers() -> tuple[Image.Image, Image.Image]:
    behind = Image.new("RGBA", (CANVAS, CANVAS))
    front = Image.new("RGBA", (CANVAS, CANVAS))
    behind_draw = ImageDraw.Draw(behind)
    front_draw = ImageDraw.Draw(front)
    for x0, x1 in ((88, 130), (894, 936)):
        behind_draw.rounded_rectangle(
            (x0, 390, x1, 690),
            radius=20,
            fill=(45, 58, 62, 220),
            outline=(132, 157, 160, 210),
            width=4,
        )
        behind_draw.rounded_rectangle(
            (x0 + 8, 405, x0 + 15, 675),
            radius=4,
            fill=(205, 225, 225, 75),
        )
    front_draw.rounded_rectangle(
        (108, 492, 144, 606),
        radius=16,
        fill=(58, 70, 73, 238),
        outline=(160, 184, 184, 205),
        width=3,
    )
    front_draw.rounded_rectangle(
        (880, 492, 916, 606),
        radius=16,
        fill=(58, 70, 73, 238),
        outline=(160, 184, 184, 205),
        width=3,
    )
    return behind, front


def compose_rails(body: Image.Image) -> Image.Image:
    behind, front = rails_layers()
    return Image.alpha_composite(Image.alpha_composite(behind, body), front)


def s05_frames(anchor: Image.Image) -> list[Image.Image]:
    specs = [
        (0, 0.35),
        (-18, 1.00),
        (0, 0.05),
        (18, 0.92),
        (0, 0.55),
    ]
    frames = []
    for dx, level in specs:
        body = set_core_state(anchor, YELLOW, level, face_shift_y=-12)
        body = transform_subject(body, dx=dx)
        frames.append(compose_rails(body))
    return frames


def add_smoke(image: Image.Image, progress: float, opacity: float) -> Image.Image:
    if progress <= 0 or opacity <= 0:
        return image.copy()
    # A single centered smoke plume made from three translucent wisps. Their
    # roots overlap the top silhouette, while the separated upper curves keep
    # the result airy instead of forming an opaque blob.
    specs = [
        (512, 18, 2.5, 0.0, 112, 20, 9),
        (488, 14, 2.2, 0.5, 110, 28, 7),
        (536, 14, 2.4, -0.45, 114, 26, 7),
    ]
    paths: list[tuple[list[tuple[int, int]], int, int]] = []
    for center_x, amplitude, cycles, phase, start_y, end_y, width in specs:
        full_path = []
        for index in range(51):
            t = index / 50
            x = center_x + amplitude * math.sin(cycles * math.pi * t + phase)
            y = start_y + (end_y - start_y) * t
            full_path.append((round(x), round(y)))
        count = max(2, min(len(full_path), round(len(full_path) * progress)))
        paths.append((full_path[:count], width, len(full_path)))

    inner_mask = Image.new("L", image.size)
    inner_draw = ImageDraw.Draw(inner_mask)
    for path, base_width, full_count in paths:
        for index in range(len(path) - 1):
            t = index / (full_count - 1)
            width = max(1, round(base_width * (1.0 - 0.55 * t)))
            alpha = round(135 * opacity * (1.0 - 0.55 * t))
            inner_draw.line(path[index : index + 2], fill=alpha, width=width)
    inner_mask = inner_mask.filter(ImageFilter.GaussianBlur(3))

    smoke = Image.new("RGBA", image.size)
    smoke.paste((102, 114, 118, 170), (0, 0, CANVAS, CANVAS), inner_mask)
    return Image.alpha_composite(image, smoke)


def s06_frames(anchor: Image.Image) -> list[Image.Image]:
    frame_0 = set_core_state(anchor, CYAN_WHITE, 0.25)
    frame_1 = transform_subject(
        set_core_state(anchor, YELLOW, 0.72, face_top_trim=10),
        scale_x=1.02,
        scale_y=1.02,
    )
    frame_2 = add_smoke(
        transform_subject(
            set_core_state(anchor, RED, 1.00, face_top_trim=10),
            scale_x=1.025,
            scale_y=1.025,
        ),
        0.45,
        0.82,
    )
    frame_3 = add_smoke(
        transform_subject(
            set_core_state(anchor, RED, 0.82, face_top_trim=10),
            scale_x=1.01,
            scale_y=1.01,
        ),
        1.00,
        1.00,
    )
    frame_4 = add_smoke(set_core_state(anchor, CYAN_WHITE, 0.12), 1.00, 0.22)
    return [frame_0, frame_1, frame_2, frame_3, frame_4]


def dim_inactive(image: Image.Image, brightness: float = 0.84) -> Image.Image:
    dimmed = ImageEnhance.Brightness(image).enhance(brightness)
    return ImageEnhance.Color(dimmed).enhance(0.88)


def closed_eye_component(
    source: Image.Image,
    target: tuple[int, int, int, int],
) -> Image.Image:
    crop_box = (
        max(0, target[0] - 3),
        max(0, target[1] - 3),
        min(CANVAS, target[2] + 3),
        min(CANVAS, target[3] + 3),
    )
    crop = source.crop(crop_box).convert("RGBA")
    crop_rgb = np.asarray(crop.convert("RGB"), dtype=np.float32)
    crop_alpha = np.asarray(crop.getchannel("A"), dtype=np.float32) / 255.0
    crop_luma = 0.2126 * crop_rgb[..., 0] + 0.7152 * crop_rgb[..., 1] + 0.0722 * crop_rgb[..., 2]
    component_alpha = np.clip((145.0 - crop_luma) / 70.0, 0.0, 1.0) * crop_alpha
    output = np.asarray(crop).copy()
    output[..., 3] = np.rint(component_alpha * 255.0).astype(np.uint8)
    output[output[..., 3] == 0, :3] = 0
    return alpha_crop(Image.fromarray(output, "RGBA"))


def detect_viewer_right_eye(image: Image.Image) -> tuple[int, int, int, int]:
    rgb = np.asarray(image.convert("RGB"))
    alpha = np.asarray(image.getchannel("A"))
    x0, x1 = round(CANVAS * 0.58), round(CANVAS * 0.86)
    y0, y1 = round(CANVAS * 0.38), round(CANVAS * 0.78)
    roi = rgb[y0:y1, x0:x1]
    roi_alpha = alpha[y0:y1, x0:x1]
    luma = 0.2126 * roi[..., 0] + 0.7152 * roi[..., 1] + 0.0722 * roi[..., 2]
    dark = (luma < 105) & (roi_alpha > 16)
    ys, xs = np.where(dark)
    if not xs.size:
        raise ValueError("could not locate viewer-right closed eye")
    return (
        int(xs.min() + x0),
        int(ys.min() + y0),
        int(xs.max() + x0 + 1),
        int(ys.max() + y0 + 1),
    )


def clear_closed_eye(
    image: Image.Image,
    target: tuple[int, int, int, int],
) -> Image.Image:
    pad_x = 14
    pad_y = 20
    x0 = max(1, target[0] - pad_x)
    y0 = max(1, target[1] - pad_y)
    x1 = min(CANVAS - 1, target[2] + pad_x)
    y1 = min(CANVAS - 1, target[3] + pad_y)

    source = np.asarray(image).astype(np.float32)
    patch = np.empty((y1 - y0, x1 - x0, 4), dtype=np.float32)
    top = source[y0 - 1, x0:x1]
    bottom = source[y1, x0:x1]
    for row in range(patch.shape[0]):
        weight = (row + 1) / (patch.shape[0] + 1)
        patch[row] = top * (1.0 - weight) + bottom * weight
    patch_image = Image.fromarray(np.rint(patch).astype(np.uint8), "RGBA")

    mask = Image.new("L", image.size)
    ImageDraw.Draw(mask).rounded_rectangle((x0, y0, x1, y1), radius=12, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(4))
    replacement = image.copy()
    replacement.alpha_composite(patch_image, (x0, y0))
    return Image.composite(replacement, image, mask)


def resize_peek_eye(closed: Image.Image, openness: float) -> Image.Image:
    target = detect_viewer_right_eye(closed)
    component = closed_eye_component(closed, target)
    target_width = target[2] - target[0]
    target_closed_height = target[3] - target[1]
    # Antialiased source pixels occupy about 75% of this resized component;
    # 42 px yields a visible dark eye body of about 32 px, half the neutral eye.
    max_open_height = 42
    open_height = round(target_closed_height + (max_open_height - target_closed_height) * openness)
    component = component.resize(
        (target_width, max(1, open_height)),
        Image.Resampling.LANCZOS,
    )

    highlight = Image.new("RGBA", component.size)
    highlight_draw = ImageDraw.Draw(highlight)
    radius = max(2, round(open_height * (0.08 + 0.07 * openness)))
    center = (round(component.width * 0.82), round(component.height * 0.34))
    highlight_draw.ellipse(
        (center[0] - radius - 2, center[1] - radius - 2, center[0] + radius + 2, center[1] + radius + 2),
        fill=(193, 255, 250, round(45 + 55 * openness)),
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(2))
    highlight_draw = ImageDraw.Draw(highlight)
    highlight_draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=(255, 255, 255, round(190 + 65 * openness)),
    )
    component = Image.alpha_composite(component, highlight)
    x = round((target[0] + target[2] - component.width) / 2)
    y = round((target[1] + target[3] - component.height) / 2)
    result = clear_closed_eye(closed, target)
    result.alpha_composite(component, (x, y))
    return result


def s07_frames(closed_anchor: Image.Image) -> list[Image.Image]:
    base = dim_inactive(closed_anchor)
    frame_0 = set_core_state(base, CYAN_WHITE, 0.06, dark=True)
    frame_1 = resize_peek_eye(set_core_state(base, CYAN_WHITE, 0.07, dark=True), 0.42)
    frame_2 = resize_peek_eye(set_core_state(base, CYAN_WHITE, 0.08, dark=True), 1.00)
    frame_3 = set_core_state(dim_inactive(closed_anchor, 0.82), CYAN_WHITE, 0.055, dark=True)
    frame_4 = set_core_state(dim_inactive(closed_anchor, 0.81), CYAN_WHITE, 0.045, dark=True)
    return [frame_0, frame_1, frame_2, frame_3, frame_4]


def build_one(
    args: argparse.Namespace,
    sticker_id: str,
    prompt: str,
    anchor_paths: list[Path],
    frames: list[Image.Image],
    durations: list[int],
    descriptions: list[str],
    deterministic: list[str],
) -> None:
    motion = motion_plan(
        sticker_id,
        prompt,
        anchor_paths,
        durations,
        descriptions,
        deterministic,
    )
    frame_dir, motion_path = write_working_set(
        args.work_root / sticker_id,
        frames,
        motion,
    )
    package(
        args.skill_dir / "scripts" / "package_sticker.py",
        frame_dir,
        motion_path,
        args.output_root / sticker_id,
    )


def build(args: argparse.Namespace) -> None:
    allowed = {"s04", "s05", "s06", "s07"}
    selected = {item.strip() for item in args.only.split(",") if item.strip()} if args.only else allowed
    unknown = selected - allowed
    if unknown:
        raise ValueError(f"unknown scene key(s): {', '.join(sorted(unknown))}")

    if "s04" in selected:
        neutral = normalize(args.neutral_anchor)
        happy = normalize(args.happy_anchor)
        build_one(
        args,
        "s04-paotongle",
        "核心转绿，机身整体渐现 DONE，双眼变成实体 ^ ^ 并短促轻弹后循环。",
        [args.neutral_anchor, args.happy_anchor],
        s04_frames(neutral, happy),
        [160, 120, 160, 160, 560, 160],
        [
            "常态方眼、青白核心、无文字。",
            "核心转绿，主体向下压缩约 3%。",
            "双眼变成实体 ^ ^，主体开始回弹，DONE 整体以 40% 不透明度出现。",
            "主体向上轻弹，绿色核心和 DONE 完全可读。",
            "主体回到基线，保持绿色核心、DONE 和 ^ ^ 眼并停留。",
            "DONE 整体淡出，核心和方眼回到常态后循环。",
        ],
        ["green core tint", "whole-word DONE opacity", "vertical squash and bounce", "anchor switch", "timing"],
        )

    if "s05" in selected:
        s05 = normalize(args.s05_anchor)
        build_one(
        args,
        "s05-kazhule",
        "主体被左右两段短夹轨卡住，以 > < 眼小幅左右挣扎，黄色核心断续脉冲并循环。",
        [args.s05_anchor],
        s05_frames(s05),
        [180, 180, 140, 180, 560],
        [
            "主体卡在短夹轨中线，黄色核心低亮。",
            "主体向左挣扎，黄色核心提亮。",
            "主体回到中线，核心短暂接近熄灭。",
            "主体向右挣扎，黄色核心重新亮起。",
            "主体回到中线，保持被卡状态并停留后循环。",
        ],
        ["short clamp rails", "horizontal translation", "yellow pulse", "timing"],
        )

    if "s06" in selected:
        half_eyes = normalize(args.half_eye_anchor)
        build_one(
        args,
        "s06-cpushaole",
        "半闭疲惫眼，主体轻微鼓胀，核心由青白转黄再转红，顶部一缕烟出现后淡出并循环。",
        [args.half_eye_anchor],
        s06_frames(half_eyes),
        [180, 180, 180, 560, 180],
        [
            "半闭疲惫眼，核心青白，主体稳定。",
            "主体轻微鼓胀，核心转黄。",
            "核心转红并提亮，头顶正中开始出现一组烟丝。",
            "正中的单组烟柱展开为三条轻烟丝，根部压入头顶，红色核心停留。",
            "烟与红色核心淡回常态后循环。",
        ],
        ["uniform scale", "yellow and red core tint", "centered multi-wisp smoke plume", "opacity", "timing"],
        )

    if "s07" in selected:
        s07_closed = normalize(args.s07_closed_anchor)
        build_one(
        args,
        "s07-yiduzhuangsi",
        "主体始终趴平装死，核心近乎熄灭，只有画面右眼短暂睁缝偷看后重新闭合并循环。",
        [args.s07_closed_anchor],
        s07_frames(s07_closed),
        [220, 140, 560, 160, 400],
        [
            "主体趴平，双横线眼，核心近乎熄灭。",
            "画面右眼出现极窄缝和微弱高光。",
            "画面右眼直接纵向变形到常态方眼高度约 50%，停留偷看语义。",
            "画面右眼重新闭合。",
            "保持趴平装死状态，核心维持最弱信号后循环。",
        ],
        ["closed-eye pixel replacement", "single-eye vertical resize", "highlight scaling", "global dimming", "dark core", "timing"],
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--neutral-anchor", type=Path, default=Path("projects/fangxin/packs/shangbanzhong/work/v6-neutral-rgba.png"))
    parser.add_argument("--happy-anchor", type=Path, default=Path("projects/fangxin/packs/shangbanzhong/work/v6-happy-rgba.png"))
    parser.add_argument("--half-eye-anchor", type=Path, default=Path("projects/fangxin/packs/shangbanzhong/work/s02-working-eyes-rgba.png"))
    parser.add_argument("--s05-anchor", type=Path, default=Path("projects/fangxin/packs/shangbanzhong/work/s05-stuck-anchor-rgba.png"))
    parser.add_argument("--s07-closed-anchor", type=Path, default=Path("projects/fangxin/packs/shangbanzhong/work/s07-flat-closed-rgba.png"))
    parser.add_argument("--work-root", type=Path, default=Path("projects/fangxin/packs/shangbanzhong/work/animation-builds"))
    parser.add_argument("--output-root", type=Path, default=Path("projects/fangxin/packs/shangbanzhong/output"))
    parser.add_argument("--skill-dir", type=Path, default=Path(".agents/skills/animated-sticker-maker"))
    parser.add_argument(
        "--only",
        help="Comma-separated scene keys to rebuild: s04,s05,s06,s07 (default: all).",
    )
    build(parser.parse_args())


if __name__ == "__main__":
    main()
