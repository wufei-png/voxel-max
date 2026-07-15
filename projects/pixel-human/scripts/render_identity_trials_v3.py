#!/usr/bin/env python3
"""Render v3 trials with an explicit upright-to-collapse body sequence."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

import render_identity_trials as common
import render_identity_trials_v2 as v2


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "identity" / "trials" / "v3"


def draw_flat_keyboard(frame: Image.Image) -> None:
    common.rect(frame, (10, 38, 38, 43), common.HAIR)
    common.rect(frame, (11, 38, 37, 38), common.FX_BLUE_DARK)
    common.rect(frame, (12, 40, 36, 42), common.PURPLE_SHADOW)


def draw_hands(
    frame: Image.Image,
    left: tuple[int, int],
    right: tuple[int, int],
) -> None:
    common.rect(frame, (9, 32, 19, 38), common.PURPLE)
    common.rect(frame, (29, 32, 39, 38), common.PURPLE)
    common.rect(frame, (left[0], left[1], left[0] + 3, left[1] + 1), common.FACE)
    common.rect(frame, (right[0], right[1], right[0] + 3, right[1] + 1), common.FACE)


def upright_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    head_dy: int,
    body_dy: int,
    hands: tuple[tuple[int, int], tuple[int, int]],
) -> Image.Image:
    frame = common.compose_character(
        layers,
        head_dy=head_dy,
        body_dy=body_dy,
    )
    draw_hands(frame, hands[0], hands[1])
    draw_flat_keyboard(frame)
    return frame


def rotated_collapse_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    head_y: int,
    body_dy: int,
    hands: tuple[tuple[int, int], tuple[int, int]],
) -> Image.Image:
    head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 20 + body_dy))
    draw_hands(frame, hands[0], hands[1])

    # The approved head occupies a 15x15 identity square. Rotate the complete
    # square so hair and blank face turn together rather than drifting apart.
    head_square = head.crop((9, 3, 24, 18)).transpose(Image.Transpose.ROTATE_90)
    frame.alpha_composite(head_square, (17, head_y))
    draw_flat_keyboard(frame)
    return frame


def render_crashed(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    collapsed = rotated_collapse_pose(
        layers,
        head_y=23,
        body_dy=2,
        hands=((11, 36), (34, 36)),
    )
    upright = upright_pose(
        layers,
        head_dy=0,
        body_dy=0,
        hands=((16, 35), (29, 35)),
    )
    anticipation = upright_pose(
        layers,
        head_dy=2,
        body_dy=0,
        hands=((16, 31), (29, 31)),
    )
    falling = rotated_collapse_pose(
        layers,
        head_y=19,
        body_dy=1,
        hands=((13, 34), (32, 34)),
    )
    return [collapsed, upright, anticipation, falling, collapsed.copy()]


def main() -> None:
    master = common.load_master()
    layers = common.split_master(master)
    trials = {
        "received": v2.render_received(layers),
        "working": v2.render_working(layers),
        "crashed": render_crashed(layers),
    }
    manifest_trials = [
        v2.export_trial(trial_id, frames, output_dir=OUTPUT_DIR)
        for trial_id, frames in trials.items()
    ]

    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    common.save_gif(
        v2.unlabeled_board_frames(trials, size=288, gap=16),
        review_dir / "unlabeled-review-light-dark.gif",
    )
    common.save_gif(
        v2.unlabeled_board_frames(trials, size=50, gap=8),
        review_dir / "unlabeled-review-50-light-dark.gif",
    )
    v2.contact_sheet(trials, background=common.LIGHT_BACKGROUND).save(
        review_dir / "frame-contact-sheet-light.png"
    )
    v2.contact_sheet(trials, background=common.DARK_BACKGROUND).save(
        review_dir / "frame-contact-sheet-dark.png"
    )
    v2.write_review_order(output_dir=OUTPUT_DIR)

    manifest = {
        "status": "superseded_by_v4",
        "superseded_by": "identity/trials/v4",
        "supersedes": "identity/trials/v2",
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "trial_order": v2.TRIAL_ORDER,
        "trials": manifest_trials,
        "notes": {
            "received": "frame-for-frame reuse of v2 received",
            "working": "frame-for-frame reuse of v2 working",
            "crashed": "upright, anticipate, rotate and collapse onto keyboard",
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for trial in manifest_trials:
        print(OUTPUT_DIR / str(trial["id"]))


if __name__ == "__main__":
    main()
