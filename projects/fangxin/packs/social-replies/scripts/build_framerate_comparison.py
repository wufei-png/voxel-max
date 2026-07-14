#!/usr/bin/env python3
"""Build parametric APNG previews for animation smoothness review.

The production sources keep their authored keyframe timings. These previews
redraw real intermediate poses from the pack's deterministic motion parameters;
they do not use optical-flow interpolation or repeat frames to fake smoothness.
"""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path

import build_pack as pack


ROOT = Path("projects/fangxin/packs/social-replies")
OUTPUT = ROOT / "output"
QA = ROOT / "qa" / "frame-rate-comparison"
STICKERS = ("s02-buxing", "s05-xiexie", "s11-zhendejiade")
RATES = (
    ("a-current", 20, False),
    ("b-balanced", 30, True),
    ("c-double", 40, True),
)

SPECS: dict[str, dict[str, object]] = {
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
}


def run(command: list[str]) -> str:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout


def probe(path: Path, count_frames: bool = False) -> dict[str, object]:
    entries = "stream=avg_frame_rate,r_frame_rate,pix_fmt"
    if count_frames:
        entries += ",nb_read_frames"
    payload = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                *( ["-count_frames"] if count_frames else [] ),
                "-show_entries",
                entries,
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    stream = payload["streams"][0]
    stream["duration"] = payload.get("format", {}).get("duration")
    return stream


def interpolate_state(
    states: tuple[tuple[float, ...], ...],
    durations: tuple[int, ...],
    time_ms: float,
    smooth: bool,
    transition_max_ms: float = 120.0,
) -> tuple[float, ...]:
    cursor = 0.0
    for index, duration in enumerate(durations):
        if time_ms < cursor + duration:
            if not smooth:
                return states[index]
            local = time_ms - cursor
            transition = min(transition_max_ms, duration * 0.75)
            if local < duration - transition:
                return states[index]
            progress = (local - (duration - transition)) / transition
            progress = progress * progress * (3.0 - 2.0 * progress)
            next_state = states[(index + 1) % len(states)]
            return tuple(
                start + (end - start) * progress
                for start, end in zip(states[index], next_state)
            )
        cursor += duration
    return states[-1]


def render_frame(
    sticker: str,
    state: tuple[float, ...],
    anchors: dict[str, object],
):
    if sticker == "s02-buxing":
        angle, core_level, token_opacity = state
        frame = pack.set_core_state(
            anchors["half"],
            pack.CORAL_RED,
            core_level,
            tint_boost=55,
            glow_strength=0.25,
            face_spread_max=45,
        )
        frame = pack.rotate_subject(frame, angle)
        return pack.add_recessed_text(frame, "NO", token_opacity)
    if sticker == "s05-xiexie":
        core_level, face_scale, text_opacity = state
        frame = pack.set_core_state(
            anchors["neutral"], pack.CYAN_WHITE, core_level, face_scale=face_scale
        )
        return pack.add_recessed_text(frame, "谢谢", text_opacity)
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
    raise ValueError(sticker)


def build_variant(
    sticker: str,
    target: Path,
    fps: int,
    smooth: bool,
    anchors: dict[str, object],
) -> int:
    spec = SPECS[sticker]
    durations = spec["durations"]
    states = spec["states"]
    total_ms = sum(durations)
    frame_count = math.ceil(total_ms * fps / 1000)
    with tempfile.TemporaryDirectory(prefix=f"{sticker}-{fps}fps-") as temp:
        frame_dir = Path(temp)
        for index in range(frame_count):
            time_ms = index * 1000 / fps
            state = interpolate_state(states, durations, time_ms, smooth)
            frame = render_frame(sticker, state, anchors)
            preview = pack.composite_on(frame, (238, 242, 242), 512)
            preview.save(frame_dir / f"{index:04d}.png")
        run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(frame_dir / "%04d.png"),
                "-plays",
                "0",
                "-f",
                "apng",
                str(target),
            ]
        )
    return frame_count


def main() -> None:
    QA.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "purpose": "review-only frame-rate comparison; not production delivery assets",
        "carrier": "light-background APNG at nominal 20/30/40 fps; total duration differs from authored timing by at most one sample",
        "interpolation": "deterministic parameter tweening with a 120 ms maximum transition window",
        "stickers": {},
    }
    anchors = {
        "neutral": pack.normalize(pack.ANCHORS / "neutral-rgba.png"),
        "half": pack.normalize(pack.ANCHORS / "half-eyes-rgba.png"),
        "focus": pack.normalize(pack.ANCHORS / "focus-eyes-rgba.png"),
    }
    for sticker in STICKERS:
        source = OUTPUT / sticker / "qa" / "preview.gif"
        source_probe = probe(source)
        authored_duration = sum(SPECS[sticker]["durations"])
        variants: list[dict[str, object]] = []
        for label, fps, interpolate in RATES:
            target = QA / f"{sticker}-{label}-{fps}fps.png"
            sample_count = build_variant(sticker, target, fps, interpolate, anchors)
            info = probe(target, count_frames=True)
            variants.append(
                {
                    "label": label,
                    "fps": fps,
                    "interpolated": interpolate,
                    "file": target.name,
                    "authored_sample_count": sample_count,
                    "encoded_frame_count": int(info["nb_read_frames"]),
                    "avg_frame_rate": info["avg_frame_rate"],
                    "pixel_format": info["pix_fmt"],
                    "bytes": target.stat().st_size,
                }
            )
        manifest["stickers"][sticker] = {
            "source": str(source.relative_to(ROOT)),
            "authored_duration_ms": authored_duration,
            "legacy_gif_carrier_duration_ms": round(float(source_probe["duration"]) * 1000),
            "variants": variants,
        }
    (QA / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
