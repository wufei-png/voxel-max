#!/usr/bin/env python3
"""Render the approved trials with a face-down crashed pose."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

import render_identity_trials as common
import render_identity_trials_v2 as v2
import render_identity_trials_v3 as v3


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "identity" / "trials" / "v4"


def front_pitch_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    body_dy: int,
    hands: tuple[tuple[int, int], tuple[int, int]],
) -> Image.Image:
    """Show the face receding as the complete head pitches toward the desk."""
    _head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 20 + body_dy))
    v3.draw_hands(frame, hands[0], hands[1])

    # The head stays centered: the visible face contracts to a short lower
    # strip while the black crown expands toward the viewer.
    common.rect(frame, (17, 21, 31, 31), common.HAIR)
    common.rect(frame, (19, 32, 29, 35), common.FACE)
    v3.draw_flat_keyboard(frame)
    return frame


def face_down_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    body_dy: int,
    hands: tuple[tuple[int, int], tuple[int, int]],
) -> Image.Image:
    """Show only the all-black crown after the face lands on the keyboard."""
    _head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 20 + body_dy))
    v3.draw_hands(frame, hands[0], hands[1])
    common.rect(frame, (17, 27, 31, 37), common.HAIR)
    v3.draw_flat_keyboard(frame)
    return frame


def render_crashed(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    collapsed = face_down_pose(
        layers,
        body_dy=2,
        hands=((11, 36), (34, 36)),
    )
    upright = v3.upright_pose(
        layers,
        head_dy=0,
        body_dy=0,
        hands=((16, 35), (29, 35)),
    )
    anticipation = v3.upright_pose(
        layers,
        head_dy=2,
        body_dy=0,
        hands=((16, 31), (29, 31)),
    )
    falling = front_pitch_pose(
        layers,
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
        "status": "approved",
        "supersedes": "identity/trials/v3",
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "trial_order": v2.TRIAL_ORDER,
        "trials": manifest_trials,
        "notes": {
            "received": "approved frame-for-frame reuse of v2 received",
            "working": "approved frame-for-frame reuse of v2 working",
            "crashed": "approved upright-to-face-down collapse with an all-black crown",
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
