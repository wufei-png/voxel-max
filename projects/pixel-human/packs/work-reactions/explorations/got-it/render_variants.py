#!/usr/bin/env python3
"""Render deterministic GOT IT speech-bubble explorations for pixel-human."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
PROJECT_DIR = Path(__file__).resolve().parents[4]
PROJECT_SCRIPTS = PROJECT_DIR / "scripts"
if str(PROJECT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_SCRIPTS))

import render_identity_trials as common  # noqa: E402
import render_identity_trials_v2 as trial_v2  # noqa: E402


CANDIDATES_DIR = ROOT / "candidates"
REVIEW_DIR = ROOT / "review"
VARIANT_ORDER = [
    "v01-chamfer-typewriter",
    "v02-split-word-chips",
    "v03-comic-burst",
    "v04-slide-caption",
    "v05-chat-card",
    "v06-right-linked-chat-card",
    "v07-original-distance-chat-card",
]

FONT_3X5 = {
    "G": ("111", "100", "101", "101", "111"),
    "O": ("111", "101", "101", "101", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "I": ("111", "010", "010", "010", "111"),
    "!": ("010", "010", "010", "000", "010"),
    " ": ("000", "000", "000", "000", "000"),
}

LIGHT_BG = common.LIGHT_BACKGROUND
DARK_BG = common.DARK_BACKGROUND


def draw_text(
    image: Image.Image,
    text: str,
    x: int,
    y: int,
    *,
    color: tuple[int, int, int, int] = common.HAIR,
) -> None:
    """Draw the pack's deliberately tiny hard-edged 3x5 lettering."""
    cursor_x = x
    for character in text:
        for row, bits in enumerate(FONT_3X5[character]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    image.putpixel((cursor_x + column, y + row), color)
        cursor_x += 4


def polygon(
    image: Image.Image,
    points: list[tuple[int, int]],
    color: tuple[int, int, int, int],
) -> None:
    ImageDraw.Draw(image).polygon(points, fill=color)


def chamfer_box(
    frame: Image.Image,
    box: tuple[int, int, int, int],
    *,
    outline: tuple[int, int, int, int],
    fill: tuple[int, int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    polygon(
        frame,
        [(x0 + 2, y0), (x1 - 2, y0), (x1, y0 + 2), (x1, y1 - 2),
         (x1 - 2, y1), (x0 + 2, y1), (x0, y1 - 2), (x0, y0 + 2)],
        outline,
    )
    polygon(
        frame,
        [(x0 + 2, y0 + 1), (x1 - 2, y0 + 1), (x1 - 1, y0 + 2),
         (x1 - 1, y1 - 2), (x1 - 2, y1 - 1), (x0 + 2, y1 - 1),
         (x0 + 1, y1 - 2), (x0 + 1, y0 + 2)],
        fill,
    )


def draw_chamfer_speech(frame: Image.Image, *, reveal: int, compact: bool) -> None:
    """A conventional balloon with a one-character-at-a-time reveal."""
    if compact:
        # The entrance grows outward from the speaking side; even this seed has a tail.
        chamfer_box(frame, (39, 9, 47, 18), outline=common.HAIR, fill=common.FACE)
        polygon(frame, [(40, 16), (40, 19), (27, 23)], common.HAIR)
        polygon(frame, [(40, 17), (39, 18), (29, 21)], common.FACE)
        return

    chamfer_box(frame, (30, 2, 47, 21), outline=common.HAIR, fill=common.FACE)
    polygon(frame, [(31, 16), (31, 21), (25, 23), (29, 16)], common.HAIR)
    polygon(frame, [(31, 17), (31, 19), (27, 21), (30, 17)], common.FACE)
    visible = "GOTIT!"[:reveal]
    draw_text(frame, visible[:3], 33, 5)
    draw_text(frame, visible[3:], 33, 13)


def render_chamfer_typewriter(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[list[Image.Image], list[int]]:
    states = [
        (0, True, 1),
        (0, False, 0),
        (1, False, 0),
        (2, False, -1),
        (3, False, 0),
        (4, False, 0),
        (5, False, 0),
        (6, False, 1),
    ]
    frames = []
    for reveal, compact, head_dy in states:
        frame = common.compose_character(layers, base_x=6, head_dy=head_dy)
        draw_chamfer_speech(frame, reveal=reveal, compact=compact)
        frames.append(frame)
    return frames, [100, 100, 80, 80, 100, 100, 140, 560]


def draw_chip(
    frame: Image.Image,
    box: tuple[int, int, int, int],
    *,
    text: str,
    text_x: int,
    text_y: int,
) -> None:
    x0, y0, x1, y1 = box
    common.rect(frame, box, common.FX_BLUE_DARK)
    common.rect(frame, (x0 + 1, y0 + 1, x1 - 1, y1 - 1), common.FACE)
    common.rect(frame, (x0, y0, x0, y1), common.FX_BLUE)
    draw_text(frame, text, text_x, text_y)


def draw_split_word_chips(frame: Image.Image, *, stage: int) -> None:
    """Two independent word chips arrive in sequence from the character."""
    if stage == 0:
        common.rect(frame, (41, 4, 47, 10), common.FX_BLUE_DARK)
        polygon(frame, [(41, 8), (41, 11), (27, 21)], common.FX_BLUE_DARK)
        return

    draw_chip(frame, (30, 2, 47, 10), text="GOT", text_x=33, text_y=4)
    if stage == 1:
        polygon(frame, [(31, 8), (31, 12), (27, 20)], common.FX_BLUE_DARK)
        polygon(frame, [(32, 9), (32, 11), (29, 18)], common.FACE)
        return

    if stage == 2:
        common.rect(frame, (40, 13, 47, 20), common.FX_BLUE_DARK)
        polygon(frame, [(41, 18), (41, 21), (27, 23)], common.FX_BLUE_DARK)
        return

    draw_chip(
        frame,
        (30, 12, 47, 21),
        text="IT" if stage == 3 else "IT!",
        text_x=33,
        text_y=14,
    )
    polygon(frame, [(31, 17), (31, 22), (25, 23), (29, 17)], common.FX_BLUE_DARK)
    polygon(frame, [(31, 18), (31, 20), (27, 21), (30, 18)], common.FACE)


def render_split_word_chips(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[list[Image.Image], list[int]]:
    states = [(0, 1), (1, 0), (2, -1), (3, 0), (4, 0), (4, 1)]
    frames = []
    for stage, head_dy in states:
        frame = common.compose_character(layers, base_x=6, head_dy=head_dy)
        draw_split_word_chips(frame, stage=stage)
        frames.append(frame)
    return frames, [100, 180, 100, 150, 220, 600]


def burst_shapes(size: int) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    if size == 0:
        return (
            [(36, 10), (40, 12), (45, 11), (44, 16), (47, 20), (40, 19),
             (35, 22), (36, 17), (27, 23), (34, 14)],
            [(37, 12), (40, 13), (43, 12), (43, 16), (45, 19), (40, 18),
             (37, 20), (37, 16), (30, 21), (36, 14)],
        )
    if size == 1:
        return (
            [(30, 5), (36, 7), (40, 3), (42, 8), (47, 7), (45, 13),
             (48, 17), (43, 18), (44, 23), (37, 20), (31, 23), (32, 18),
             (24, 22), (29, 15), (26, 11), (31, 10)],
            [(31, 7), (36, 8), (40, 5), (41, 10), (45, 9), (43, 13),
             (46, 16), (41, 17), (42, 21), (37, 18), (32, 21), (33, 16),
             (27, 20), (31, 14), (29, 12), (33, 11)],
        )
    return (
        [(27, 1), (34, 4), (38, 0), (41, 5), (47, 3), (45, 10),
         (48, 13), (44, 17), (47, 22), (40, 21), (37, 25), (33, 21),
         (25, 24), (28, 18), (22, 20), (27, 13), (24, 9), (30, 8)],
        [(29, 4), (34, 6), (38, 3), (40, 7), (45, 6), (43, 11),
         (46, 13), (42, 16), (44, 20), (39, 19), (37, 22), (33, 19),
         (28, 22), (30, 17), (25, 19), (29, 13), (27, 10), (32, 10)],
    )


def draw_comic_burst(frame: Image.Image, *, size: int, words: int) -> None:
    outer, inner = burst_shapes(size)
    polygon(frame, outer, common.HAIR)
    polygon(frame, inner, common.FACE)
    # The long lower-left spike is the speech tail, not a decorative ray.
    if size == 2:
        polygon(frame, [(29, 15), (30, 20), (23, 23)], common.HAIR)
        polygon(frame, [(30, 16), (30, 18), (25, 21)], common.FACE)
    if words >= 1 and size == 2:
        draw_text(frame, "GOT", 33, 6)
    if words >= 2 and size == 2:
        draw_text(frame, "IT!", 33, 14)


def render_comic_burst(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[list[Image.Image], list[int]]:
    states = [(0, 0, 1), (1, 0, 0), (2, 0, -1), (2, 1, 0), (2, 2, 0), (2, 2, 1)]
    frames = []
    for size, words, head_dy in states:
        frame = common.compose_character(layers, base_x=4, head_dy=head_dy)
        draw_comic_burst(frame, size=size, words=words)
        frames.append(frame)
    return frames, [90, 100, 110, 160, 240, 620]


def draw_slide_caption(frame: Image.Image, *, width: int, reveal: int) -> None:
    """A horizontal dialog rail expands from the tail before text types in."""
    anchor_x = 29
    x0 = max(2, anchor_x - width)
    x1 = min(46, anchor_x + max(3, width // 3))
    common.rect(frame, (x0, 1, x1, 11), common.FX_BLUE_DARK)
    common.rect(frame, (x0 + 1, 2, x1 - 1, 10), common.FACE)
    common.rect(frame, (x0 + 2, 1, min(x0 + 5, x1), 1), common.FX_BLUE)
    polygon(frame, [(27, 11), (33, 11), (28, 16)], common.FX_BLUE_DARK)
    polygon(frame, [(28, 11), (31, 11), (28, 14)], common.FACE)
    if width >= 27:
        draw_text(frame, "GOT IT!"[:reveal], 4, 4)


def render_slide_caption(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[list[Image.Image], list[int]]:
    states = [
        (5, 0, 1),
        (12, 0, 0),
        (20, 0, -1),
        (27, 3, 0),
        (27, 5, 0),
        (27, 7, 0),
        (27, 7, 1),
    ]
    frames = []
    for width, reveal, head_dy in states:
        frame = common.compose_character(layers, head_dy=head_dy)
        draw_slide_caption(frame, width=width, reveal=reveal)
        frames.append(frame)
    return frames, [80, 80, 100, 140, 140, 200, 580]


def draw_chat_card(frame: Image.Image, *, dots: int, words: int, short: bool) -> None:
    """A left-side messenger card transitions from typing dots into the reply."""
    if short:
        common.rect(frame, (13, 9, 20, 18), common.PURPLE_SHADOW)
        common.rect(frame, (12, 8, 19, 17), common.FACE)
        polygon(frame, [(18, 14), (22, 18), (18, 18)], common.HAIR)
        return

    common.rect(frame, (3, 5, 21, 24), common.PURPLE_SHADOW)
    common.rect(frame, (1, 3, 19, 22), common.HAIR)
    common.rect(frame, (2, 4, 18, 21), common.FACE)
    common.rect(frame, (2, 4, 18, 5), common.FX_BLUE)
    polygon(frame, [(18, 15), (23, 19), (18, 20)], common.HAIR)
    polygon(frame, [(18, 16), (21, 19), (18, 19)], common.FACE)
    if words == 0:
        for index in range(dots):
            common.rect(frame, (5 + index * 4, 13, 6 + index * 4, 14), common.FX_BLUE_DARK)
    else:
        draw_text(frame, "GOT", 4, 7)
        if words >= 2:
            draw_text(frame, "IT!", 4, 15)


def render_chat_card(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[list[Image.Image], list[int]]:
    states = [
        (0, 0, True, 1),
        (1, 0, False, 0),
        (2, 0, False, -1),
        (3, 0, False, 0),
        (0, 1, False, 0),
        (0, 2, False, 1),
    ]
    frames = []
    for dots, words, short, head_dy in states:
        frame = common.compose_character(layers, base_x=13, head_dy=head_dy)
        draw_chat_card(frame, dots=dots, words=words, short=short)
        frames.append(frame)
    return frames, [90, 110, 110, 180, 220, 620]


def draw_right_linked_chat_card(
    frame: Image.Image,
    *,
    dots: int,
    reveal: int,
) -> None:
    """Combine the original right bubble and pixel tail with v05 card layers."""
    # V05-style offset layer, kept behind the original black main border.
    common.rect(frame, (32, 7, 47, 23), common.PURPLE_SHADOW)
    common.rect(frame, (30, 5, 46, 21), common.HAIR)
    common.rect(frame, (31, 6, 45, 20), common.FACE)
    common.rect(frame, (31, 6, 45, 7), common.FX_BLUE)

    # A stepped two-tone pixel line retains the original character-to-box link.
    for point in [(27, 22), (28, 21), (29, 20), (30, 19)]:
        frame.putpixel(point, common.HAIR)
    for point in [(28, 22), (29, 21), (30, 20)]:
        frame.putpixel(point, common.FACE)

    if reveal == 0:
        for index in range(dots):
            common.rect(
                frame,
                (33 + index * 4, 12, 34 + index * 4, 13),
                common.FX_BLUE_DARK,
            )
        return

    visible = "GOTIT!"[:reveal]
    draw_text(frame, visible[:3], 33, 8)
    draw_text(frame, visible[3:], 33, 15)


def render_right_linked_chat_card(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[list[Image.Image], list[int]]:
    states = [
        (1, 0, 1),
        (2, 0, 0),
        (3, 0, -1),
        (0, 3, 0),
        (0, 4, 0),
        (0, 6, 0),
        (0, 6, 1),
    ]
    frames = []
    for dots, reveal, head_dy in states:
        frame = common.compose_character(layers, base_x=6, head_dy=head_dy)
        draw_right_linked_chat_card(frame, dots=dots, reveal=reveal)
        frames.append(frame)
    return frames, [100, 100, 160, 160, 140, 240, 620]


def draw_original_distance_chat_card(
    frame: Image.Image,
    *,
    dots: int,
    reveal: int,
) -> None:
    """Use the original box and tail coordinates with v05 card styling."""
    # Offset layer remains behind the exact original outer box (31,6)-(46,22).
    common.rect(frame, (33, 8, 47, 23), common.PURPLE_SHADOW)
    common.rect(frame, (31, 6, 46, 22), common.HAIR)
    common.rect(frame, (32, 7, 45, 21), common.FACE)
    common.rect(frame, (32, 7, 45, 8), common.FX_BLUE)

    # Exact original tail pixels preserve the original head-to-box distance.
    frame.putpixel((30, 19), common.HAIR)
    frame.putpixel((29, 20), common.HAIR)
    frame.putpixel((28, 21), common.HAIR)
    frame.putpixel((30, 18), common.FACE)
    frame.putpixel((29, 19), common.FACE)

    if reveal == 0:
        for index in range(dots):
            common.rect(
                frame,
                (33 + index * 4, 12, 34 + index * 4, 13),
                common.FX_BLUE_DARK,
            )
        return
    visible = "GOTIT!"[:reveal]
    draw_text(frame, visible[:3], 33, 9)
    draw_text(frame, visible[3:], 33, 16)


def render_original_distance_chat_card(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[list[Image.Image], list[int]]:
    states = [
        (1, 0, 1),
        (2, 0, 0),
        (3, 0, -1),
        (0, 3, 0),
        (0, 4, 0),
        (0, 6, 0),
        (0, 6, 1),
    ]
    frames = []
    for dots, reveal, head_dy in states:
        frame = common.compose_character(layers, base_x=6, head_dy=head_dy)
        draw_original_distance_chat_card(frame, dots=dots, reveal=reveal)
        frames.append(frame)
    return frames, [100, 100, 160, 160, 140, 240, 620]


RENDERERS: dict[
    str,
    Callable[
        [tuple[Image.Image, Image.Image, Image.Image]],
        tuple[list[Image.Image], list[int]],
    ],
] = {
    "v01-chamfer-typewriter": render_chamfer_typewriter,
    "v02-split-word-chips": render_split_word_chips,
    "v03-comic-burst": render_comic_burst,
    "v04-slide-caption": render_slide_caption,
    "v05-chat-card": render_chat_card,
    "v06-right-linked-chat-card": render_right_linked_chat_card,
    "v07-original-distance-chat-card": render_original_distance_chat_card,
}


def validate_frames(variant_id: str, frames: list[Image.Image], durations: list[int]) -> None:
    if len(frames) != len(durations) or len(frames) < 2:
        raise ValueError(f"{variant_id}: frame/duration mismatch")
    if len(set(durations)) < 2:
        raise ValueError(f"{variant_id}: final hold is not differentiated")
    if len({frame.tobytes() for frame in frames}) < 4:
        raise ValueError(f"{variant_id}: insufficient motion states")
    allowed = {
        common.TRANSPARENT,
        common.HAIR,
        common.FACE,
        common.NECK_SHADOW,
        common.PURPLE,
        common.PURPLE_SHADOW,
        common.FX_BLUE,
        common.FX_BLUE_DARK,
    }
    for index, frame in enumerate(frames):
        if frame.mode != "RGBA" or frame.size != (48, 48):
            raise ValueError(f"{variant_id} frame {index}: must be 48x48 RGBA")
        alpha = frame.getchannel("A").histogram()
        if sum(alpha[1:255]) != 0:
            raise ValueError(f"{variant_id} frame {index}: alpha must be binary")
        colors = set(frame.get_flattened_data())
        if not colors.issubset(allowed):
            raise ValueError(f"{variant_id} frame {index}: unexpected color")


def save_apng(frames: list[Image.Image], path: Path, durations: list[int]) -> None:
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


def save_gif(frames: list[Image.Image], path: Path, durations: list[int]) -> None:
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


def scaled_frames(frames: Iterable[Image.Image], size: int) -> list[Image.Image]:
    return [frame.resize((size, size), Image.Resampling.NEAREST) for frame in frames]


def on_background(
    frame: Image.Image,
    background: tuple[int, int, int, int],
) -> Image.Image:
    panel = Image.new("RGBA", frame.size, background)
    panel.alpha_composite(frame)
    return panel


def light_dark_frames(frames: list[Image.Image], size: int, gap: int) -> list[Image.Image]:
    output = []
    for frame in frames:
        scaled = frame.resize((size, size), Image.Resampling.NEAREST)
        panel = Image.new("RGBA", (size * 2 + gap, size), common.TRANSPARENT)
        panel.alpha_composite(on_background(scaled, LIGHT_BG), (0, 0))
        panel.alpha_composite(on_background(scaled, DARK_BG), (size + gap, 0))
        output.append(panel)
    return output


def frame_at_time(
    frames: list[Image.Image], durations: list[int], time_ms: int
) -> Image.Image:
    cursor = time_ms % sum(durations)
    elapsed = 0
    for frame, duration in zip(frames, durations, strict=True):
        elapsed += duration
        if cursor < elapsed:
            return frame
    return frames[-1]


def comparison_frames(
    variants: dict[str, list[Image.Image]],
    durations: dict[str, list[int]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    width = len(VARIANT_ORDER) * size + (len(VARIANT_ORDER) - 1) * gap
    height = size * 2 + gap
    output = []
    for time_ms in range(0, 1800, 100):
        board = Image.new("RGBA", (width, height), common.TRANSPARENT)
        for column, variant_id in enumerate(VARIANT_ORDER):
            frame = frame_at_time(variants[variant_id], durations[variant_id], time_ms)
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            x = column * (size + gap)
            board.alpha_composite(on_background(scaled, LIGHT_BG), (x, 0))
            board.alpha_composite(on_background(scaled, DARK_BG), (x, size + gap))
        output.append(board)
    return output


def final_comparison(
    variants: dict[str, list[Image.Image]], *, size: int = 144, gap: int = 8
) -> Image.Image:
    width = len(VARIANT_ORDER) * size + (len(VARIANT_ORDER) - 1) * gap
    board = Image.new("RGBA", (width, size * 2 + gap), common.TRANSPARENT)
    for column, variant_id in enumerate(VARIANT_ORDER):
        scaled = variants[variant_id][-1].resize((size, size), Image.Resampling.NEAREST)
        x = column * (size + gap)
        board.alpha_composite(on_background(scaled, LIGHT_BG), (x, 0))
        board.alpha_composite(on_background(scaled, DARK_BG), (x, size + gap))
    return board


def focused_comparison_frames(
    original: tuple[list[Image.Image], list[int]],
    v05: tuple[list[Image.Image], list[int]],
    v06: tuple[list[Image.Image], list[int]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    candidates = [original, v05, v06]
    output = []
    for time_ms in range(0, 1800, 100):
        board = Image.new(
            "RGBA",
            (size * 3 + gap * 2, size * 2 + gap),
            common.TRANSPARENT,
        )
        for column, (frames, durations) in enumerate(candidates):
            frame = frame_at_time(frames, durations, time_ms)
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            x = column * (size + gap)
            board.alpha_composite(on_background(scaled, LIGHT_BG), (x, 0))
            board.alpha_composite(on_background(scaled, DARK_BG), (x, size + gap))
        output.append(board)
    return output


def focused_final_comparison(
    original: list[Image.Image],
    v05: list[Image.Image],
    v06: list[Image.Image],
    *,
    size: int = 144,
    gap: int = 8,
) -> Image.Image:
    board = Image.new(
        "RGBA",
        (size * 3 + gap * 2, size * 2 + gap),
        common.TRANSPARENT,
    )
    for column, frames in enumerate((original, v05, v06)):
        scaled = frames[-1].resize((size, size), Image.Resampling.NEAREST)
        x = column * (size + gap)
        board.alpha_composite(on_background(scaled, LIGHT_BG), (x, 0))
        board.alpha_composite(on_background(scaled, DARK_BG), (x, size + gap))
    return board


def selected_comparison_frames(
    candidates: list[tuple[list[Image.Image], list[int]]],
    *,
    size: int,
    gap: int,
) -> list[Image.Image]:
    output = []
    for time_ms in range(0, 1800, 100):
        board = Image.new(
            "RGBA",
            (size * len(candidates) + gap * (len(candidates) - 1), size * 2 + gap),
            common.TRANSPARENT,
        )
        for column, (frames, durations) in enumerate(candidates):
            frame = frame_at_time(frames, durations, time_ms)
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            x = column * (size + gap)
            board.alpha_composite(on_background(scaled, LIGHT_BG), (x, 0))
            board.alpha_composite(on_background(scaled, DARK_BG), (x, size + gap))
        output.append(board)
    return output


def selected_final_comparison(
    candidates: list[list[Image.Image]],
    *,
    size: int = 144,
    gap: int = 8,
) -> Image.Image:
    board = Image.new(
        "RGBA",
        (size * len(candidates) + gap * (len(candidates) - 1), size * 2 + gap),
        common.TRANSPARENT,
    )
    for column, frames in enumerate(candidates):
        scaled = frames[-1].resize((size, size), Image.Resampling.NEAREST)
        x = column * (size + gap)
        board.alpha_composite(on_background(scaled, LIGHT_BG), (x, 0))
        board.alpha_composite(on_background(scaled, DARK_BG), (x, size + gap))
    return board


def contact_sheet(
    variants: dict[str, list[Image.Image]],
    *,
    background: tuple[int, int, int, int],
    size: int = 96,
    gap: int = 4,
) -> Image.Image:
    columns = max(len(frames) for frames in variants.values())
    width = columns * size + (columns - 1) * gap
    height = len(VARIANT_ORDER) * size + (len(VARIANT_ORDER) - 1) * gap
    sheet = Image.new("RGBA", (width, height), common.TRANSPARENT)
    for row, variant_id in enumerate(VARIANT_ORDER):
        for column, frame in enumerate(variants[variant_id]):
            scaled = frame.resize((size, size), Image.Resampling.NEAREST)
            sheet.alpha_composite(
                on_background(scaled, background),
                (column * (size + gap), row * (size + gap)),
            )
    return sheet


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_variant(
    variant_id: str,
    frames: list[Image.Image],
    durations: list[int],
) -> dict[str, object]:
    validate_frames(variant_id, frames, durations)
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
    save_apng(frames, variant_dir / f"{variant_id}.apng", durations)
    save_gif(
        scaled_frames(frames, 480),
        variant_dir / f"{variant_id}-review.gif",
        durations,
    )
    save_gif(
        light_dark_frames(frames, 480, 16),
        variant_dir / f"{variant_id}-review-light-dark.gif",
        durations,
    )
    save_gif(
        light_dark_frames(frames, 50, 8),
        variant_dir / f"{variant_id}-review-50-light-dark.gif",
        durations,
    )
    return {
        "id": variant_id,
        "frame_count": len(frames),
        "durations_ms": durations,
        "frames": frame_entries,
    }


def main() -> None:
    master = common.load_master()
    layers = common.split_master(master)
    rendered = {variant_id: RENDERERS[variant_id](layers) for variant_id in VARIANT_ORDER}
    variants = {variant_id: result[0] for variant_id, result in rendered.items()}
    durations = {variant_id: result[1] for variant_id, result in rendered.items()}

    entries = [
        export_variant(variant_id, variants[variant_id], durations[variant_id])
        for variant_id in VARIANT_ORDER
    ]
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    review_durations = [100] * 18
    save_gif(
        comparison_frames(variants, durations, size=144, gap=8),
        REVIEW_DIR / "comparison-light-dark.gif",
        review_durations,
    )
    save_gif(
        comparison_frames(variants, durations, size=50, gap=8),
        REVIEW_DIR / "comparison-50-light-dark.gif",
        review_durations,
    )
    final_comparison(variants).save(REVIEW_DIR / "comparison-final-light-dark.png")
    original = (trial_v2.render_received(layers), common.FRAME_DURATIONS_MS)
    focused = {
        "v05": rendered["v05-chat-card"],
        "v06": rendered["v06-right-linked-chat-card"],
        "v07": rendered["v07-original-distance-chat-card"],
    }
    save_gif(
        focused_comparison_frames(
            original,
            focused["v05"],
            focused["v06"],
            size=144,
            gap=8,
        ),
        REVIEW_DIR / "focus-original-v05-v06-light-dark.gif",
        [100] * 18,
    )
    focused_final_comparison(
        original[0],
        focused["v05"][0],
        focused["v06"][0],
    ).save(REVIEW_DIR / "focus-original-v05-v06-final-light-dark.png")
    save_gif(
        selected_comparison_frames(
            [original, focused["v05"], focused["v06"], focused["v07"]],
            size=144,
            gap=8,
        ),
        REVIEW_DIR / "focus-original-v05-v06-v07-light-dark.gif",
        [100] * 18,
    )
    selected_final_comparison(
        [original[0], focused["v05"][0], focused["v06"][0], focused["v07"][0]]
    ).save(REVIEW_DIR / "focus-original-v05-v06-v07-final-light-dark.png")
    contact_sheet(variants, background=LIGHT_BG).save(REVIEW_DIR / "frame-contact-sheet-light.png")
    contact_sheet(variants, background=DARK_BG).save(REVIEW_DIR / "frame-contact-sheet-dark.png")

    manifest = {
        "status": "exploration_only",
        "canvas": [48, 48],
        "alpha": "binary",
        "resampling": "nearest-neighbor",
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "variant_order": VARIANT_ORDER,
        "variants": entries,
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(ROOT)


if __name__ == "__main__":
    main()
