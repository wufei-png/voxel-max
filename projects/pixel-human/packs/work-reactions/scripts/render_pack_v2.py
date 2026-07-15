#!/usr/bin/env python3
"""Render the revised nine-item work-reactions candidate set."""

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


PACK_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACK_DIR / "work" / "v2"
ITEM_ORDER = [
    "s01-received",
    "s02-working",
    "s03-wait",
    "s04-meeting",
    "s05-done",
    "s06-speechless",
    "s07-crashed",
    "s08-off-work",
    "s09-kowtow",
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
    "s09-kowtow": "磕头",
}
STANDARD_DURATIONS = [480, 120, 120, 120, 360]
DONE_DURATIONS = [260, 90, 90, 90, 120, 560]
OFF_WORK_DURATIONS = [400, 80, 80, 100, 100, 100, 100, 100, 120, 120, 180, 600]
KOWTOW_DURATIONS = [400, 100, 100, 100, 220, 100, 380]


def draw_headset(frame: Image.Image, *, hand_y: int, signal_on: bool) -> None:
    common.rect(frame, (16, 8, 32, 9), common.FX_BLUE_DARK)
    common.rect(frame, (14, 10, 16, 23), common.FX_BLUE_DARK)
    common.rect(frame, (14, 18, 16, 24), common.FX_BLUE)

    # The right cup is deliberately smaller because the microphone adds visual
    # mass on this side. A one-pixel gap keeps both parts readable.
    common.rect(frame, (32, 11, 33, 22), common.FX_BLUE_DARK)
    common.rect(frame, (32, 18, 33, 22), common.FX_BLUE)
    common.rect(frame, (35, 23, 35, 25), common.FX_BLUE_DARK)
    common.rect(frame, (34, 25, 35, 26), common.FX_BLUE_DARK)
    common.rect(
        frame,
        (32, 26, 34, 27),
        common.FX_BLUE if signal_on else common.FX_BLUE_DARK,
    )

    common.rect(frame, (37, 28, 40, 35), common.PURPLE)
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


CHECK_SEGMENTS = [
    (34, 14, 35, 15),
    (36, 16, 37, 17),
    (38, 14, 39, 15),
    (40, 12, 41, 13),
]


def draw_check(frame: Image.Image, *, segments: int) -> None:
    for box in CHECK_SEGMENTS[:segments]:
        common.rect(frame, box, common.FX_BLUE)


def render_done(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (4, -1)]
    frames: list[Image.Image] = []
    for segments, body_dy in states:
        frame = common.compose_character(
            layers,
            head_dy=body_dy,
            neck_dy=body_dy,
            body_dy=body_dy,
        )
        trial_v3.draw_flat_keyboard(frame)
        draw_check(frame, segments=segments)
        frames.append(frame)
    return frames


def draw_bow_hands(
    frame: Image.Image,
    *,
    left_x: int,
    right_x: int,
    hand_y: int,
) -> None:
    common.rect(frame, (10, 31, 19, 38), common.PURPLE)
    common.rect(frame, (29, 31, 38, 38), common.PURPLE)
    common.rect(frame, (left_x, hand_y, left_x + 4, hand_y + 2), common.FACE)
    common.rect(frame, (right_x, hand_y, right_x + 4, hand_y + 2), common.FACE)


def bow_pitch_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    crown_y: int,
    face_y: int,
) -> Image.Image:
    _head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 21))
    draw_bow_hands(frame, left_x=13, right_x=31, hand_y=36)
    common.rect(frame, (17, crown_y, 31, face_y - 1), common.HAIR)
    common.rect(frame, (19, face_y, 29, face_y + 3), common.FACE)
    return frame


def bow_down_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    impact: bool,
) -> Image.Image:
    _head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 22))
    draw_bow_hands(frame, left_x=12, right_x=32, hand_y=37)
    common.rect(frame, (17, 27, 31, 38), common.HAIR)
    if impact:
        common.rect(frame, (8, 35, 11, 36), common.NECK_SHADOW)
        common.rect(frame, (37, 35, 40, 36), common.NECK_SHADOW)
        common.rect(frame, (11, 32, 12, 33), common.NECK_SHADOW)
        common.rect(frame, (35, 32, 36, 33), common.NECK_SHADOW)
    return frame


def render_kowtow(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    bowed = bow_down_pose(layers, impact=True)
    upright = common.compose_character(layers, head_dy=1, body_dy=1)
    draw_bow_hands(upright, left_x=15, right_x=29, hand_y=35)
    prepare = common.compose_character(layers, head_dy=3, body_dy=1)
    draw_bow_hands(prepare, left_x=13, right_x=31, hand_y=36)
    pitch = bow_pitch_pose(layers, crown_y=21, face_y=32)
    lifted = bow_pitch_pose(layers, crown_y=23, face_y=34)
    return [bowed, upright, prepare, pitch, bowed.copy(), lifted, bowed.copy()]


GLYPHS = {
    "下": [
        "1111111111",
        "0000100000",
        "0000100000",
        "0000101000",
        "0000100100",
        "0000100010",
        "0000100000",
        "0000100000",
        "0000100000",
        "0000100000",
    ],
    "班": [
        "000000100000",
        "011110111110",
        "001000100100",
        "001000100100",
        "001001100100",
        "011110111110",
        "001000100100",
        "001000100100",
        "001101000100",
        "010001111111",
        "000010000000",
    ],
    "了": [
        "1111111110",
        "0000000100",
        "0000001000",
        "0000010000",
        "0000010000",
        "0000010000",
        "0000010000",
        "0000010000",
        "0000010000",
        "0001100000",
    ],
}


def draw_glyphs(frame: Image.Image, *, count: int) -> None:
    y = 2
    for character in "下班了"[:count]:
        rows = GLYPHS[character]
        for row, bits in enumerate(rows):
            for column, bit in enumerate(bits):
                if bit == "1":
                    frame.putpixel((1 + column, y + row), common.FX_BLUE)
        y += len(rows) + 1


def draw_chair(frame: Image.Image) -> None:
    common.rect(frame, (6, 28, 9, 41), common.HAIR)
    common.rect(frame, (7, 39, 24, 42), common.PURPLE_SHADOW)
    common.rect(frame, (9, 40, 26, 41), common.HAIR)


def draw_backpack(
    frame: Image.Image,
    *,
    base_x: int,
    base_y: int,
) -> None:
    common.rect(frame, (base_x + 1, base_y + 21, base_x + 7, base_y + 32), common.PURPLE_SHADOW)
    common.rect(frame, (base_x + 3, base_y + 18, base_x + 6, base_y + 20), common.HAIR)
    common.rect(frame, (base_x + 6, base_y + 20, base_x + 8, base_y + 27), common.FX_BLUE_DARK)


def render_off_work(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [
        (0, 0, False, 0),
        (0, -1, False, 0),
        (0, -2, False, 0),
        (0, -2, True, 0),
        (2, -2, True, 0),
        (4, -2, True, 1),
        (6, -2, True, 1),
        (8, -2, True, 2),
        (10, -2, True, 2),
        (12, -2, True, 3),
        (15, -2, True, 3),
        (18, -2, True, 3),
    ]
    frames: list[Image.Image] = []
    for shift, rise, backpack, glyph_count in states:
        frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
        draw_chair(frame)
        draw_glyphs(frame, count=glyph_count)
        base_x = common.BASE_X + shift
        base_y = common.BASE_Y + rise
        if backpack:
            draw_backpack(frame, base_x=base_x, base_y=base_y)
        character = common.compose_character(layers, base_x=base_x, base_y=base_y)
        frame.alpha_composite(character)
        frames.append(frame)
    return frames


def validate_item(
    item_id: str,
    frames: list[Image.Image],
    durations: list[int],
) -> None:
    if len(frames) != len(durations) or len(frames) < 2:
        raise ValueError(f"{item_id}: frame and duration count mismatch")
    if len({frame.tobytes() for frame in frames}) < 2:
        raise ValueError(f"{item_id}: animation has no movement")
    for frame in frames:
        if frame.size != (48, 48) or frame.mode != "RGBA":
            raise ValueError(f"{item_id}: invalid frame contract")
        alpha = frame.getchannel("A").histogram()
        if sum(alpha[1:255]) != 0:
            raise ValueError(f"{item_id}: alpha must be binary")


def save_gif(
    frames: list[Image.Image],
    path: Path,
    durations: list[int],
) -> None:
    paletted = common.rgba_to_palette(frames)
    paletted[0].save(
        path,
        save_all=True,
        append_images=paletted[1:],
        duration=durations,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False,
    )


def save_apng(
    frames: list[Image.Image],
    path: Path,
    durations: list[int],
) -> None:
    frames[0].save(
        path,
        format="PNG",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=0,
        blend=0,
    )


def export_item(
    item_id: str,
    frames: list[Image.Image],
    durations: list[int],
) -> dict[str, object]:
    validate_item(item_id, frames, durations)
    item_dir = OUTPUT_DIR / item_id
    frames_dir = item_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[str] = []
    for index, frame in enumerate(frames):
        path = frames_dir / f"frame-{index:02d}.png"
        frame.save(path)
        frame_paths.append(str(path.relative_to(OUTPUT_DIR)))
    save_apng(frames, item_dir / f"{item_id}.apng", durations)
    save_gif(
        common.scaled_frames(frames, 480),
        item_dir / f"{item_id}-review.gif",
        durations,
    )
    save_gif(
        common.light_dark_frames(frames, 480, 16),
        item_dir / f"{item_id}-review-light-dark.gif",
        durations,
    )
    save_gif(
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


def frame_at_time(
    frames: list[Image.Image],
    durations: list[int],
    time_ms: int,
) -> Image.Image:
    cursor = time_ms % sum(durations)
    elapsed = 0
    for frame, duration in zip(frames, durations, strict=True):
        elapsed += duration
        if cursor < elapsed:
            return frame
    return frames[-1]


def board_frames(
    items: dict[str, list[Image.Image]],
    durations: dict[str, list[int]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output: list[Image.Image] = []
    width = size * 6 + gap * 5
    height = size * 3 + gap * 2
    for time_ms in range(0, 2100, 100):
        board = Image.new("RGBA", (width, height), common.TRANSPARENT)
        for index, item_id in enumerate(ITEM_ORDER):
            row = index // 3
            column = index % 3
            frame = frame_at_time(items[item_id], durations[item_id], time_ms)
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            light_x = column * (size + gap)
            dark_x = (column + 3) * (size + gap)
            y = row * (size + gap)
            board.alpha_composite(
                common.on_background(scaled, common.LIGHT_BACKGROUND),
                (light_x, y),
            )
            board.alpha_composite(
                common.on_background(scaled, common.DARK_BACKGROUND),
                (dark_x, y),
            )
        output.append(board)
    return output


def contact_sheet(
    items: dict[str, list[Image.Image]],
    *,
    background: tuple[int, int, int, int],
    size: int = 64,
    gap: int = 4,
) -> Image.Image:
    columns = max(len(frames) for frames in items.values())
    width = size * columns + gap * (columns - 1)
    height = size * len(ITEM_ORDER) + gap * (len(ITEM_ORDER) - 1)
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
        "左侧 3x3 为浅色背景，右侧 3x3 以相同顺序重复为深色背景。",
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
        "s01-received": trial_v2.render_received(layers),
        "s02-working": trial_v2.render_working(layers),
        "s03-wait": pack_v1.render_wait(layers),
        "s04-meeting": render_meeting(layers),
        "s05-done": render_done(layers),
        "s06-speechless": pack_v1.render_speechless(layers),
        "s07-crashed": trial_v3.render_crashed(layers),
        "s08-off-work": render_off_work(layers),
        "s09-kowtow": render_kowtow(layers),
    }
    durations = {
        item_id: STANDARD_DURATIONS for item_id in ITEM_ORDER
    }
    durations["s05-done"] = DONE_DURATIONS
    durations["s08-off-work"] = OFF_WORK_DURATIONS
    durations["s09-kowtow"] = KOWTOW_DURATIONS

    manifest_items = [
        export_item(item_id, items[item_id], durations[item_id])
        for item_id in ITEM_ORDER
    ]
    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_durations = [100] * 21
    save_gif(
        board_frames(items, durations, size=144, gap=8),
        review_dir / "unlabeled-pack-review-light-dark.gif",
        review_durations,
    )
    save_gif(
        board_frames(items, durations, size=50, gap=8),
        review_dir / "unlabeled-pack-review-50-light-dark.gif",
        review_durations,
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
        "supersedes": "work/v1",
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "item_order": ITEM_ORDER,
        "labels": LABELS,
        "items": manifest_items,
        "approved_trial_reuse": {
            "s01-received": "identity/trials/v4/received",
            "s02-working": "identity/trials/v4/working",
            "s07-crashed": "identity/trials/v3/crashed",
            "s09-kowtow": "identity/trials/v4/crashed adapted without keyboard",
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
