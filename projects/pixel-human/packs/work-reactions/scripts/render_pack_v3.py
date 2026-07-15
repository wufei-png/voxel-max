#!/usr/bin/env python3
"""Render work-reactions v3 with a balanced meeting headset."""

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


PACK_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACK_DIR / "work" / "v3"


def draw_balanced_headset(
    frame: Image.Image,
    *,
    hand_y: int,
    signal_on: bool,
) -> None:
    # Headband arms and cyan ear cups are exact left-right mirrors.
    common.rect(frame, (16, 8, 32, 9), common.FX_BLUE_DARK)
    common.rect(frame, (14, 10, 16, 23), common.FX_BLUE_DARK)
    common.rect(frame, (32, 10, 34, 23), common.FX_BLUE_DARK)
    common.rect(frame, (14, 18, 16, 24), common.FX_BLUE)
    common.rect(frame, (32, 18, 34, 24), common.FX_BLUE)

    # Preserve the complete cyan cup. The hinge grows from its inner edge into
    # the face area, then the dark boom continues inward along the lower edge.
    common.rect(frame, (31, 23, 32, 24), common.FX_BLUE)
    common.rect(frame, (30, 24, 31, 25), common.FX_BLUE_DARK)
    common.rect(
        frame,
        (28, 25, 30, 26),
        common.FX_BLUE if signal_on else common.FX_BLUE_DARK,
    )

    # Keep the raised hand spatially separate from the microphone assembly.
    common.rect(frame, (40, 28, 43, 35), common.PURPLE)
    common.rect(frame, (40, hand_y, 43, hand_y + 4), common.FACE)


def render_meeting(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(20, True, 0), (18, True, 0), (19, False, 1), (21, True, 0), (20, True, 0)]
    frames: list[Image.Image] = []
    for hand_y, signal_on, head_dy in states:
        frame = common.compose_character(layers, head_dy=head_dy)
        draw_balanced_headset(frame, hand_y=hand_y, signal_on=signal_on)
        frames.append(frame)
    return frames


def export_item(
    item_id: str,
    frames: list[Image.Image],
    durations: list[int],
    *,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, object]:
    pack_v2.validate_item(item_id, frames, durations)
    item_dir = output_dir / item_id
    frames_dir = item_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[str] = []
    for index, frame in enumerate(frames):
        path = frames_dir / f"frame-{index:02d}.png"
        frame.save(path)
        frame_paths.append(str(path.relative_to(output_dir)))
    pack_v2.save_apng(frames, item_dir / f"{item_id}.apng", durations)
    pack_v2.save_gif(
        common.scaled_frames(frames, 480),
        item_dir / f"{item_id}-review.gif",
        durations,
    )
    pack_v2.save_gif(
        common.light_dark_frames(frames, 480, 16),
        item_dir / f"{item_id}-review-light-dark.gif",
        durations,
    )
    pack_v2.save_gif(
        common.light_dark_frames(frames, 50, 8),
        item_dir / f"{item_id}-review-50-light-dark.gif",
        durations,
    )
    return {
        "id": item_id,
        "frame_paths": frame_paths,
        "durations_ms": durations,
        "distinct_poses": len({frame.tobytes() for frame in frames}),
    }


def meeting_comparison_frames(
    current: list[Image.Image],
    revised: list[Image.Image],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output: list[Image.Image] = []
    for current_frame, revised_frame in zip(current, revised, strict=True):
        board = Image.new("RGBA", (size * 2 + gap, size * 2 + gap), common.TRANSPARENT)
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
        export_item(item_id, items[item_id], durations[item_id])
        for item_id in pack_v2.ITEM_ORDER
    ]

    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_durations = [100] * 21
    pack_v2.save_gif(
        pack_v2.board_frames(items, durations, size=144, gap=8),
        review_dir / "unlabeled-pack-review-light-dark.gif",
        review_durations,
    )
    pack_v2.save_gif(
        pack_v2.board_frames(items, durations, size=50, gap=8),
        review_dir / "unlabeled-pack-review-50-light-dark.gif",
        review_durations,
    )
    pack_v2.contact_sheet(items, background=common.LIGHT_BACKGROUND).save(
        review_dir / "frame-contact-sheet-light.png"
    )
    pack_v2.contact_sheet(items, background=common.DARK_BACKGROUND).save(
        review_dir / "frame-contact-sheet-dark.png"
    )
    pack_v2.save_gif(
        meeting_comparison_frames(
            pack_v2.render_meeting(layers),
            items["s04-meeting"],
            size=288,
            gap=16,
        ),
        review_dir / "meeting-v2-v3-comparison-light-dark.gif",
        pack_v2.STANDARD_DURATIONS,
    )
    (review_dir / "order.md").write_text(
        "# 无标签审阅顺序\n\n"
        "九张总览：左侧 3x3 为浅色，右侧 3x3 为深色，顺序为 S01-S09。\n\n"
        "耳机对照：左列为当前 v2，右列为等大耳罩 v3；上行为浅色，下行为深色。\n",
        encoding="utf-8",
    )

    manifest = {
        "status": "candidate_comparison",
        "pack_id": "work-reactions",
        "alternative_to": "work/v2",
        "change_scope": ["s04-meeting"],
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "item_order": pack_v2.ITEM_ORDER,
        "labels": pack_v2.LABELS,
        "items": manifest_items,
        "meeting_notes": {
            "ear_cups": "exact mirrored 3x7 cyan pads",
            "microphone": "attached from the cup's inner edge; full cup remains visible",
            "raised_hand": "moved outward with a four-pixel gap from the headset",
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
