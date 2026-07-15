#!/usr/bin/env python3
"""Render and compare the current and grounded-palms kowtow motions."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
PACK_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path(__file__).resolve().parents[4]
PROJECT_SCRIPTS = PROJECT_DIR / "scripts"
PACK_SCRIPTS = PACK_DIR / "scripts"
for script_dir in (PROJECT_SCRIPTS, PACK_SCRIPTS):
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

import render_identity_trials as common  # noqa: E402
import render_pack_v2 as pack_v2  # noqa: E402


CANDIDATES_DIR = ROOT / "candidates"
REVIEW_DIR = ROOT / "review"
VARIANT_ORDER = ["v01-current", "v02-grounded-palms"]
DURATIONS = pack_v2.KOWTOW_DURATIONS


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def draw_upright_arms(frame: Image.Image, *, prepared: bool) -> None:
    if prepared:
        common.rect(frame, (10, 31, 16, 39), common.PURPLE)
        common.rect(frame, (32, 31, 38, 39), common.PURPLE)
        common.rect(frame, (12, 37, 16, 40), common.FACE)
        common.rect(frame, (32, 37, 36, 40), common.FACE)
        return
    common.rect(frame, (12, 30, 18, 37), common.PURPLE)
    common.rect(frame, (30, 30, 36, 37), common.PURPLE)
    common.rect(frame, (15, 34, 18, 37), common.FACE)
    common.rect(frame, (30, 34, 33, 37), common.FACE)


def draw_grounded_arms(frame: Image.Image) -> None:
    """Draw palms as grounded blocks with continuous purple forearms."""
    common.rect(frame, (9, 31, 16, 39), common.PURPLE)
    common.rect(frame, (32, 31, 39, 39), common.PURPLE)
    common.rect(frame, (11, 37, 16, 41), common.FACE)
    common.rect(frame, (32, 37, 37, 41), common.FACE)


def grounded_pitch_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    crown_y: int,
    face_y: int,
) -> Image.Image:
    _head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 21))
    draw_grounded_arms(frame)
    common.rect(frame, (17, crown_y, 31, face_y - 1), common.HAIR)
    common.rect(frame, (19, face_y, 29, face_y + 3), common.FACE)
    return frame


def grounded_down_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> Image.Image:
    _head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 22))
    draw_grounded_arms(frame)
    common.rect(frame, (17, 27, 31, 39), common.HAIR)
    return frame


def render_grounded_palms(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    bowed = grounded_down_pose(layers)
    upright = common.compose_character(layers, head_dy=1, body_dy=1)
    draw_upright_arms(upright, prepared=False)
    prepare = common.compose_character(layers, head_dy=3, body_dy=1)
    draw_upright_arms(prepare, prepared=True)
    pitch = grounded_pitch_pose(layers, crown_y=21, face_y=32)
    lifted = grounded_pitch_pose(layers, crown_y=23, face_y=34)
    return [bowed, upright, prepare, pitch, bowed.copy(), lifted, bowed.copy()]


def validate_frames(variant_id: str, frames: list[Image.Image]) -> None:
    pack_v2.validate_item(variant_id, frames, DURATIONS)
    if len({frame.tobytes() for frame in frames}) < 5:
        raise ValueError(f"{variant_id}: fewer than five distinct poses")
    for index, frame in enumerate(frames):
        alpha = frame.getchannel("A").histogram()
        if sum(alpha[1:255]) != 0:
            raise ValueError(f"{variant_id} frame {index}: alpha must be binary")


def export_variant(variant_id: str, frames: list[Image.Image]) -> dict[str, object]:
    validate_frames(variant_id, frames)
    variant_dir = CANDIDATES_DIR / variant_id
    frames_dir = variant_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_entries = []
    for index, frame in enumerate(frames):
        path = frames_dir / f"frame-{index:02d}.png"
        frame.save(path)
        frame_entries.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
        )
    pack_v2.save_apng(frames, variant_dir / f"{variant_id}.apng", DURATIONS)
    pack_v2.save_gif(
        common.scaled_frames(frames, 480),
        variant_dir / f"{variant_id}-review.gif",
        DURATIONS,
    )
    pack_v2.save_gif(
        common.light_dark_frames(frames, 480, 16),
        variant_dir / f"{variant_id}-review-light-dark.gif",
        DURATIONS,
    )
    pack_v2.save_gif(
        common.light_dark_frames(frames, 50, 8),
        variant_dir / f"{variant_id}-review-50-light-dark.gif",
        DURATIONS,
    )
    return {
        "id": variant_id,
        "frame_count": len(frames),
        "durations_ms": DURATIONS,
        "frames": frame_entries,
    }


def comparison_frames(
    variants: dict[str, list[Image.Image]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output = []
    for frames_at_index in zip(
        *(variants[variant_id] for variant_id in VARIANT_ORDER),
        strict=True,
    ):
        board = Image.new(
            "RGBA",
            (size * 2 + gap, size * 2 + gap),
            common.TRANSPARENT,
        )
        for column, frame in enumerate(frames_at_index):
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            x = column * (size + gap)
            board.alpha_composite(
                common.on_background(scaled, common.LIGHT_BACKGROUND),
                (x, 0),
            )
            board.alpha_composite(
                common.on_background(scaled, common.DARK_BACKGROUND),
                (x, size + gap),
            )
        output.append(board)
    return output


def contact_sheet(
    variants: dict[str, list[Image.Image]],
    *,
    background: tuple[int, int, int, int],
) -> Image.Image:
    size = 96
    gap = 6
    sheet = Image.new(
        "RGBA",
        (size * 7 + gap * 6, size * 2 + gap),
        common.TRANSPARENT,
    )
    for row, variant_id in enumerate(VARIANT_ORDER):
        for column, frame in enumerate(variants[variant_id]):
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            panel = common.on_background(scaled, background)
            sheet.alpha_composite(
                panel,
                (column * (size + gap), row * (size + gap)),
            )
    return sheet


def main() -> None:
    master = common.load_master()
    layers = common.split_master(master)
    variants = {
        "v01-current": pack_v2.render_kowtow(layers),
        "v02-grounded-palms": render_grounded_palms(layers),
    }
    entries = [
        export_variant(variant_id, variants[variant_id])
        for variant_id in VARIANT_ORDER
    ]
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    pack_v2.save_gif(
        comparison_frames(variants, size=288, gap=16),
        REVIEW_DIR / "current-vs-grounded-palms-light-dark.gif",
        DURATIONS,
    )
    pack_v2.save_gif(
        comparison_frames(variants, size=50, gap=8),
        REVIEW_DIR / "current-vs-grounded-palms-50-light-dark.gif",
        DURATIONS,
    )
    contact_sheet(
        variants,
        background=common.LIGHT_BACKGROUND,
    ).save(REVIEW_DIR / "frame-contact-sheet-light.png")
    contact_sheet(
        variants,
        background=common.DARK_BACKGROUND,
    ).save(REVIEW_DIR / "frame-contact-sheet-dark.png")
    manifest = {
        "status": "candidate_review",
        "item": "s09-kowtow",
        "canvas": [48, 48],
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "variant_order": VARIANT_ORDER,
        "variants": entries,
        "v02_design": {
            "removed": "pale impact strips and side impact blocks",
            "palms": "compact grounded blocks",
            "forearms": "continuous purple connection from body to palms",
            "semantic_separation": "frontal symmetry, no keyboard, repeated bow",
        },
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(ROOT)


if __name__ == "__main__":
    main()
