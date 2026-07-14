#!/usr/bin/env python3
"""Build the deterministic S02 and S03 animated-sticker packages."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CANVAS = 1024
CORE_BOX = (458, 473, 578, 597)
FONT_PATH = Path.home() / "Library/Fonts/Sarasa-SuperTTC.ttc"
FONT_INDEX = 301  # Sarasa Mono SC SemiBold in the local SuperTTC.

IDENTITY_LOCK = {
    "subject": "Voxel Max 2.5D turquoise rounded-square AI mascot",
    "fixed": [
        "right-top inward notch",
        "turquoise body palette and soft 2.5D material",
        "front-facing rounded-square silhouette",
        "centered cyan-white rounded-square status core",
        "dark glossy physical eye modules and symmetric spacing",
    ],
    "flexible": ["eye shape", "core brightness", "small body translation", "one support signal"],
    "forbidden": [
        "limbs or mouth",
        "body hue drift",
        "missing or inverted notch",
        "text generated inside the anchor",
        "extra UI or props",
    ],
}


def normalize(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").resize(
        (CANVAS, CANVAS), Image.Resampling.LANCZOS
    )


def font(size: int) -> ImageFont.FreeTypeFont:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Required project font not found: {FONT_PATH}")
    return ImageFont.truetype(str(FONT_PATH), size, index=FONT_INDEX)


def core_pulse(image: Image.Image, level: float) -> Image.Image:
    level = max(0.0, min(1.0, level))
    result = image.copy()
    if level < 0.5:
        veil = Image.new("RGBA", result.size)
        ImageDraw.Draw(veil).rounded_rectangle(
            (451, 466, 585, 604),
            radius=28,
            fill=(4, 92, 96, round((0.5 - level) * 42)),
        )
        result = Image.alpha_composite(result, veil.filter(ImageFilter.GaussianBlur(8)))

    glow = Image.new("RGBA", result.size)
    ImageDraw.Draw(glow).rounded_rectangle(
        CORE_BOX,
        radius=25,
        fill=(229, 255, 252, round(12 + 50 * level)),
    )
    result = Image.alpha_composite(result, glow.filter(ImageFilter.GaussianBlur(18)))
    return Image.alpha_composite(result, glow)


def translate(image: Image.Image, dy: int) -> Image.Image:
    result = Image.new("RGBA", image.size)
    result.alpha_composite(image, (0, dy))
    return result


def draw_recessed_run(
    layer: Image.Image,
    text: str,
    xy: tuple[float, float],
    text_font: ImageFont.FreeTypeFont,
    opacity: float,
) -> None:
    if not text or opacity <= 0:
        return
    draw = ImageDraw.Draw(layer)

    def alpha(value: int) -> int:
        return round(value * opacity)

    draw.text((xy[0] - 1, xy[1] - 1), text, font=text_font, fill=(4, 73, 70, alpha(115)))
    draw.text((xy[0], xy[1] + 2), text, font=text_font, fill=(137, 241, 232, alpha(45)))
    draw.text(xy, text, font=text_font, fill=(15, 110, 103, alpha(235)))


def add_working_text(image: Image.Image, dot_opacities: tuple[float, float, float]) -> Image.Image:
    layer = Image.new("RGBA", image.size)
    text_font = font(68)
    base = "WORKING"
    core_center_x = (CORE_BOX[0] + CORE_BOX[2]) / 2
    base_width = ImageDraw.Draw(layer).textlength(base, font=text_font)
    x = core_center_x - base_width / 2
    # Center the visible glyphs between the core's lower edge and the body's baseline.
    glyph_bbox = text_font.getbbox(base)
    lower_region_center_y = (CORE_BOX[3] + 952) / 2
    glyph_center_offset_y = (glyph_bbox[1] + glyph_bbox[3]) / 2
    y = lower_region_center_y - glyph_center_offset_y
    draw_recessed_run(layer, base, (x, y), text_font, 1.0)
    dot_width = ImageDraw.Draw(layer).textlength(".", font=text_font)
    dot_x = x + ImageDraw.Draw(layer).textlength(base, font=text_font)
    for index, opacity in enumerate(dot_opacities):
        draw_recessed_run(layer, ".", (dot_x + dot_width * index, y), text_font, opacity)
    return Image.alpha_composite(image, layer)


def add_thought_squares(
    image: Image.Image,
    opacities: tuple[float, float, float],
) -> Image.Image:
    layer = Image.new("RGBA", image.size)
    # Enlarge the ascending squares by about 15% while preserving their edge gaps.
    positions = [(774, 164, 35), (824, 113, 28), (870, 70, 21)]
    for (cx, cy, size), opacity in zip(positions, opacities):
        if opacity <= 0:
            continue
        glow = Image.new("RGBA", image.size)
        glow_draw = ImageDraw.Draw(glow)
        half = size // 2
        glow_draw.rounded_rectangle(
            (cx - half, cy - half, cx + half, cy + half),
            radius=max(3, size // 5),
            fill=(205, 255, 249, round(65 * opacity)),
        )
        layer = Image.alpha_composite(layer, glow.filter(ImageFilter.GaussianBlur(8)))
        draw = ImageDraw.Draw(layer)
        draw.rounded_rectangle(
            (cx - half + 2, cy - half + 3, cx + half + 2, cy + half + 3),
            radius=max(3, size // 5),
            fill=(8, 82, 79, round(105 * opacity)),
        )
        draw.rounded_rectangle(
            (cx - half, cy - half, cx + half, cy + half),
            radius=max(3, size // 5),
            fill=(111, 238, 225, round(245 * opacity)),
            outline=(220, 255, 251, round(220 * opacity)),
            width=max(1, size // 9),
        )
    return Image.alpha_composite(image, layer)


def s02_frames(anchor: Image.Image) -> list[Image.Image]:
    specs = [
        (0.15, (0.0, 0.0, 0.0), 0),
        (0.35, (1.0, 0.0, 0.0), 16),
        (0.60, (0.45, 1.0, 0.0), 8),
        (1.00, (0.30, 0.55, 1.0), 0),
        (0.72, (1.0, 1.0, 1.0), 0),
    ]
    frames = []
    for core_level, dots, dy in specs:
        frame = core_pulse(anchor, core_level)
        frame = add_working_text(frame, dots)
        frames.append(translate(frame, dy))
    return frames


def s02_square_to_squint_frames(
    neutral_anchor: Image.Image,
    squint_anchor: Image.Image,
) -> list[Image.Image]:
    specs = [
        (neutral_anchor, 0.15, (0.0, 0.0, 0.0), 0),
        (neutral_anchor, 0.35, (1.0, 0.0, 0.0), 16),
        (neutral_anchor, 0.60, (0.45, 1.0, 0.0), 8),
        (squint_anchor, 1.00, (0.30, 0.55, 1.0), 0),
        (squint_anchor, 0.72, (1.0, 1.0, 1.0), 0),
    ]
    frames = []
    for anchor, core_level, dots, dy in specs:
        frame = core_pulse(anchor, core_level)
        frame = add_working_text(frame, dots)
        frames.append(translate(frame, dy))
    return frames


def s03_frames(anchor: Image.Image) -> list[Image.Image]:
    specs = [
        (0.15, (0.0, 0.0, 0.0)),
        (0.32, (1.0, 0.0, 0.0)),
        (0.58, (1.0, 1.0, 0.0)),
        (1.00, (1.0, 1.0, 1.0)),
        (0.18, (0.22, 0.22, 0.22)),
    ]
    return [add_thought_squares(core_pulse(anchor, level), dots) for level, dots in specs]


def motion_plan(
    sticker_id: str,
    prompt: str,
    anchor_paths: list[Path],
    durations: list[int],
    descriptions: list[str],
    deterministic: list[str],
) -> dict[str, object]:
    return {
        "id": sticker_id,
        "prompt": prompt,
        "reference_image": "projects/fangxin/identity/masters/fangxin-v6.png",
        "canvas": [CANVAS, CANVAS],
        "loop": True,
        "identity_lock": IDENTITY_LOCK,
        "generation_plan": {
            "anchors": [str(anchor_path) for anchor_path in anchor_paths],
            "deterministic": deterministic,
        },
        "transparency": {"strategy": "chroma-key", "work_color": "#FF00FF"},
        "frames": [
            {
                "file": f"frames/{index:03d}.png",
                "duration_ms": duration,
                "description": description,
            }
            for index, (duration, description) in enumerate(zip(durations, descriptions))
        ],
    }


def write_working_set(
    root: Path,
    frames: list[Image.Image],
    motion: dict[str, object],
) -> tuple[Path, Path]:
    frame_dir = root / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for stale in frame_dir.glob("*.png"):
        stale.unlink()
    motion_path = root / "motion.json"
    motion_path.write_text(json.dumps(motion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for index, frame in enumerate(frames):
        frame.save(frame_dir / f"{index:03d}.png")
    return frame_dir, motion_path


def package(
    package_script: Path,
    frame_dir: Path,
    motion_path: Path,
    output: Path,
) -> None:
    subprocess.run(
        [
            sys.executable,
            str(package_script),
            "--frames-dir",
            str(frame_dir),
            "--motion",
            str(motion_path),
            "--output",
            str(output),
        ],
        check=True,
    )


def build(args: argparse.Namespace) -> None:
    package_script = args.skill_dir / "scripts" / "package_sticker.py"

    s02_durations = [180, 160, 160, 180, 560]
    s02_descriptions = [
        "半闭横眼，核心低亮，机身显示 WORKING，无句点。",
        "第一个句点点亮，主体轻微下沉，核心开始提亮。",
        "第二个句点点亮，主体回弹一半，核心继续提亮。",
        "第三个句点点亮，主体回到基线，核心达到最高亮度。",
        "WORKING... 完整停留，核心略微回落后循环。",
    ]
    s02_anchor = normalize(args.s02_anchor)
    s02_motion = motion_plan(
        "s02-biecui",
        "半闭横眼，核心缓慢脉冲，机身显示 WORKING，三个句点依次点亮并循环。",
        [args.s02_anchor],
        s02_durations,
        s02_descriptions,
        ["exact WORKING text", "sequential period opacity", "core pulse", "vertical translation", "timing"],
    )
    s02_work = args.work_root / "s02-biecui"
    s02_frames_dir, s02_motion_path = write_working_set(
        s02_work, s02_frames(s02_anchor), s02_motion
    )
    package(package_script, s02_frames_dir, s02_motion_path, args.output_root / "s02-biecui")

    s02_alt_descriptions = [
        "常态方眼，核心低亮，机身显示 WORKING，无句点。",
        "保持方眼，第一个句点点亮，主体轻微下沉。",
        "保持方眼，第二个句点点亮，主体回弹一半。",
        "主体回到基线，双眼眯成半闭横眼，第三个句点点亮。",
        "半闭横眼与 WORKING... 完整停留，然后循环回方眼。",
    ]
    neutral_anchor = normalize(args.neutral_anchor)
    s02_alt_motion = motion_plan(
        "s02-biecui-square-to-squint",
        "眼睛先保持常态方形；主体完成一次轻微下沉回弹后眯成半闭横眼，WORKING 三个句点依次点亮并循环。",
        [args.neutral_anchor, args.s02_anchor],
        s02_durations,
        s02_alt_descriptions,
        ["anchor switch after recovery", "exact WORKING text", "sequential period opacity", "core pulse", "vertical translation", "timing"],
    )
    s02_alt_work = args.work_root / "s02-biecui-square-to-squint"
    s02_alt_frames_dir, s02_alt_motion_path = write_working_set(
        s02_alt_work,
        s02_square_to_squint_frames(neutral_anchor, s02_anchor),
        s02_alt_motion,
    )
    package(
        package_script,
        s02_alt_frames_dir,
        s02_alt_motion_path,
        args.output_root / "s02-biecui-square-to-squint",
    )

    s03_durations = [180, 160, 180, 560, 180]
    s03_descriptions = [
        "专注眼，核心低亮，右上没有思考点。",
        "最靠近缺角的第一个方形思考点出现。",
        "第二个方形思考点出现，核心亮度上升。",
        "三个方形思考点全部出现，核心达到最高亮度并停留。",
        "三个方点一起淡出，核心回到低亮后循环。",
    ]
    s03_anchor = normalize(args.s03_anchor)
    s03_motion = motion_plan(
        "s03-sikaozhong",
        "保持身体稳定和专注眼，核心缓慢脉冲，右上三个方形思考点依次出现并循环。",
        [args.s03_anchor],
        s03_durations,
        s03_descriptions,
        ["three square thought points", "point opacity", "core pulse", "timing"],
    )
    s03_work = args.work_root / "s03-sikaozhong"
    s03_frames_dir, s03_motion_path = write_working_set(
        s03_work, s03_frames(s03_anchor), s03_motion
    )
    package(package_script, s03_frames_dir, s03_motion_path, args.output_root / "s03-sikaozhong")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--neutral-anchor",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/v6-neutral-rgba.png"),
    )
    parser.add_argument(
        "--s02-anchor",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/s02-working-eyes-rgba.png"),
    )
    parser.add_argument(
        "--s03-anchor",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/s03-thinking-eyes-rgba.png"),
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/work/animation-builds"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/output"),
    )
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=Path(".agents/skills/animated-sticker-maker"),
    )
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
