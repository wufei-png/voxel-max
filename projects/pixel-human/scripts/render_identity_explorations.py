#!/usr/bin/env python3
"""Render deterministic A3-A5 pixel-human identity explorations."""

from collections.abc import Callable
from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[1]
CANDIDATES_DIR = PROJECT_DIR / "identity" / "candidates"

TRANSPARENT = (0, 0, 0, 0)
HAIR = (18, 16, 22, 255)
FACE = (246, 239, 203, 255)
NECK_SHADOW = (221, 211, 158, 255)
PURPLE = (130, 71, 157, 255)
PURPLE_SHADOW = (100, 53, 121, 255)

LIGHT_BACKGROUND = (242, 241, 235, 255)
DARK_BACKGROUND = (23, 23, 29, 255)


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


def render_a3() -> Image.Image:
    """Refine A2 proportions while preserving its source-faithful silhouette."""
    image = Image.new("RGBA", (32, 32), TRANSPARENT)

    rect(image, (9, 3, 23, 7), HAIR)
    rect(image, (9, 8, 12, 11), HAIR)
    rect(image, (13, 8, 23, 11), FACE)
    rect(image, (9, 12, 23, 17), FACE)

    # Separate the neck and shoulder bands cleanly; A2 overlaps them at y=19.
    rect(image, (13, 18, 19, 19), NECK_SHADOW)
    rect(image, (8, 20, 24, 23), PURPLE)
    rect(image, (3, 24, 29, 30), PURPLE)

    # Keep the sleeve planes, but shorten them to preserve a quieter center mass.
    rect(image, (3, 26, 6, 30), PURPLE_SHADOW)
    rect(image, (26, 26, 29, 30), PURPLE_SHADOW)
    rect(image, (14, 20, 17, 30), HAIR)

    return image


def render_a4() -> Image.Image:
    """Build a broader, grounded work-partner silhouette with stronger sleeves."""
    image = Image.new("RGBA", (32, 32), TRANSPARENT)

    # A wider, slightly lower head reads as calm and grounded rather than sprite-like.
    rect(image, (8, 4, 23, 7), HAIR)
    rect(image, (8, 8, 12, 12), HAIR)
    rect(image, (13, 8, 23, 12), FACE)
    rect(image, (8, 13, 23, 17), FACE)

    rect(image, (13, 18, 19, 19), NECK_SHADOW)
    rect(image, (7, 20, 24, 23), PURPLE)
    rect(image, (2, 24, 29, 30), PURPLE)

    # Stepped internal sleeve planes suggest controlled forearm volume without
    # introducing another shoulder tier or a costume detail.
    rect(image, (2, 25, 6, 30), PURPLE_SHADOW)
    rect(image, (7, 27, 7, 30), PURPLE_SHADOW)
    rect(image, (25, 25, 29, 30), PURPLE_SHADOW)
    rect(image, (24, 27, 24, 30), PURPLE_SHADOW)
    rect(image, (14, 20, 17, 30), HAIR)

    return image


def render_a5() -> Image.Image:
    """Strengthen the left hair signature and repeat its step rhythm in sleeves."""
    image = Image.new("RGBA", (32, 32), TRANSPARENT)

    # The lower fringe returns inward by one pixel, making the asymmetric hair
    # memorable while leaving the face plane completely blank.
    rect(image, (8, 3, 23, 7), HAIR)
    rect(image, (8, 8, 12, 10), HAIR)
    rect(image, (9, 11, 12, 12), HAIR)
    rect(image, (13, 8, 23, 12), FACE)
    rect(image, (9, 13, 23, 17), FACE)

    rect(image, (13, 18, 19, 19), NECK_SHADOW)
    rect(image, (8, 20, 24, 22), PURPLE)
    rect(image, (3, 23, 29, 30), PURPLE)

    # One-pixel top notches echo the fringe step without adding outline or trim.
    rect(image, (3, 24, 6, 30), PURPLE_SHADOW)
    rect(image, (7, 25, 7, 30), PURPLE_SHADOW)
    rect(image, (26, 24, 29, 30), PURPLE_SHADOW)
    rect(image, (25, 25, 25, 30), PURPLE_SHADOW)
    rect(image, (14, 20, 17, 30), HAIR)

    return image


def composite_on(
    background: tuple[int, int, int, int], scaled: Image.Image
) -> Image.Image:
    panel = Image.new("RGBA", (336, 336), background)
    panel.alpha_composite(scaled, (8, 8))
    return panel


def small_composite_on(
    background: tuple[int, int, int, int], scaled: Image.Image
) -> Image.Image:
    panel = Image.new("RGBA", (50, 50), background)
    panel.alpha_composite(scaled)
    return panel


def validate(master: Image.Image) -> None:
    assert master.size == (32, 32)
    assert master.mode == "RGBA"
    pixels = master.get_flattened_data()
    assert {pixel[3] for pixel in pixels} == {0, 255}
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


def export_candidate(candidate_id: str, render: Callable[[], Image.Image]) -> Path:
    output_dir = CANDIDATES_DIR / candidate_id
    output_dir.mkdir(parents=True, exist_ok=True)

    master = render()
    validate(master)

    master_path = output_dir / f"master-{candidate_id}-32.png"
    master.save(master_path)

    scaled = master.resize((320, 320), Image.Resampling.NEAREST)
    scaled.save(output_dir / f"master-{candidate_id}-32@10x.png")

    review = Image.new("RGBA", (680, 336), TRANSPARENT)
    review.alpha_composite(composite_on(LIGHT_BACKGROUND, scaled), (0, 0))
    review.alpha_composite(composite_on(DARK_BACKGROUND, scaled), (344, 0))
    review.save(output_dir / f"master-{candidate_id}-review-light-dark.png")

    display_50 = master.resize((50, 50), Image.Resampling.NEAREST)
    review_50 = Image.new("RGBA", (108, 50), TRANSPARENT)
    review_50.alpha_composite(
        small_composite_on(LIGHT_BACKGROUND, display_50), (0, 0)
    )
    review_50.alpha_composite(
        small_composite_on(DARK_BACKGROUND, display_50), (58, 0)
    )
    review_50.save(output_dir / f"master-{candidate_id}-review-50-light-dark.png")

    return master_path


def main() -> None:
    renderers = {
        "a3": render_a3,
        "a4": render_a4,
        "a5": render_a5,
    }
    for candidate_id, render in renderers.items():
        print(export_candidate(candidate_id, render))


if __name__ == "__main__":
    main()
