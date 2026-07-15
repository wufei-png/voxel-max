#!/usr/bin/env python3
"""Render deterministic A2-A5 side-by-side identity comparison boards."""

from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[1]
CANDIDATES_DIR = PROJECT_DIR / "identity" / "candidates"

TRANSPARENT = (0, 0, 0, 0)
LIGHT_BACKGROUND = (242, 241, 235, 255)
DARK_BACKGROUND = (23, 23, 29, 255)
HEADER_BACKGROUND = (42, 42, 50, 255)
LABEL_COLOR = (246, 239, 203, 255)

CANDIDATE_IDS = ("a2", "a3", "a4", "a5")

# Fixed 3x5 glyphs keep labels pixel-aligned and independent of system fonts.
GLYPHS = {
    "A": ("010", "101", "111", "101", "101"),
    "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "110", "001", "110"),
}


def load_masters() -> dict[str, Image.Image]:
    masters = {}
    for candidate_id in CANDIDATE_IDS:
        path = CANDIDATES_DIR / candidate_id / f"master-{candidate_id}-32.png"
        with Image.open(path) as source:
            master = source.convert("RGBA")
            master.load()
        assert master.size == (32, 32), (path, master.size)
        assert {pixel[3] for pixel in master.get_flattened_data()} == {0, 255}
        masters[candidate_id] = master
    return masters


def draw_label(
    image: Image.Image,
    label: str,
    center_x: int,
    top: int,
    scale: int,
) -> None:
    glyph_width = 3 * scale
    gap = scale
    label_width = len(label) * glyph_width + (len(label) - 1) * gap
    left = center_x - label_width // 2

    for char_index, char in enumerate(label):
        glyph = GLYPHS[char]
        glyph_left = left + char_index * (glyph_width + gap)
        for row_index, row in enumerate(glyph):
            for column_index, pixel in enumerate(row):
                if pixel == "0":
                    continue
                x0 = glyph_left + column_index * scale
                y0 = top + row_index * scale
                for y in range(y0, y0 + scale):
                    for x in range(x0, x0 + scale):
                        image.putpixel((x, y), LABEL_COLOR)


def render_board(
    masters: dict[str, Image.Image],
    display_size: int,
    panel_size: int,
    panel_padding: int,
    header_height: int,
    label_scale: int,
    gutter: int,
) -> Image.Image:
    width = len(CANDIDATE_IDS) * panel_size + (len(CANDIDATE_IDS) - 1) * gutter
    height = header_height + panel_size * 2
    board = Image.new("RGBA", (width, height), TRANSPARENT)

    header = Image.new("RGBA", (width, header_height), HEADER_BACKGROUND)
    board.alpha_composite(header, (0, 0))

    label_height = 5 * label_scale
    label_top = (header_height - label_height) // 2

    for index, candidate_id in enumerate(CANDIDATE_IDS):
        x = index * (panel_size + gutter)
        center_x = x + panel_size // 2
        draw_label(board, candidate_id.upper(), center_x, label_top, label_scale)

        scaled = masters[candidate_id].resize(
            (display_size, display_size), Image.Resampling.NEAREST
        )
        for row_index, background in enumerate(
            (LIGHT_BACKGROUND, DARK_BACKGROUND)
        ):
            panel = Image.new("RGBA", (panel_size, panel_size), background)
            panel.alpha_composite(scaled, (panel_padding, panel_padding))
            y = header_height + row_index * panel_size
            board.alpha_composite(panel, (x, y))

    return board


def main() -> None:
    masters = load_masters()

    large = render_board(
        masters,
        display_size=320,
        panel_size=336,
        panel_padding=8,
        header_height=40,
        label_scale=4,
        gutter=8,
    )
    large.save(CANDIDATES_DIR / "a2-a5-comparison-light-dark.png")

    display_50 = render_board(
        masters,
        display_size=50,
        panel_size=50,
        panel_padding=0,
        header_height=24,
        label_scale=2,
        gutter=8,
    )
    display_50.save(CANDIDATES_DIR / "a2-a5-comparison-50-light-dark.png")

    print(CANDIDATES_DIR / "a2-a5-comparison-light-dark.png")
    print(CANDIDATES_DIR / "a2-a5-comparison-50-light-dark.png")


if __name__ == "__main__":
    main()
