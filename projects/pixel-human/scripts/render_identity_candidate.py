#!/usr/bin/env python3
"""Render the deterministic A1 identity candidate and review images."""

from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "identity" / "candidates" / "a2"

TRANSPARENT = (0, 0, 0, 0)
HAIR = (18, 16, 22, 255)
FACE = (246, 239, 203, 255)
NECK_SHADOW = (221, 211, 158, 255)
PURPLE = (130, 71, 157, 255)
PURPLE_SHADOW = (100, 53, 121, 255)

LIGHT_BACKGROUND = (242, 241, 235, 255)
DARK_BACKGROUND = (23, 23, 29, 255)


def rect(image: Image.Image, box: tuple[int, int, int, int], color: tuple[int, int, int, int]) -> None:
    """Draw an inclusive integer-aligned rectangle."""
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            image.putpixel((x, y), color)


def render_master() -> Image.Image:
    image = Image.new("RGBA", (32, 32), TRANSPARENT)

    # Stepped hair and intentionally blank face plane.
    rect(image, (9, 3, 23, 7), HAIR)
    rect(image, (9, 8, 12, 11), HAIR)
    rect(image, (13, 8, 23, 11), FACE)
    rect(image, (9, 12, 23, 16), FACE)

    # Neck and broad geometric shoulders preserve the source silhouette while
    # adding clear attachment points for later controlled arm poses.
    rect(image, (13, 17, 19, 19), NECK_SHADOW)
    rect(image, (8, 19, 24, 22), PURPLE)
    rect(image, (3, 23, 29, 30), PURPLE)

    # Sleeve-side shadow blocks keep the center mass readable at 50 px.
    rect(image, (3, 25, 6, 30), PURPLE_SHADOW)
    rect(image, (26, 25, 29, 30), PURPLE_SHADOW)

    # The thin source collar lines do not survive the 32 px grid cleanly; the
    # broad center seam carries that structure without adding chunky stairs.
    rect(image, (14, 20, 17, 30), HAIR)

    return image


def composite_on(background: tuple[int, int, int, int], scaled: Image.Image) -> Image.Image:
    panel = Image.new("RGBA", (336, 336), background)
    panel.alpha_composite(scaled, (8, 8))
    return panel


def small_composite_on(background: tuple[int, int, int, int], scaled: Image.Image) -> Image.Image:
    panel = Image.new("RGBA", (50, 50), background)
    panel.alpha_composite(scaled)
    return panel


def validate(master: Image.Image) -> None:
    assert master.size == (32, 32)
    assert master.mode == "RGBA"
    pixels = master.get_flattened_data()
    alpha_values = {pixel[3] for pixel in pixels}
    assert alpha_values == {0, 255}, alpha_values
    expected_colors = {
        TRANSPARENT,
        HAIR,
        FACE,
        NECK_SHADOW,
        PURPLE,
        PURPLE_SHADOW,
    }
    actual_colors = set(pixels)
    assert actual_colors == expected_colors, actual_colors ^ expected_colors


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = render_master()
    validate(master)

    master_path = OUTPUT_DIR / "master-a2-32.png"
    master.save(master_path)

    scaled = master.resize((320, 320), Image.Resampling.NEAREST)
    scaled.save(OUTPUT_DIR / "master-a2-32@10x.png")

    review = Image.new("RGBA", (680, 336), (0, 0, 0, 0))
    review.alpha_composite(composite_on(LIGHT_BACKGROUND, scaled), (0, 0))
    review.alpha_composite(composite_on(DARK_BACKGROUND, scaled), (344, 0))
    review.save(OUTPUT_DIR / "master-a2-review-light-dark.png")

    display_50 = master.resize((50, 50), Image.Resampling.NEAREST)
    review_50 = Image.new("RGBA", (108, 50), (0, 0, 0, 0))
    review_50.alpha_composite(small_composite_on(LIGHT_BACKGROUND, display_50), (0, 0))
    review_50.alpha_composite(small_composite_on(DARK_BACKGROUND, display_50), (58, 0))
    review_50.save(OUTPUT_DIR / "master-a2-review-50-light-dark.png")

    print(master_path)


if __name__ == "__main__":
    main()
