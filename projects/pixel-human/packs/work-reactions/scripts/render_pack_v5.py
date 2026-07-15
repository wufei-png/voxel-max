#!/usr/bin/env python3
"""Render v3 headset geometry with the original v2 raised-hand position."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[3]
PROJECT_SCRIPTS = PROJECT_DIR / "scripts"
PACK_SCRIPTS = Path(__file__).resolve().parent
for script_dir in (PROJECT_SCRIPTS, PACK_SCRIPTS):
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

import render_identity_trials as common  # noqa: E402
import render_identity_trials_v2 as trial_v2  # noqa: E402
import render_identity_trials_v3 as trial_v3  # noqa: E402
import render_pack_v1 as pack_v1  # noqa: E402
import render_pack_v2 as pack_v2  # noqa: E402
import render_pack_v3 as pack_v3  # noqa: E402
import render_pack_v4 as pack_v4  # noqa: E402


PACK_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACK_DIR / "work" / "v5"


def draw_v3_headset_with_v2_hand(
    frame: Image.Image,
    *,
    hand_y: int,
    signal_on: bool,
) -> None:
    # V3 headset: mirrored full-size cups and inward microphone connection.
    common.rect(frame, (16, 8, 32, 9), common.FX_BLUE_DARK)
    common.rect(frame, (14, 10, 16, 23), common.FX_BLUE_DARK)
    common.rect(frame, (32, 10, 34, 23), common.FX_BLUE_DARK)
    common.rect(frame, (14, 18, 16, 24), common.FX_BLUE)
    common.rect(frame, (32, 18, 34, 24), common.FX_BLUE)
    common.rect(frame, (31, 23, 32, 24), common.FX_BLUE)
    common.rect(frame, (30, 24, 31, 25), common.FX_BLUE_DARK)
    common.rect(
        frame,
        (28, 25, 30, 26),
        common.FX_BLUE if signal_on else common.FX_BLUE_DARK,
    )

    # Exact v2 arm and hand coordinates; no v3 outward spacing adjustment.
    common.rect(frame, (37, 28, 40, 35), common.PURPLE)
    common.rect(frame, (37, hand_y, 40, hand_y + 4), common.FACE)


def render_meeting(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(20, True, 0), (18, True, 0), (19, False, 1), (21, True, 0), (20, True, 0)]
    frames: list[Image.Image] = []
    for hand_y, signal_on, head_dy in states:
        frame = common.compose_character(layers, head_dy=head_dy)
        draw_v3_headset_with_v2_hand(frame, hand_y=hand_y, signal_on=signal_on)
        frames.append(frame)
    return frames


def four_way_comparison_frames(
    variants: list[list[Image.Image]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output: list[Image.Image] = []
    for frames_at_index in zip(*variants, strict=True):
        board = Image.new(
            "RGBA",
            (size * 4 + gap * 3, size * 2 + gap),
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


def main() -> None:
    master = common.load_master()
    layers = common.split_master(master)
    items = {
        "s01-received": trial_v2.render_received(layers),
        "s02-working": trial_v2.render_working(layers),
        "s03-wait": pack_v1.render_wait(layers),
        "s04-meeting": render_meeting(layers),
        "s05-done": pack_v2.render_done(layers),
        "s06-speechless": pack_v1.render_speechless(layers),
        "s07-crashed": trial_v3.render_crashed(layers),
        "s08-off-work": pack_v2.render_off_work(layers),
        "s09-kowtow": pack_v2.render_kowtow(layers),
    }
    durations = {item_id: pack_v2.STANDARD_DURATIONS for item_id in pack_v2.ITEM_ORDER}
    durations["s05-done"] = pack_v2.DONE_DURATIONS
    durations["s08-off-work"] = pack_v2.OFF_WORK_DURATIONS
    durations["s09-kowtow"] = pack_v2.KOWTOW_DURATIONS
    manifest_items = [
        pack_v3.export_item(
            item_id,
            items[item_id],
            durations[item_id],
            output_dir=OUTPUT_DIR,
        )
        for item_id in pack_v2.ITEM_ORDER
    ]

    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    pack_v2.save_gif(
        four_way_comparison_frames(
            [
                pack_v2.render_meeting(layers),
                pack_v3.render_meeting(layers),
                pack_v4.render_meeting(layers),
                items["s04-meeting"],
            ],
            size=288,
            gap=16,
        ),
        review_dir / "meeting-v2-v3-v4-v5-comparison-light-dark.gif",
        pack_v2.STANDARD_DURATIONS,
    )
    pack_v2.save_gif(
        common.light_dark_frames(items["s04-meeting"], 50, 8),
        review_dir / "meeting-v5-50-light-dark.gif",
        pack_v2.STANDARD_DURATIONS,
    )
    (review_dir / "order.md").write_text(
        "# 耳机对照顺序\n\n从左到右为 v2 / v3 / v4 / v5；上行为浅色，下行为深色。\n",
        encoding="utf-8",
    )

    manifest = {
        "status": "candidate_comparison",
        "pack_id": "work-reactions",
        "based_on": "work/v3",
        "borrows_from": "work/v2 raised-hand coordinates",
        "change_scope": ["s04-meeting"],
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "item_order": pack_v2.ITEM_ORDER,
        "labels": pack_v2.LABELS,
        "items": manifest_items,
        "meeting_notes": {
            "headset_and_microphone": "pixel-identical to v3",
            "raised_hand": "pixel-identical coordinates to v2",
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
