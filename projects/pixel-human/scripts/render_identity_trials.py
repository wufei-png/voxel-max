#!/usr/bin/env python3
"""Render three deterministic 48 px identity animation trials from master v1."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[1]
MASTER_PATH = PROJECT_DIR / "identity" / "masters" / "master-v1-32.png"
OUTPUT_DIR = PROJECT_DIR / "identity" / "trials" / "v1"
EXPECTED_MASTER_SHA256 = (
    "c7d0e4f83d6816231bd3d36109c291164e142159dc14cfdedd924fe1a96ec6ed"
)

TRANSPARENT = (0, 0, 0, 0)
HAIR = (18, 16, 22, 255)
FACE = (246, 239, 203, 255)
NECK_SHADOW = (221, 211, 158, 255)
PURPLE = (130, 71, 157, 255)
PURPLE_SHADOW = (100, 53, 121, 255)
FX_BLUE = (91, 185, 200, 255)
FX_BLUE_DARK = (49, 113, 128, 255)

LIGHT_BACKGROUND = (242, 241, 235, 255)
DARK_BACKGROUND = (23, 23, 29, 255)

FRAME_DURATIONS_MS = [480, 120, 120, 120, 360]
TRIAL_ORDER = ["stuck", "received", "take-a-look"]
BASE_X = 8
BASE_Y = 7


def rect(
    image: Image.Image,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int, int],
) -> None:
    """Draw an inclusive integer-aligned rectangle."""
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            image.putpixel((x, y), color)


def load_master() -> Image.Image:
    digest = hashlib.sha256(MASTER_PATH.read_bytes()).hexdigest()
    if digest != EXPECTED_MASTER_SHA256:
        raise ValueError(f"approved master hash mismatch: {digest}")
    master = Image.open(MASTER_PATH).convert("RGBA")
    if master.size != (32, 32):
        raise ValueError(f"approved master must be 32x32, got {master.size}")
    return master


def split_master(master: Image.Image) -> tuple[Image.Image, Image.Image, Image.Image]:
    """Split the approved master into fixed head, neck, and body layers."""
    return (
        master.crop((0, 0, 32, 18)),
        master.crop((0, 18, 32, 20)),
        master.crop((0, 20, 32, 32)),
    )


def compose_character(
    layers: tuple[Image.Image, Image.Image, Image.Image],
    *,
    head_dx: int = 0,
    head_dy: int = 0,
    neck_dx: int = 0,
    neck_dy: int = 0,
    body_dx: int = 0,
    body_dy: int = 0,
    base_x: int = BASE_X,
    base_y: int = BASE_Y,
) -> Image.Image:
    head, neck, body = layers
    frame = Image.new("RGBA", (48, 48), TRANSPARENT)
    frame.alpha_composite(head, (base_x + head_dx, base_y + head_dy))
    frame.alpha_composite(
        neck,
        (base_x + neck_dx, base_y + 18 + neck_dy),
    )
    frame.alpha_composite(
        body,
        (base_x + body_dx, base_y + 20 + body_dy),
    )
    return frame


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
    return [compose_character(layers, **pose) for pose in poses]


def draw_screen_pose(frame: Image.Image, state: int) -> None:
    """Add block forearms, hands, and one compact screen edge."""
    hand_states = [((18, 33), (29, 34)), ((18, 34), (29, 34)), ((18, 32), (29, 34)), ((18, 34), (29, 32))]
    cursor_x = [17, 21, 25, 29][state]
    left_hand, right_hand = hand_states[state]

    rect(frame, (16, 30, 20, 35), PURPLE)
    rect(frame, (28, 30, 32, 35), PURPLE)
    rect(frame, (14, 35, 34, 42), HAIR)
    rect(frame, (14, 35, 34, 35), FX_BLUE_DARK)
    rect(frame, (16, 37, 32, 40), PURPLE_SHADOW)
    rect(frame, (cursor_x, 37, min(cursor_x + 2, 32), 37), FX_BLUE)

    rect(frame, (left_hand[0], left_hand[1], left_hand[0] + 2, left_hand[1] + 1), FACE)
    rect(frame, (right_hand[0], right_hand[1], right_hand[0] + 2, right_hand[1] + 1), FACE)


def render_take_a_look(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    states = [0, 1, 2, 3, 0]
    frames: list[Image.Image] = []
    for state in states:
        frame = compose_character(layers, head_dy=1 if state != 1 else 0)
        draw_screen_pose(frame, state)
        frames.append(frame)
    return frames


def draw_sweat(frame: Image.Image, state: int) -> None:
    shapes = {
        0: [(35, 14), (34, 15), (35, 15), (34, 16), (34, 17)],
        1: [(35, 15), (34, 16), (35, 16), (34, 17)],
        2: [(35, 14), (34, 15), (35, 15), (34, 16), (35, 17)],
        3: [(35, 15), (34, 16), (35, 16), (35, 17), (34, 18)],
    }
    for point in shapes[state]:
        frame.putpixel(point, FX_BLUE)


def render_stuck(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> list[Image.Image]:
    poses = [
        ({"head_dx": 1, "body_dx": -1, "body_dy": -1}, 0),
        ({"body_dy": -1}, 1),
        ({"head_dx": 1, "body_dy": -1}, 2),
        ({"body_dx": -1}, 3),
        ({"head_dx": 1, "body_dx": -1, "body_dy": -1}, 0),
    ]
    frames: list[Image.Image] = []
    for pose, sweat_state in poses:
        frame = compose_character(layers, **pose)
        draw_sweat(frame, sweat_state)
        frames.append(frame)
    return frames


def rgba_to_palette(frames: Iterable[Image.Image]) -> list[Image.Image]:
    frame_list = list(frames)
    colors = sorted(
        {
            pixel
            for frame in frame_list
            for pixel in frame.get_flattened_data()
            if pixel[3] != 0
        }
    )
    if len(colors) > 255:
        raise ValueError(f"GIF palette overflow: {len(colors)} colors")
    palette_colors = [TRANSPARENT, *colors]
    color_to_index = {color: index for index, color in enumerate(palette_colors)}
    flat_palette: list[int] = []
    for color in palette_colors:
        flat_palette.extend(color[:3])
    flat_palette.extend([0] * (768 - len(flat_palette)))

    converted: list[Image.Image] = []
    for frame in frame_list:
        image = Image.new("P", frame.size, 0)
        image.putpalette(flat_palette)
        indices = [
            0 if pixel[3] == 0 else color_to_index[pixel]
            for pixel in frame.get_flattened_data()
        ]
        image.putdata(indices)
        image.info["transparency"] = 0
        converted.append(image)
    return converted


def save_gif(frames: list[Image.Image], path: Path) -> None:
    paletted = rgba_to_palette(frames)
    paletted[0].save(
        path,
        save_all=True,
        append_images=paletted[1:],
        duration=FRAME_DURATIONS_MS,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False,
    )


def save_apng(frames: list[Image.Image], path: Path) -> None:
    frames[0].save(
        path,
        format="PNG",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATIONS_MS,
        loop=0,
        disposal=0,
        blend=0,
    )


def scaled_frames(frames: list[Image.Image], size: int) -> list[Image.Image]:
    return [frame.resize((size, size), Image.Resampling.NEAREST) for frame in frames]


def on_background(
    frame: Image.Image,
    background: tuple[int, int, int, int],
) -> Image.Image:
    panel = Image.new("RGBA", frame.size, background)
    panel.alpha_composite(frame)
    return panel


def light_dark_frames(frames: list[Image.Image], size: int, gap: int) -> list[Image.Image]:
    scaled = scaled_frames(frames, size)
    output: list[Image.Image] = []
    for frame in scaled:
        board = Image.new("RGBA", (size * 2 + gap, size), TRANSPARENT)
        board.alpha_composite(on_background(frame, LIGHT_BACKGROUND), (0, 0))
        board.alpha_composite(on_background(frame, DARK_BACKGROUND), (size + gap, 0))
        output.append(board)
    return output


def validate_frames(trial_id: str, frames: list[Image.Image]) -> None:
    if len(frames) != 5:
        raise ValueError(f"{trial_id}: expected 5 frames")
    if len({frame.tobytes() for frame in frames}) != 4:
        raise ValueError(f"{trial_id}: expected exactly 4 distinct poses")
    for frame in frames:
        if frame.size != (48, 48) or frame.mode != "RGBA":
            raise ValueError(f"{trial_id}: invalid frame contract")
        if {pixel[3] for pixel in frame.get_flattened_data()} != {0, 255}:
            raise ValueError(f"{trial_id}: alpha must be binary")


def export_trial(trial_id: str, frames: list[Image.Image]) -> dict[str, object]:
    validate_frames(trial_id, frames)
    trial_dir = OUTPUT_DIR / trial_id
    frames_dir = trial_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    frame_paths: list[str] = []
    for index, frame in enumerate(frames):
        frame_path = frames_dir / f"frame-{index:02d}.png"
        frame.save(frame_path)
        frame_paths.append(str(frame_path.relative_to(OUTPUT_DIR)))

    save_apng(frames, trial_dir / f"{trial_id}.apng")
    save_gif(scaled_frames(frames, 480), trial_dir / f"{trial_id}-review.gif")
    save_gif(
        light_dark_frames(frames, 480, 16),
        trial_dir / f"{trial_id}-review-light-dark.gif",
    )
    save_gif(
        light_dark_frames(frames, 50, 8),
        trial_dir / f"{trial_id}-review-50-light-dark.gif",
    )

    return {
        "id": trial_id,
        "frame_paths": frame_paths,
        "durations_ms": FRAME_DURATIONS_MS,
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
        board = Image.new("RGBA", (width, size * 2 + gap), TRANSPARENT)
        for column, trial_id in enumerate(TRIAL_ORDER):
            frame = trials[trial_id][frame_index].resize(
                (size, size), Image.Resampling.NEAREST
            )
            x = column * (size + gap)
            board.alpha_composite(on_background(frame, LIGHT_BACKGROUND), (x, 0))
            board.alpha_composite(
                on_background(frame, DARK_BACKGROUND),
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
    """Place all five poses in rows: received, take-a-look, then stuck."""
    row_order = ["received", "take-a-look", "stuck"]
    width = size * 5 + gap * 4
    height = size * len(row_order) + gap * (len(row_order) - 1)
    sheet = Image.new("RGBA", (width, height), TRANSPARENT)
    for row, trial_id in enumerate(row_order):
        for column, frame in enumerate(trials[trial_id]):
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            panel = on_background(scaled, background)
            sheet.alpha_composite(panel, (column * (size + gap), row * (size + gap)))
    return sheet


def write_order_file() -> None:
    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    labels = {
        "received": "收到",
        "take-a-look": "我看一下",
        "stuck": "卡住了",
    }
    lines = ["# 无标签审阅列顺序", ""]
    lines.extend(
        f"{index}. `{trial_id}`：{labels[trial_id]}"
        for index, trial_id in enumerate(TRIAL_ORDER, start=1)
    )
    lines.append("")
    (review_dir / "order.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    master = load_master()
    layers = split_master(master)
    renderers: dict[
        str,
        Callable[[tuple[Image.Image, Image.Image, Image.Image]], list[Image.Image]],
    ] = {
        "received": render_received,
        "take-a-look": render_take_a_look,
        "stuck": render_stuck,
    }
    trials = {trial_id: render(layers) for trial_id, render in renderers.items()}
    manifest_trials = [export_trial(trial_id, trials[trial_id]) for trial_id in renderers]

    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    save_gif(
        unlabeled_board_frames(trials, size=288, gap=16),
        review_dir / "unlabeled-review-light-dark.gif",
    )
    save_gif(
        unlabeled_board_frames(trials, size=50, gap=8),
        review_dir / "unlabeled-review-50-light-dark.gif",
    )
    contact_sheet(trials, background=LIGHT_BACKGROUND).save(
        review_dir / "frame-contact-sheet-light.png"
    )
    contact_sheet(trials, background=DARK_BACKGROUND).save(
        review_dir / "frame-contact-sheet-dark.png"
    )
    write_order_file()

    manifest = {
        "status": "candidate_review",
        "master_path": str(MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": EXPECTED_MASTER_SHA256,
        "canvas": [48, 48],
        "trial_order": TRIAL_ORDER,
        "trials": manifest_trials,
        "identity_colors": [HAIR, FACE, NECK_SHADOW, PURPLE, PURPLE_SHADOW],
        "trial_effect_colors": [FX_BLUE, FX_BLUE_DARK],
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for trial in manifest_trials:
        print(OUTPUT_DIR / str(trial["id"]))


if __name__ == "__main__":
    main()
