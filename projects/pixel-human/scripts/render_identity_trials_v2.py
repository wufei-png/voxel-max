#!/usr/bin/env python3
"""Render revised v2 identity trials from the approved pixel-human master."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from PIL import Image

import render_identity_trials as common


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "identity" / "trials" / "v2"
TRIAL_ORDER = ["crashed", "received", "working"]
ROW_ORDER = ["received", "working", "crashed"]

FONT_3X5 = {
    "G": ("111", "100", "101", "101", "111"),
    "O": ("111", "101", "101", "101", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "I": ("111", "010", "010", "010", "111"),
    "!": ("010", "010", "010", "000", "010"),
}


def draw_text(image: Image.Image, text: str, x: int, y: int) -> None:
    cursor_x = x
    for character in text:
        glyph = FONT_3X5[character]
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    image.putpixel((cursor_x + column, y + row), common.HAIR)
        cursor_x += 4


def draw_speech_bubble(frame: Image.Image) -> None:
    common.rect(frame, (31, 6, 46, 22), common.HAIR)
    common.rect(frame, (32, 7, 45, 21), common.FACE)

    # A short filled tail points to the lower-right edge of the blank face.
    frame.putpixel((30, 19), common.HAIR)
    frame.putpixel((29, 20), common.HAIR)
    frame.putpixel((28, 21), common.HAIR)
    frame.putpixel((30, 18), common.FACE)
    frame.putpixel((29, 19), common.FACE)

    draw_text(frame, "GOT", 33, 8)
    draw_text(frame, "IT!", 33, 15)


def render_received(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    poses = [
        {"head_dy": 1},
        {},
        {"head_dy": -1, "neck_dy": -1},
        {"body_dy": -1},
        {"head_dy": 1},
    ]
    frames: list[Image.Image] = []
    for pose in poses:
        frame = common.compose_character(layers, base_x=6, **pose)
        draw_speech_bubble(frame)
        frames.append(frame)
    return frames


def render_working(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    # Preserve the accepted v1 typing animation frame-for-frame.
    return common.render_take_a_look(layers)


def draw_crash_pose(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    head_dy: int,
    body_dy: int,
    arm_state: int,
) -> Image.Image:
    head, _neck, body = layers
    frame = Image.new("RGBA", (48, 48), common.TRANSPARENT)
    frame.alpha_composite(body, (common.BASE_X, common.BASE_Y + 20 + body_dy))

    hand_states = {
        0: ((12, 35), (33, 35)),
        1: ((14, 34), (31, 34)),
        2: ((17, 31), (29, 31)),
        3: ((12, 35), (31, 34)),
    }
    left_hand, right_hand = hand_states[arm_state]
    common.rect(frame, (10, 32, 19, 37), common.PURPLE)
    common.rect(frame, (29, 32, 38, 37), common.PURPLE)
    common.rect(
        frame,
        (left_hand[0], left_hand[1], left_hand[0] + 3, left_hand[1] + 1),
        common.FACE,
    )
    common.rect(
        frame,
        (right_hand[0], right_hand[1], right_hand[0] + 3, right_hand[1] + 1),
        common.FACE,
    )

    # The lowered head is drawn over the shoulders; no neck is visible at collapse.
    frame.alpha_composite(head, (common.BASE_X, common.BASE_Y + head_dy))

    # A flat keyboard, rather than a glowing screen, keeps this distinct from working.
    common.rect(frame, (11, 37, 37, 42), common.HAIR)
    common.rect(frame, (12, 37, 36, 37), common.FX_BLUE_DARK)
    common.rect(frame, (13, 39, 35, 41), common.PURPLE_SHADOW)
    return frame


def render_crashed(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    poses = [
        {"head_dy": 10, "body_dy": 1, "arm_state": 0},
        {"head_dy": 7, "body_dy": 0, "arm_state": 1},
        {"head_dy": 4, "body_dy": 0, "arm_state": 2},
        {"head_dy": 8, "body_dy": 1, "arm_state": 3},
        {"head_dy": 10, "body_dy": 1, "arm_state": 0},
    ]
    return [draw_crash_pose(layers, **pose) for pose in poses]


def export_trial(
    trial_id: str,
    frames: list[Image.Image],
    *,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, object]:
    common.validate_frames(trial_id, frames)
    trial_dir = output_dir / trial_id
    frames_dir = trial_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    frame_paths: list[str] = []
    for index, frame in enumerate(frames):
        path = frames_dir / f"frame-{index:02d}.png"
        frame.save(path)
        frame_paths.append(str(path.relative_to(output_dir)))

    common.save_apng(frames, trial_dir / f"{trial_id}.apng")
    common.save_gif(
        common.scaled_frames(frames, 480),
        trial_dir / f"{trial_id}-review.gif",
    )
    common.save_gif(
        common.light_dark_frames(frames, 480, 16),
        trial_dir / f"{trial_id}-review-light-dark.gif",
    )
    common.save_gif(
        common.light_dark_frames(frames, 50, 8),
        trial_dir / f"{trial_id}-review-50-light-dark.gif",
    )
    return {
        "id": trial_id,
        "frame_paths": frame_paths,
        "durations_ms": common.FRAME_DURATIONS_MS,
        "distinct_poses": 4,
    }


def unlabeled_board_frames(
    trials: dict[str, list[Image.Image]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output: list[Image.Image] = []
    for frame_index in range(5):
        width = size * len(TRIAL_ORDER) + gap * (len(TRIAL_ORDER) - 1)
        board = Image.new("RGBA", (width, size * 2 + gap), common.TRANSPARENT)
        for column, trial_id in enumerate(TRIAL_ORDER):
            frame = trials[trial_id][frame_index].resize(
                (size, size), Image.Resampling.NEAREST
            )
            x = column * (size + gap)
            board.alpha_composite(
                common.on_background(frame, common.LIGHT_BACKGROUND),
                (x, 0),
            )
            board.alpha_composite(
                common.on_background(frame, common.DARK_BACKGROUND),
                (x, size + gap),
            )
        output.append(board)
    return output


def contact_sheet(
    trials: dict[str, list[Image.Image]],
    *,
    background: tuple[int, int, int, int],
    size: int = 192,
    gap: int = 8,
) -> Image.Image:
    width = size * 5 + gap * 4
    height = size * len(ROW_ORDER) + gap * (len(ROW_ORDER) - 1)
    sheet = Image.new("RGBA", (width, height), common.TRANSPARENT)
    for row, trial_id in enumerate(ROW_ORDER):
        for column, frame in enumerate(trials[trial_id]):
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            panel = common.on_background(scaled, background)
            sheet.alpha_composite(
                panel,
                (column * (size + gap), row * (size + gap)),
            )
    return sheet


def write_review_order(*, output_dir: Path = OUTPUT_DIR) -> None:
    labels = {"received": "收到", "working": "工作中", "crashed": "崩了"}
    lines = ["# 无标签审阅列顺序", ""]
    lines.extend(
        f"{index}. `{trial_id}`：{labels[trial_id]}"
        for index, trial_id in enumerate(TRIAL_ORDER, start=1)
    )
    lines.append("")
    (output_dir / "review" / "order.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    master = common.load_master()
    layers = common.split_master(master)
    renderers: dict[
        str,
        Callable[[tuple[Image.Image, Image.Image, Image.Image]], list[Image.Image]],
    ] = {
        "received": render_received,
        "working": render_working,
        "crashed": render_crashed,
    }
    trials = {trial_id: render(layers) for trial_id, render in renderers.items()}
    manifest_trials = [export_trial(trial_id, trials[trial_id]) for trial_id in renderers]

    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    common.save_gif(
        unlabeled_board_frames(trials, size=288, gap=16),
        review_dir / "unlabeled-review-light-dark.gif",
    )
    common.save_gif(
        unlabeled_board_frames(trials, size=50, gap=8),
        review_dir / "unlabeled-review-50-light-dark.gif",
    )
    contact_sheet(trials, background=common.LIGHT_BACKGROUND).save(
        review_dir / "frame-contact-sheet-light.png"
    )
    contact_sheet(trials, background=common.DARK_BACKGROUND).save(
        review_dir / "frame-contact-sheet-dark.png"
    )
    write_review_order()

    manifest = {
        "status": "superseded_by_v3",
        "superseded_by": "identity/trials/v3",
        "supersedes": "identity/trials/v1",
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "trial_order": TRIAL_ORDER,
        "trials": manifest_trials,
        "notes": {
            "received": "GOT / IT! speech bubble; no facial features",
            "working": "frame-for-frame reuse of v1 take-a-look",
            "crashed": "physical collapse onto a flat keyboard",
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
