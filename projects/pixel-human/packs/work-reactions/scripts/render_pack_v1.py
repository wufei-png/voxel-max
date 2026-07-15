#!/usr/bin/env python3
"""Render the first eight platform-neutral work-reactions candidates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[3]
PROJECT_SCRIPTS = PROJECT_DIR / "scripts"
if str(PROJECT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_SCRIPTS))

import render_identity_trials as common  # noqa: E402
import render_identity_trials_v2 as v2  # noqa: E402
import render_identity_trials_v3 as v3  # noqa: E402
import render_identity_trials_v4 as v4  # noqa: E402


PACK_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACK_DIR / "work" / "v1"
ITEM_ORDER = [
    "s01-received",
    "s02-working",
    "s03-wait",
    "s04-meeting",
    "s05-done",
    "s06-speechless",
    "s07-crashed",
    "s08-off-work",
]
LABELS = {
    "s01-received": "收到",
    "s02-working": "工作中",
    "s03-wait": "稍等",
    "s04-meeting": "开会中",
    "s05-done": "搞定了",
    "s06-speechless": "无语",
    "s07-crashed": "崩了",
    "s08-off-work": "下班了",
}


def draw_dots(
    frame: Image.Image,
    *,
    positions: list[tuple[int, int]],
    active: int,
    active_color: tuple[int, int, int, int],
    inactive_color: tuple[int, int, int, int],
) -> None:
    for index, (x, y) in enumerate(positions):
        color = active_color if index < active else inactive_color
        common.rect(frame, (x, y, x + 2, y + 2), color)


def render_wait(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(3, 0), (1, 1), (2, 1), (3, 1), (3, 0)]
    frames: list[Image.Image] = []
    for active, head_dy in states:
        frame = common.compose_character(layers, head_dy=head_dy)
        draw_dots(
            frame,
            positions=[(18, 2), (23, 2), (28, 2)],
            active=active,
            active_color=common.FX_BLUE,
            inactive_color=common.FX_BLUE_DARK,
        )
        frames.append(frame)
    return frames


def draw_headset(frame: Image.Image, *, hand_y: int, signal_on: bool) -> None:
    common.rect(frame, (16, 8, 32, 9), common.FX_BLUE_DARK)
    common.rect(frame, (14, 10, 16, 23), common.FX_BLUE_DARK)
    common.rect(frame, (32, 10, 34, 23), common.FX_BLUE_DARK)
    common.rect(frame, (14, 18, 17, 24), common.FX_BLUE)
    common.rect(frame, (31, 18, 34, 24), common.FX_BLUE)
    common.rect(frame, (34, 23, 36, 25), common.FX_BLUE_DARK)
    common.rect(frame, (32, 25, 36, 26), common.FX_BLUE_DARK)
    common.rect(
        frame,
        (31, 25, 33, 27),
        common.FX_BLUE if signal_on else common.FX_BLUE_DARK,
    )
    common.rect(frame, (36, 27, 40, 34), common.PURPLE)
    common.rect(frame, (37, hand_y, 40, hand_y + 4), common.FACE)


def render_meeting(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(20, True, 0), (18, True, 0), (19, False, 1), (21, True, 0), (20, True, 0)]
    frames: list[Image.Image] = []
    for hand_y, signal_on, head_dy in states:
        frame = common.compose_character(layers, head_dy=head_dy)
        draw_headset(frame, hand_y=hand_y, signal_on=signal_on)
        frames.append(frame)
    return frames


def draw_check(frame: Image.Image, *, state: int) -> None:
    pixels = [(34, 13), (35, 14), (36, 15), (37, 14), (38, 13), (39, 12)]
    visible = {0: 6, 1: 3, 2: 5, 3: 6}[state]
    for x, y in pixels[:visible]:
        common.rect(frame, (x, y, x + 1, y + 1), common.FX_BLUE)


def render_done(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(0, 0), (1, 1), (2, 0), (3, -1), (0, 0)]
    frames: list[Image.Image] = []
    for check_state, body_dy in states:
        frame = common.compose_character(
            layers,
            head_dy=body_dy,
            neck_dy=body_dy,
            body_dy=body_dy,
        )
        v3.draw_flat_keyboard(frame)
        draw_check(frame, state=check_state)
        frames.append(frame)
    return frames


def render_speechless(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(3, 1, 1), (1, 0, 0), (2, 1, 0), (3, 1, 0), (3, 1, 1)]
    frames: list[Image.Image] = []
    for active, head_dx, body_dy in states:
        frame = common.compose_character(
            layers,
            head_dx=head_dx,
            head_dy=1,
            body_dy=body_dy,
        )
        draw_dots(
            frame,
            positions=[(35, 16), (39, 16), (43, 16)],
            active=active,
            active_color=common.FACE,
            inactive_color=common.NECK_SHADOW,
        )
        frames.append(frame)
    return frames


def draw_waving_arm(frame: Image.Image, *, hand_y: int) -> None:
    common.rect(frame, (37, 25, 42, 35), common.PURPLE)
    common.rect(frame, (38, hand_y, 42, hand_y + 4), common.FACE)


def render_off_work(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(4, 18), (1, 20), (2, 17), (5, 19), (4, 18)]
    frames: list[Image.Image] = []
    for shift, hand_y in states:
        frame = common.compose_character(
            layers,
            base_x=common.BASE_X + shift,
        )
        draw_waving_arm(frame, hand_y=hand_y)
        common.rect(frame, (4, 31, 8 + shift, 32), common.FX_BLUE_DARK)
        frames.append(frame)
    return frames


def board_frames(
    items: dict[str, list[Image.Image]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output: list[Image.Image] = []
    width = size * 4 + gap * 3
    height = size * 4 + gap * 3
    for frame_index in range(5):
        board = Image.new("RGBA", (width, height), common.TRANSPARENT)
        for index, item_id in enumerate(ITEM_ORDER):
            column = index % 4
            row = index // 4
            scaled = items[item_id][frame_index].resize(
                (size, size), Image.Resampling.NEAREST
            )
            x = column * (size + gap)
            light_y = row * (size + gap)
            dark_y = (row + 2) * (size + gap)
            board.alpha_composite(
                common.on_background(scaled, common.LIGHT_BACKGROUND),
                (x, light_y),
            )
            board.alpha_composite(
                common.on_background(scaled, common.DARK_BACKGROUND),
                (x, dark_y),
            )
        output.append(board)
    return output


def contact_sheet(
    items: dict[str, list[Image.Image]],
    *,
    background: tuple[int, int, int, int],
    size: int = 96,
    gap: int = 8,
) -> Image.Image:
    width = size * 5 + gap * 4
    height = size * 8 + gap * 7
    sheet = Image.new("RGBA", (width, height), common.TRANSPARENT)
    for row, item_id in enumerate(ITEM_ORDER):
        for column, frame in enumerate(items[item_id]):
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            panel = common.on_background(scaled, background)
            sheet.alpha_composite(
                panel,
                (column * (size + gap), row * (size + gap)),
            )
    return sheet


def write_order() -> None:
    lines = [
        "# 无标签审阅顺序",
        "",
        "八宫格从左到右、从上到下；上半为浅色背景，下半重复同一顺序为深色背景。",
        "",
    ]
    lines.extend(
        f"{index}. `{item_id}`：{LABELS[item_id]}"
        for index, item_id in enumerate(ITEM_ORDER, start=1)
    )
    lines.append("")
    (OUTPUT_DIR / "review" / "order.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> None:
    master = common.load_master()
    layers = common.split_master(master)
    items = {
        "s01-received": v2.render_received(layers),
        "s02-working": v2.render_working(layers),
        "s03-wait": render_wait(layers),
        "s04-meeting": render_meeting(layers),
        "s05-done": render_done(layers),
        "s06-speechless": render_speechless(layers),
        "s07-crashed": v4.render_crashed(layers),
        "s08-off-work": render_off_work(layers),
    }
    manifest_items = [
        v2.export_trial(item_id, items[item_id], output_dir=OUTPUT_DIR)
        for item_id in ITEM_ORDER
    ]

    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    common.save_gif(
        board_frames(items, size=144, gap=8),
        review_dir / "unlabeled-pack-review-light-dark.gif",
    )
    common.save_gif(
        board_frames(items, size=50, gap=8),
        review_dir / "unlabeled-pack-review-50-light-dark.gif",
    )
    contact_sheet(items, background=common.LIGHT_BACKGROUND).save(
        review_dir / "frame-contact-sheet-light.png"
    )
    contact_sheet(items, background=common.DARK_BACKGROUND).save(
        review_dir / "frame-contact-sheet-dark.png"
    )
    write_order()

    manifest = {
        "status": "candidate_review",
        "pack_id": "work-reactions",
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "item_order": ITEM_ORDER,
        "labels": LABELS,
        "items": manifest_items,
        "approved_trial_reuse": {
            "s01-received": "identity/trials/v4/received",
            "s02-working": "identity/trials/v4/working",
            "s07-crashed": "identity/trials/v4/crashed",
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
