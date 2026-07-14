#!/usr/bin/env python3
"""Render the locked 12-sticker pack at the approved 30 fps sampling rate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import build_pack as pack
from build_framerate_comparison import interpolate_state


FPS = 30
ROOT = Path("projects/fangxin/packs/social-replies")
OUTPUT = ROOT / "output"
PACK_QA = ROOT / "qa"

SPECS: dict[str, dict[str, object]] = {
    "s01-ok": {
        "durations": (180, 160, 160, 580, 180),
        "states": (
            (0.0, 0.30, 1.00, 0.0, 0.00, 0.00),
            (1.0, 0.55, 0.98, 0.0, 0.42, 0.70),
            (1.0, 0.90, 1.00, -13.0, 1.00, 1.00),
            (1.0, 0.82, 1.00, 0.0, 1.00, 1.00),
            (0.0, 0.26, 1.00, 0.0, 1.00, 0.18),
        ),
    },
    "s02-buxing": {
        "durations": (180, 150, 150, 580, 180),
        "states": (
            (0.0, 0.32, 0.38),
            (7.0, 0.52, 0.68),
            (-7.0, 0.78, 0.92),
            (0.0, 0.70, 1.00),
            (0.0, 0.32, 0.38),
        ),
    },
    "s03-wuyu": {
        "durations": (180, 180, 180, 600, 180),
        "states": (
            (0.18, 0.03, 0.25),
            (0.55, 0.22, 0.60),
            (0.88, 0.62, 0.90),
            (1.00, 1.00, 1.00),
            (0.22, 0.05, 0.30),
        ),
    },
    "s04-xiaosi": {
        "durations": (200, 220, 220, 740, 200),
        "transition_ms": 190.0,
        "states": (
            (0.36, 0.00, 0.0, 1.00, 1.00, 0.00, 0.18),
            (0.58, 1.00, 0.0, 1.00, 1.00, 1.00, 0.48),
            (0.82, 1.00, math.pi, 1.00, 1.00, -1.00, 0.86),
            (0.74, 0.00, 0.0, 1.01, 0.99, 0.00, 1.00),
            (0.36, 0.10, 0.0, 1.00, 1.00, 0.10, 0.24),
        ),
    },
    "s05-xiexie": {
        "durations": (180, 180, 180, 620, 180),
        "states": (
            (0.32, 1.00, 0.25),
            (0.58, 1.03, 0.55),
            (0.96, 1.06, 0.88),
            (0.82, 1.04, 1.00),
            (0.34, 1.00, 0.30),
        ),
    },
    "s06-meishi": {
        "durations": (180, 180, 180, 600, 180),
        "states": (
            (0.965, 0.965, 0.30, 0.28),
            (0.985, 0.985, 0.52, 0.58),
            (1.010, 1.010, 0.78, 0.88),
            (1.000, 1.000, 0.72, 1.00),
            (0.970, 0.970, 0.34, 0.34),
        ),
    },
    "s07-jiayou": {
        "durations": (180, 140, 160, 600, 180),
        "states": (
            (0.980, 0.950, 0.0, 10.0, 0.35, 0.35),
            (1.000, 0.920, 0.0, 24.0, 0.65, 0.70),
            (1.015, 1.000, 0.0, -20.0, 1.00, 1.00),
            (1.000, 0.985, 0.0, -8.0, 0.92, 1.00),
            (0.990, 0.960, 0.0, 12.0, 0.42, 0.42),
        ),
    },
    "s08-xinkule": {
        "durations": (200, 200, 200, 620, 200),
        "states": (
            (0.12, 0.28, 0.25),
            (0.45, 0.42, 0.55),
            (0.85, 0.60, 0.88),
            (1.00, 0.56, 1.00),
            (0.18, 0.30, 0.30),
        ),
    },
    "s09-lihai": {
        "durations": (160, 140, 160, 600, 160),
        "states": (
            (0.00, 0.10, 0.30, 0.25),
            (1.00, 0.42, 0.56, 0.58),
            (1.00, 1.00, 0.92, 0.90),
            (1.00, 0.85, 0.82, 1.00),
            (0.00, 0.15, 0.34, 0.30),
        ),
    },
    "s10-baoqian": {
        "durations": (200, 200, 200, 620, 200),
        "states": (
            (0.12, 0.28, 0.25),
            (0.50, 0.22, 0.55),
            (0.85, 0.16, 0.88),
            (1.00, 0.14, 1.00),
            (0.18, 0.26, 0.30),
        ),
    },
    "s11-zhendejiade": {
        "durations": (180, 200, 200, 620, 180),
        "states": (
            (0.08, 0.26, 0.25),
            (0.35, 0.42, 0.55),
            (0.75, 0.64, 0.88),
            (1.00, 0.58, 1.00),
            (0.12, 0.28, 0.30),
        ),
    },
    "s12-wanan": {
        "durations": (220, 240, 240, 640, 220),
        "states": (
            (0.10, 0.20, 0.25),
            (0.40, 0.14, 0.55),
            (0.75, 0.08, 0.88),
            (1.00, 0.05, 1.00),
            (0.15, 0.18, 0.30),
        ),
    },
}


def legacy_core_state(
    image: Image.Image,
    color: tuple[int, int, int],
    level: float,
) -> Image.Image:
    """Preserve the already-approved S03/S12 core treatment during tweening."""
    level = max(0.0, min(1.0, level))
    box = pack.detect_core_box(image)
    width, height = box[2] - box[0], box[3] - box[1]
    inset = max(7, round(min(width, height) * 0.08))
    face = (box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset)
    radius = max(12, round(min(face[2] - face[0], face[3] - face[1]) * 0.22))
    overlay = Image.new("RGBA", image.size)
    draw = ImageDraw.Draw(overlay)
    if level < 0.35:
        draw.rounded_rectangle(
            face,
            radius=radius,
            fill=(30, 100, 102, round(92 * (0.35 - level) / 0.35)),
        )
    draw.rounded_rectangle(face, radius=radius, fill=(*color, round(35 + 110 * level)))
    result = Image.alpha_composite(image, overlay)
    glow = Image.new("RGBA", image.size)
    ImageDraw.Draw(glow).rounded_rectangle(
        face,
        radius=radius,
        fill=(*color, round(8 + 30 * level)),
    )
    return Image.alpha_composite(result, glow.filter(ImageFilter.GaussianBlur(12)))


def lerp_color(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    progress: float,
) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * progress) for a, b in zip(start, end))


def render_frame(
    sticker: str,
    state: tuple[float, ...],
    anchors: dict[str, Image.Image],
) -> Image.Image:
    neutral = anchors["neutral"]
    half = anchors["half"]
    if sticker == "s01-ok":
        green_mix, core_level, scale_y, dy, check_progress, check_opacity = state
        color = lerp_color(pack.CYAN_WHITE, pack.SUCCESS_GREEN, green_mix)
        frame = pack.set_core_state(
            neutral, color, core_level, top_extend=2, top_cover=6
        )
        frame = pack.transform_subject(frame, scale_y=scale_y, dy=round(dy))
        return pack.add_core_check(frame, check_progress, check_opacity)
    if sticker == "s02-buxing":
        angle, core_level, text_opacity = state
        frame = pack.set_core_state(
            half,
            pack.CORAL_RED,
            core_level,
            tint_boost=55,
            glow_strength=0.25,
            face_spread_max=45,
        )
        frame = pack.rotate_subject(frame, angle)
        return pack.add_recessed_text(frame, "NO", text_opacity)
    if sticker == "s03-wuyu":
        top_level, bottom_level, text_opacity = state
        core_level = 0.12 + 0.10 * (1.0 - top_level)
        frame = legacy_core_state(half, pack.DIM_CYAN, core_level)
        frame = pack.asymmetric_slump(frame, top_level, bottom_level)
        return pack.add_recessed_text(frame, "无语", text_opacity)
    if sticker == "s04-xiaosi":
        core_level, wave_progress, phase, scale_x, scale_y, eye_wobble, text_opacity = state
        frame = pack.set_core_state(anchors["happy"], pack.CYAN_WHITE, core_level)
        if wave_progress > 0.001:
            frame = pack.horizontal_wave(frame, wave_progress, phase)
        frame = pack.eye_micro_wobble(frame, eye_wobble)
        if abs(scale_x - 1.0) > 0.001 or abs(scale_y - 1.0) > 0.001:
            frame = pack.transform_subject(frame, scale_x=scale_x, scale_y=scale_y)
        return pack.add_recessed_text(frame, "hhh!", text_opacity)
    if sticker == "s05-xiexie":
        core_level, face_scale, text_opacity = state
        frame = pack.set_core_state(
            neutral, pack.CYAN_WHITE, core_level, face_scale=face_scale
        )
        return pack.add_recessed_text(frame, "谢谢", text_opacity)
    if sticker == "s06-meishi":
        scale_x, scale_y, core_level, text_opacity = state
        frame = pack.set_core_state(neutral, pack.CYAN_WHITE, core_level)
        frame = pack.transform_subject(frame, scale_x=scale_x, scale_y=scale_y)
        return pack.add_recessed_text(frame, "没事", text_opacity)
    if sticker == "s07-jiayou":
        scale_x, scale_y, dx, dy, core_level, text_opacity = state
        frame = pack.set_core_state(anchors["forward"], pack.CYAN_WHITE, core_level)
        frame = pack.transform_subject(
            frame,
            scale_x=scale_x,
            scale_y=scale_y,
            dx=round(dx),
            dy=round(dy),
        )
        return pack.add_recessed_text(frame, "加油", text_opacity)
    if sticker == "s08-xinkule":
        progress, core_level, text_opacity = state
        frame = pack.set_core_state(neutral, pack.CYAN_WHITE, core_level)
        frame = pack.vertical_pose_warp(frame, progress, top_shift=30.0)
        return pack.add_recessed_text(frame, "辛苦了", text_opacity)
    if sticker == "s09-lihai":
        eye_open, progress, core_level, text_opacity = state
        # Eye modules are discrete identity assets. Crossfading the full anchors
        # creates duplicate highlights, so switch cleanly while the body warp,
        # core and text continue their 30 fps interpolation.
        anchor = neutral if eye_open >= 0.5 else half
        frame = pack.set_core_state(anchor, pack.CYAN_WHITE, core_level)
        frame = pack.vertical_pose_warp(frame, progress, top_shift=-22.0)
        return pack.add_recessed_text(frame, "厉害", text_opacity)
    if sticker == "s10-baoqian":
        progress, core_level, text_opacity = state
        frame = pack.set_core_state(neutral, pack.DIM_CYAN, core_level)
        frame = pack.transform_subject(
            frame,
            scale_x=1.0 - 0.04 * progress,
            scale_y=1.0 - 0.035 * progress,
            dy=round(18 * progress),
        )
        return pack.add_recessed_text(frame, "抱歉", text_opacity)
    if sticker == "s11-zhendejiade":
        progress, core_level, text_opacity = state
        frame = pack.set_core_state(
            anchors["focus"],
            pack.WARNING_YELLOW,
            core_level,
            top_extend=2,
            top_cover=6,
        )
        frame = pack.rotate_subject(frame, -7.0 * progress)
        return pack.add_recessed_text(frame, "真的假的", text_opacity)
    if sticker == "s12-wanan":
        progress, core_level, text_opacity = state
        frame = pack.set_core_state(
            half,
            pack.DIM_CYAN,
            core_level,
            face_spread_max=45,
            dim_strength=1.8,
            glow_strength=0.35,
        )
        frame = pack.transform_subject(frame, dy=round(26 * progress))
        frame = pack.dim_subject(frame, 1.0 - 0.16 * progress)
        return pack.add_recessed_text(frame, "晚安", text_opacity)
    raise ValueError(sticker)


def timing(total_ms: int) -> tuple[list[int], list[float]]:
    frame_count = max(1, round(total_ms * FPS / 1000))
    boundaries = [round(index * total_ms / frame_count) for index in range(frame_count + 1)]
    durations = [end - start for start, end in zip(boundaries, boundaries[1:])]
    return durations, [float(value) for value in boundaries[:-1]]


def make_render_contact_sheet(frames: list[Image.Image], path: Path) -> None:
    sample_count = 12
    indices = [round(index * (len(frames) - 1) / (sample_count - 1)) for index in range(sample_count)]
    previews = [pack.composite_on(frames[index], (248, 248, 248), 220) for index in indices]
    sheet = Image.new("RGB", (220 * 6, 220 * 2), (248, 248, 248))
    for index, preview in enumerate(previews):
        sheet.paste(preview, ((index % 6) * 220, (index // 6) * 220))
    sheet.save(path)


def render_sticker(
    sticker: str,
    anchors: dict[str, Image.Image],
) -> dict[str, object]:
    spec = SPECS[sticker]
    authored_durations = spec["durations"]
    states = spec["states"]
    total_ms = sum(authored_durations)
    frame_durations, times = timing(total_ms)
    frames = [
        render_frame(
            sticker,
            interpolate_state(
                states,
                authored_durations,
                time_ms,
                True,
                transition_max_ms=float(spec.get("transition_ms", 120.0)),
            ),
            anchors,
        )
        for time_ms in times
    ]

    output = OUTPUT / sticker
    frame_dir = output / "source" / "rendered-frames"
    qa = output / "qa"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for stale in frame_dir.glob("*.png"):
        stale.unlink()
    for index, frame in enumerate(frames):
        frame.save(frame_dir / f"{index:03d}.png")

    frames[0].save(
        output / "sticker.webp",
        save_all=True,
        append_images=frames[1:],
        duration=frame_durations,
        loop=0,
        lossless=False,
        quality=92,
        method=6,
        minimize_size=True,
        allow_mixed=True,
    )
    preview_frames = [
        pack.composite_on(frame, (238, 242, 242), 512) for frame in frames
    ]
    preview_frames[0].save(
        qa / "preview-30fps.png",
        save_all=True,
        append_images=preview_frames[1:],
        duration=frame_durations,
        loop=0,
        disposal=1,
        blend=0,
    )
    make_render_contact_sheet(frames, qa / "30fps-contact-sheet.png")

    motion_path = output / "source" / "motion.json"
    motion = json.loads(motion_path.read_text(encoding="utf-8"))
    motion["render"] = {
        "fps": FPS,
        "method": "deterministic parameter tweening",
        "transition_window_ms_max": float(spec.get("transition_ms", 120.0)),
        "frame_dir": "rendered-frames",
        "frame_count": len(frames),
        "frame_durations_ms": frame_durations,
        "total_duration_ms": sum(frame_durations),
    }
    motion_path.write_text(
        json.dumps(motion, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    frame_metrics = [pack.alpha_metrics(frame) for frame in frames]
    endpoint_delta = pack.loop_endpoint_delta(frames[0], frames[-1])
    checks = {
        "nominal_fps_is_30": FPS == 30,
        "all_frames_1024_rgba": all(
            frame.mode == "RGBA" and frame.size == (pack.CANVAS, pack.CANVAS)
            for frame in frames
        ),
        "all_borders_transparent": all(
            item["border_is_transparent"] for item in frame_metrics
        ),
        "duration_matches_authored_timing": sum(frame_durations) == total_ms,
        "loop_endpoint_mean_rgba_delta_below_8": endpoint_delta < 8.0,
    }
    result = {
        "status": "pass" if all(checks.values()) else "fail",
        "fps": FPS,
        "frame_count": len(frames),
        "duration_ms": total_ms,
        "frame_duration_ms_range": [min(frame_durations), max(frame_durations)],
        "loop_endpoint_mean_rgba_delta": round(endpoint_delta, 4),
        "checks": checks,
        "visual_review": {"status": "pending"},
    }
    (qa / "30fps-report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        default=",".join(SPECS),
        help="Comma-separated output ids; defaults to the complete pack",
    )
    args = parser.parse_args()
    selected = [item.strip() for item in args.only.split(",") if item.strip()]
    unknown = set(selected) - set(SPECS)
    if unknown:
        raise ValueError(f"unknown sticker(s): {', '.join(sorted(unknown))}")

    anchors = {
        "neutral": pack.normalize(pack.ANCHORS / "neutral-rgba.png"),
        "half": pack.normalize(pack.ANCHORS / "half-eyes-rgba.png"),
        "happy": pack.normalize(pack.ANCHORS / "happy-eyes-rgba.png"),
        "focus": pack.normalize(pack.ANCHORS / "focus-eyes-rgba.png"),
        "forward": pack.fit_subject(
            pack.ANCHORS / "s07-jiayou-generated-v1-rgba.png",
            target_width=825,
            target_height=825,
            center_y=510,
        ),
    }
    results = {sticker: render_sticker(sticker, anchors) for sticker in selected}
    if set(selected) != set(SPECS):
        return
    review = {
        "status": "pass" if all(item["status"] == "pass" for item in results.values()) else "fail",
        "fps": FPS,
        "method": "deterministic parameter tweening",
        "reviewed_on": "2026-07-14",
        "stickers": {
            sticker: {
                "status": item["status"],
                "frame_count": item["frame_count"],
                "duration_ms": item["duration_ms"],
                "loop_endpoint_mean_rgba_delta": item["loop_endpoint_mean_rgba_delta"],
            }
            for sticker, item in results.items()
        },
        "visual_review": {"status": "pending"},
    }
    (PACK_QA / "30fps-review.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
