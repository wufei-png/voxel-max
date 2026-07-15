#!/usr/bin/env python3
"""Build the approved pixel-human v1 source pack and WeChat release assets."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageSequence


PROJECT_DIR = Path(__file__).resolve().parents[3]
PACK_DIR = Path(__file__).resolve().parents[1]
PROJECT_SCRIPTS = PROJECT_DIR / "scripts"
PACK_SCRIPTS = Path(__file__).resolve().parent
GOT_IT_SCRIPTS = PACK_DIR / "explorations" / "got-it"
for script_dir in (PROJECT_SCRIPTS, PACK_SCRIPTS, GOT_IT_SCRIPTS):
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

import render_identity_trials as common  # noqa: E402
import render_identity_trials_v2 as trial_v2  # noqa: E402
import render_identity_trials_v3 as trial_v3  # noqa: E402
import render_pack_v1 as pack_v1  # noqa: E402
import render_pack_v2 as pack_v2  # noqa: E402
import render_pack_v3 as pack_v3  # noqa: E402
import render_pack_v5 as pack_v5  # noqa: E402
import render_pack_v6 as pack_v6  # noqa: E402
import render_variants as got_it  # noqa: E402


RELEASE_DIR = PACK_DIR / "releases" / "v1"
SOURCE_DIR = RELEASE_DIR / "source"
WECHAT_DIR = RELEASE_DIR / "wechat"
STICKERS_DIR = WECHAT_DIR / "stickers"
BRAND_DIR = WECHAT_DIR / "brand"
WECHAT_REVIEW_DIR = WECHAT_DIR / "review"

CHARACTER_NAME = "像素小同事"
PACK_NAME = "小同事上班记"
PACK_INTRO = "像素小同事陪你过完一个工作日：收到、忙碌、开会、搞定、崩溃，再准时下班。"
VERIFIED_ON = "2026-07-15"

FILE_STEMS = {
    "s01-received": "01-received",
    "s02-working": "02-working",
    "s03-wait": "03-wait",
    "s04-meeting": "04-meeting",
    "s05-done": "05-done",
    "s06-speechless": "06-speechless",
    "s07-crashed": "07-crashed",
    "s08-off-work": "08-off-work",
    "s09-kowtow": "09-kowtow",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_items(
    layers: tuple[Image.Image, Image.Image, Image.Image],
) -> tuple[dict[str, list[Image.Image]], dict[str, list[int]]]:
    received_frames, received_durations = got_it.render_chat_card(layers)
    items = {
        "s01-received": received_frames,
        "s02-working": trial_v2.render_working(layers),
        "s03-wait": pack_v1.render_wait(layers),
        "s04-meeting": pack_v5.render_meeting(layers),
        "s05-done": pack_v2.render_done(layers),
        "s06-speechless": pack_v1.render_speechless(layers),
        "s07-crashed": trial_v3.render_crashed(layers),
        "s08-off-work": pack_v2.render_off_work(layers),
        "s09-kowtow": pack_v6.render_kowtow(layers),
    }
    durations = {
        item_id: pack_v2.STANDARD_DURATIONS for item_id in pack_v2.ITEM_ORDER
    }
    durations["s01-received"] = received_durations
    durations["s05-done"] = pack_v2.DONE_DURATIONS
    durations["s08-off-work"] = pack_v2.OFF_WORK_DURATIONS
    durations["s09-kowtow"] = pack_v2.KOWTOW_DURATIONS
    return items, durations


def export_source(
    items: dict[str, list[Image.Image]],
    durations: dict[str, list[int]],
) -> None:
    source_entries = [
        pack_v3.export_item(
            item_id,
            items[item_id],
            durations[item_id],
            output_dir=SOURCE_DIR,
        )
        for item_id in pack_v2.ITEM_ORDER
    ]

    review_dir = SOURCE_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_durations = [100] * 21
    pack_v2.save_gif(
        pack_v2.board_frames(items, durations, size=144, gap=8),
        review_dir / "selected-pack-light-dark.gif",
        review_durations,
    )
    pack_v2.save_gif(
        pack_v2.board_frames(items, durations, size=50, gap=8),
        review_dir / "selected-pack-50-light-dark.gif",
        review_durations,
    )
    pack_v2.contact_sheet(
        items,
        background=common.LIGHT_BACKGROUND,
    ).save(review_dir / "frame-contact-sheet-light.png")
    pack_v2.contact_sheet(
        items,
        background=common.DARK_BACKGROUND,
    ).save(review_dir / "frame-contact-sheet-dark.png")
    (review_dir / "order.md").write_text(
        "# 发布源审阅顺序\n\n"
        "左侧 3x3 为浅色，右侧 3x3 为深色；顺序为 S01-S09。\n",
        encoding="utf-8",
    )

    manifest = {
        "status": "approved_release_source",
        "release": "v1",
        "character_name": CHARACTER_NAME,
        "pack_name": PACK_NAME,
        "canvas": [48, 48],
        "master_path": str(common.MASTER_PATH.relative_to(PROJECT_DIR)),
        "master_sha256": common.EXPECTED_MASTER_SHA256,
        "item_order": pack_v2.ITEM_ORDER,
        "labels": pack_v2.LABELS,
        "selection": {
            "s01-received": "explorations/got-it v05-chat-card",
            "s04-meeting": "work/v5",
            "s09-kowtow": "work/v6 grounded-palms revision",
            "other_items": "work/v5, pixel-identical to the approved v2 motions",
        },
        "items": source_entries,
    }
    (SOURCE_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def crop_and_scale(
    image: Image.Image,
    *,
    scale: int,
) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("cannot crop an empty image")
    cropped = image.crop(bbox)
    return cropped.resize(
        (cropped.width * scale, cropped.height * scale),
        Image.Resampling.NEAREST,
    )


def centered_transparent(
    sprite: Image.Image,
    size: tuple[int, int],
    *,
    offset: tuple[int, int] = (0, 0),
) -> Image.Image:
    canvas = Image.new("RGBA", size, common.TRANSPARENT)
    x = (size[0] - sprite.width) // 2 + offset[0]
    y = (size[1] - sprite.height) // 2 + offset[1]
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def export_brand_assets(
    master: Image.Image,
    layers: tuple[Image.Image, Image.Image, Image.Image],
    items: dict[str, list[Image.Image]],
) -> None:
    BRAND_DIR.mkdir(parents=True, exist_ok=True)

    neutral = common.compose_character(layers)
    cover_sprite = crop_and_scale(neutral, scale=6)
    centered_transparent(cover_sprite, (240, 240), offset=(0, 4)).save(
        BRAND_DIR / "cover.png"
    )

    head = master.crop((0, 0, 32, 18))
    tab_sprite = crop_and_scale(head, scale=3)
    centered_transparent(tab_sprite, (50, 50), offset=(0, 1)).save(
        BRAND_DIR / "tab.png"
    )

    banner = Image.new("RGB", (750, 400), (214, 232, 238))
    draw = ImageDraw.Draw(banner)
    draw.rectangle((0, 0, 249, 399), fill=(232, 226, 240))
    draw.rectangle((250, 0, 499, 399), fill=(207, 230, 235))
    draw.rectangle((500, 0, 749, 399), fill=(244, 232, 198))
    for x, y, color in [
        (38, 52, (130, 71, 157)),
        (182, 304, (91, 185, 200)),
        (321, 42, (49, 113, 128)),
        (451, 312, (130, 71, 157)),
        (558, 58, (91, 185, 200)),
        (686, 286, (49, 113, 128)),
    ]:
        draw.rectangle((x, y, x + 23, y + 23), fill=color)

    banner_rgba = banner.convert("RGBA")
    scenes = [
        (items["s02-working"][2], 7, 48, 112),
        (items["s04-meeting"][1], 7, 292, 104),
        (items["s05-done"][-1], 7, 523, 105),
    ]
    for frame, scale, x, y in scenes:
        sprite = crop_and_scale(frame, scale=scale)
        banner_rgba.alpha_composite(sprite, (x, y))
    banner_rgba.convert("RGB").save(BRAND_DIR / "banner.png", optimize=True)


def export_wechat_stickers(
    items: dict[str, list[Image.Image]],
    durations: dict[str, list[int]],
) -> list[dict[str, object]]:
    STICKERS_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    for item_id in pack_v2.ITEM_ORDER:
        frames = [
            frame.resize((240, 240), Image.Resampling.NEAREST)
            for frame in items[item_id]
        ]
        path = STICKERS_DIR / f"{FILE_STEMS[item_id]}.gif"
        pack_v2.save_gif(frames, path, durations[item_id])
        entries.append(
            {
                "id": item_id,
                "label": pack_v2.LABELS[item_id],
                "path": str(path.relative_to(WECHAT_DIR)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "frame_count": len(frames),
                "durations_ms": durations[item_id],
            }
        )
    return entries


def export_wechat_review(
    items: dict[str, list[Image.Image]],
    durations: dict[str, list[int]],
) -> None:
    WECHAT_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    pack_v2.save_gif(
        pack_v2.board_frames(items, durations, size=120, gap=8),
        WECHAT_REVIEW_DIR / "submission-pack-light-dark.gif",
        [100] * 21,
    )
    brand_board = Image.new("RGB", (750, 690), (242, 241, 235))
    banner = Image.open(BRAND_DIR / "banner.png").convert("RGB")
    cover = Image.open(BRAND_DIR / "cover.png").convert("RGBA")
    tab = Image.open(BRAND_DIR / "tab.png").convert("RGBA")
    brand_board.paste(banner, (0, 0))
    cover_bg = Image.new("RGBA", (240, 240), common.LIGHT_BACKGROUND)
    cover_bg.alpha_composite(cover)
    brand_board.paste(cover_bg.convert("RGB"), (150, 425))
    tab_bg = Image.new("RGBA", (100, 100), common.DARK_BACKGROUND)
    tab_bg.alpha_composite(tab.resize((100, 100), Image.Resampling.NEAREST), (0, 0))
    brand_board.paste(tab_bg.convert("RGB"), (500, 495))
    brand_board.save(WECHAT_REVIEW_DIR / "brand-assets-preview.png")


def inspect_gif(path: Path) -> tuple[int, list[int], int | None]:
    image = Image.open(path)
    durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(image)]
    return image.n_frames, durations, image.info.get("loop")


def validate_release(sticker_entries: list[dict[str, object]]) -> dict[str, object]:
    failures: list[str] = []
    for entry in sticker_entries:
        path = WECHAT_DIR / str(entry["path"])
        image = Image.open(path)
        if image.size != (240, 240) or image.format != "GIF":
            failures.append(f"{entry['id']}: invalid format or dimensions")
        if path.stat().st_size > 500_000:
            failures.append(f"{entry['id']}: exceeds 500 KB")
        frame_count, actual_durations, loop = inspect_gif(path)
        if frame_count != entry["frame_count"]:
            failures.append(f"{entry['id']}: frame count changed during export")
        if actual_durations != entry["durations_ms"]:
            failures.append(f"{entry['id']}: timing changed during export")
        if loop != 0:
            failures.append(f"{entry['id']}: GIF is not set to loop forever")

    brand_contract = {
        "brand/banner.png": ((750, 400), {"PNG", "JPEG"}, 500_000),
        "brand/cover.png": ((240, 240), {"PNG"}, 500_000),
        "brand/tab.png": ((50, 50), {"PNG"}, 100_000),
    }
    for relative_path, (size, formats, byte_limit) in brand_contract.items():
        path = WECHAT_DIR / relative_path
        image = Image.open(path)
        if image.size != size or image.format not in formats:
            failures.append(f"{relative_path}: invalid format or dimensions")
        if path.stat().st_size > byte_limit:
            failures.append(f"{relative_path}: exceeds platform byte limit")
    for relative_path in ("brand/cover.png", "brand/tab.png"):
        if Image.open(WECHAT_DIR / relative_path).convert("RGBA").getchannel("A").getextrema()[0] != 0:
            failures.append(f"{relative_path}: transparent background missing")

    if failures:
        raise ValueError("release validation failed:\n- " + "\n- ".join(failures))
    return {
        "status": "passed",
        "checks": [
            "9 GIF files at 240x240",
            "each GIF <= 500 KB",
            "source timing and frame count preserved",
            "infinite loop enabled",
            "banner, cover, and tab dimensions and byte limits",
            "transparent cover and tab backgrounds",
        ],
    }


def main() -> None:
    for generated_dir in (SOURCE_DIR, WECHAT_DIR):
        if generated_dir.exists():
            shutil.rmtree(generated_dir)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    master = common.load_master()
    layers = common.split_master(master)
    items, durations = selected_items(layers)

    export_source(items, durations)
    sticker_entries = export_wechat_stickers(items, durations)
    export_brand_assets(master, layers, items)
    export_wechat_review(items, durations)
    qa = validate_release(sticker_entries)

    brand_entries = []
    for relative_path in ("brand/banner.png", "brand/cover.png", "brand/tab.png"):
        path = WECHAT_DIR / relative_path
        brand_entries.append(
            {
                "path": relative_path,
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    manifest = {
        "status": "ready_for_submission",
        "platform": "wechat_sticker_album",
        "verified_on": VERIFIED_ON,
        "character_name": CHARACTER_NAME,
        "pack_name": PACK_NAME,
        "pack_intro": PACK_INTRO,
        "release_mode": "free",
        "appreciation": False,
        "sticker_count": len(sticker_entries),
        "stickers": sticker_entries,
        "brand_assets": brand_entries,
        "qa": qa,
    }
    (WECHAT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(RELEASE_DIR)


if __name__ == "__main__":
    main()
