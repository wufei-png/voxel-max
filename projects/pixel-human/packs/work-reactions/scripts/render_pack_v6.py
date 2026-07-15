#!/usr/bin/env python3
"""Render work-reactions v6 with grounded palms for S09 kowtow."""

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
import render_pack_v5 as pack_v5  # noqa: E402


PACK_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACK_DIR / "work" / "v6"


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


def render_kowtow(
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


def comparison_frames(
    current: list[Image.Image],
    revised: list[Image.Image],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output = []
    for current_frame, revised_frame in zip(current, revised, strict=True):
        board = Image.new(
            "RGBA",
            (size * 2 + gap, size * 2 + gap),
            common.TRANSPARENT,
        )
        for column, frame in enumerate((current_frame, revised_frame)):
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
        "s04-meeting": pack_v5.render_meeting(layers),
        "s05-done": pack_v2.render_done(layers),
        "s06-speechless": pack_v1.render_speechless(layers),
        "s07-crashed": trial_v3.render_crashed(layers),
        "s08-off-work": pack_v2.render_off_work(layers),
        "s09-kowtow": render_kowtow(layers),
    }
    durations = {
        item_id: pack_v2.STANDARD_DURATIONS for item_id in pack_v2.ITEM_ORDER
    }
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
        pack_v2.board_frames(items, durations, size=144, gap=8),
        review_dir / "selected-pack-light-dark.gif",
        [100] * 21,
    )
    pack_v2.save_gif(
        comparison_frames(
            pack_v2.render_kowtow(layers),
            items["s09-kowtow"],
            size=288,
            gap=16,
        ),
        review_dir / "kowtow-v2-v6-comparison-light-dark.gif",
        pack_v2.KOWTOW_DURATIONS,
    )
    (review_dir / "order.md").write_text(
        "# v6 审阅顺序\n\n"
        "九张总览顺序为 S01-S09。磕头对照左列为 v2，右列为 v6；上行为浅色，下行为深色。\n",
        encoding="utf-8",
    )

    manifest = {
        "status": "selected_for_release_v1",
        "pack_id": "work-reactions",
        "based_on": "work/v5",
        "change_scope": ["s09-kowtow"],
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "item_order": pack_v2.ITEM_ORDER,
        "labels": pack_v2.LABELS,
        "items": manifest_items,
        "kowtow_notes": {
            "removed": "thin pale hand strips and decorative impact blocks",
            "palms": "grounded blocks connected to continuous purple forearms",
            "semantic_separation": "frontal symmetry, no keyboard, repeated bow",
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
