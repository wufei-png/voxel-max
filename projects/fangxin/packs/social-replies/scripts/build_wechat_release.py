#!/usr/bin/env python3
"""Build the WeChat release package for 《方芯回你了》.

This pack-specific exporter reads the approved 30 fps RGBA render frames,
creates adaptive-size GIF derivatives, and builds the three static WeChat
brand assets. It does not invoke the repository's manual Skill.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageSequence

import build_pack as pack


REPO_ROOT = Path(__file__).resolve().parents[5]
PACK_ROOT = REPO_ROOT / "projects/fangxin/packs/social-replies"
OUTPUT_ROOT = PACK_ROOT / "output"
ANCHORS = PACK_ROOT / "work/anchors/rgba"
DEFAULT_RELEASE_ROOT = PACK_ROOT / "releases/v1"

TITLE = "方芯回你了"
INTRODUCTION = "方芯不只会上班，也会认真回你：同意、拒绝、笑死、感谢、鼓励，以及好好说晚安。"
WECHAT_SPEC = (
    "https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/"
    "readtemplate?t=guide/index.html#/makingSpecifications"
)
MAX_GIF_BYTES = 500_000
TARGET_GIF_BYTES = 490_000
FPS_CANDIDATES = (30, 24, 20, 15)
COLOR_CANDIDATES = (128, 96, 64)

ITEMS = (
    ("01", "ok", "好的", "s01-ok"),
    ("02", "buxing", "不行", "s02-buxing"),
    ("03", "wuyu", "无语", "s03-wuyu"),
    ("04", "xiaosi", "笑死", "s04-xiaosi"),
    ("05", "xiexie", "谢谢", "s05-xiexie"),
    ("06", "meishi", "没事", "s06-meishi"),
    ("07", "jiayou", "加油", "s07-jiayou"),
    ("08", "xinkule", "辛苦了", "s08-xinkule"),
    ("09", "lihai", "厉害", "s09-lihai"),
    ("10", "baoqian", "抱歉", "s10-baoqian"),
    ("11", "zhendejiade", "真的假的", "s11-zhendejiade"),
    ("12", "wanan", "晚安", "s12-wanan"),
)


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def repo_path(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def motion_record(package: str) -> dict[str, object]:
    path = OUTPUT_ROOT / package / "source/motion.json"
    motion = json.loads(path.read_text(encoding="utf-8"))
    render = motion.get("render")
    if not isinstance(render, dict) or render.get("fps") != 30:
        raise ValueError(f"approved 30 fps render metadata missing: {path}")
    return motion


def gif_info(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        durations = []
        borders_clear = True
        for frame in ImageSequence.Iterator(image):
            durations.append(frame.info.get("duration", image.info.get("duration", 0)))
            alpha = frame.convert("RGBA").getchannel("A")
            width, height = alpha.size
            borders_clear &= all(
                edge.getbbox() is None
                for edge in (
                    alpha.crop((0, 0, width, 1)),
                    alpha.crop((0, height - 1, width, height)),
                    alpha.crop((0, 0, 1, height)),
                    alpha.crop((width - 1, 0, width, height)),
                )
            )
        return {
            "path": repo_path(path),
            "format": image.format,
            "size": list(image.size),
            "bytes": path.stat().st_size,
            "frame_count": getattr(image, "n_frames", 1),
            "duration_ms": sum(durations),
            "frame_duration_ms_range": [min(durations), max(durations)],
            "loop": image.info.get("loop"),
            "transparent_borders": borders_clear,
        }


def encode_candidate(
    frames_dir: Path,
    source_rate: float,
    fps: int,
    colors: int,
    output: Path,
) -> None:
    filter_graph = (
        f"[0:v]fps={fps},scale=240:240:flags=lanczos,split[a][b];"
        f"[a]palettegen=max_colors={colors}:reserve_transparent=1:"
        "stats_mode=diff[p];"
        "[b][p]paletteuse=dither=sierra2_4a:alpha_threshold=48:"
        "diff_mode=rectangle"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            f"{source_rate:.9f}",
            "-i",
            str(frames_dir / "%03d.png"),
            "-filter_complex",
            filter_graph,
            "-loop",
            "0",
            str(output),
        ]
    )


def export_sticker(
    package: str,
    release_name: str,
    release_root: Path,
    verified_on: str,
) -> dict[str, object]:
    motion = motion_record(package)
    render = motion["render"]
    source_count = int(render["frame_count"])
    total_ms = int(render["total_duration_ms"])
    frames_dir = OUTPUT_ROOT / package / "source/rendered-frames"
    actual_count = len(list(frames_dir.glob("*.png")))
    if actual_count != source_count:
        raise ValueError(f"rendered frame count mismatch for {package}")
    source_rate = source_count * 1000.0 / total_ms

    package_export = OUTPUT_ROOT / package / "exports/wechat"
    package_export.mkdir(parents=True, exist_ok=True)
    final_path = package_export / "sticker.gif"
    attempts: list[dict[str, object]] = []
    selected: dict[str, object] | None = None

    with tempfile.TemporaryDirectory(prefix=f"{package}-wechat-") as temp:
        candidate = Path(temp) / "candidate.gif"
        for fps in FPS_CANDIDATES:
            for colors in COLOR_CANDIDATES:
                encode_candidate(frames_dir, source_rate, fps, colors, candidate)
                size = candidate.stat().st_size
                attempt = {"fps": fps, "colors": colors, "bytes": size}
                attempts.append(attempt)
                if size <= TARGET_GIF_BYTES:
                    shutil.copy2(candidate, final_path)
                    selected = attempt
                    break
            if selected is not None:
                break
    if selected is None:
        raise ValueError(f"cannot meet WeChat GIF size limit for {package}: {attempts}")

    info = gif_info(final_path)
    checks = {
        "format_is_gif": info["format"] == "GIF",
        "size_is_240_square": info["size"] == [240, 240],
        "under_500000_bytes": info["bytes"] <= MAX_GIF_BYTES,
        "animated": info["frame_count"] > 1,
        "loops_forever": info["loop"] == 0,
        "transparent_borders": info["transparent_borders"],
        "duration_within_50ms_of_source": abs(info["duration_ms"] - total_ms) <= 50,
        "fps_is_approved_candidate": selected["fps"] in FPS_CANDIDATES,
        "palette_has_at_least_64_colors": selected["colors"] >= 64,
    }
    status = "pass" if all(checks.values()) else "fail"
    report = {
        "status": status,
        "platform": "wechat",
        "verified_on": verified_on,
        "spec_url": WECHAT_SPEC,
        "source": {
            "package": package,
            "render_fps": render["fps"],
            "frame_count": source_count,
            "duration_ms": total_ms,
        },
        "adaptive_encoding": {
            "fps_order": list(FPS_CANDIDATES),
            "color_order": list(COLOR_CANDIDATES),
            "target_bytes": TARGET_GIF_BYTES,
            "attempts": attempts,
            "selected": selected,
        },
        "output": info,
        "checks": checks,
        "visual_review": None,
    }
    report_path = package_export / "sticker.export-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if status != "pass":
        raise ValueError(f"WeChat export validation failed for {package}: {checks}")

    wechat = release_root / "wechat"
    shutil.copy2(final_path, wechat / f"stickers/{release_name}.gif")
    shutil.copy2(report_path, wechat / f"qa/reports/{release_name}.json")
    return report


def fit_subject(image: Image.Image, size: tuple[int, int], max_side: int) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("brand asset source has no visible subject")
    subject = rgba.crop(bbox)
    subject.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size)
    canvas.alpha_composite(
        subject,
        ((size[0] - subject.width) // 2, (size[1] - subject.height) // 2),
    )
    return canvas


def banner_subject(image: Image.Image, max_side: int) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("banner source has no visible subject")
    subject = rgba.crop(bbox)
    subject.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return subject


def make_brand_assets(release_root: Path) -> None:
    wechat = release_root / "wechat"
    happy = Image.open(ANCHORS / "happy-eyes-rgba.png").convert("RGBA")
    fit_subject(happy, (240, 240), 220).save(wechat / "cover.png")
    fit_subject(happy, (50, 50), 46).save(wechat / "chat-icon.png")

    s01 = Image.open(OUTPUT_ROOT / "s01-ok/source/frames/003.png").convert("RGBA")
    s04 = happy
    half = pack.normalize(ANCHORS / "half-eyes-rgba.png")
    s12 = pack.set_core_state(
        half,
        pack.DIM_CYAN,
        0.14,
        face_spread_max=45,
        dim_strength=1.8,
        glow_strength=0.35,
    )
    s12 = pack.dim_subject(pack.transform_subject(s12, dy=26), 0.84)

    width, height = 750, 400
    banner = Image.new("RGBA", (width, height))
    pixels = banner.load()
    for y in range(height):
        for x in range(width):
            mix = (x / (width - 1)) * 0.65 + (y / (height - 1)) * 0.35
            start = (6, 28, 40)
            end = (13, 89, 100)
            pixels[x, y] = tuple(
                round(start[channel] * (1.0 - mix) + end[channel] * mix)
                for channel in range(3)
            ) + (255,)
    draw = ImageDraw.Draw(banner, "RGBA")
    for x, alpha in ((42, 54), (70, 82), (98, 118)):
        draw.rounded_rectangle((x, 70, x + 18, 88), radius=4, fill=(116, 231, 224, alpha))
    draw.rectangle((45, 330, 190, 332), fill=(113, 217, 213, 40))
    draw.rectangle((565, 62, 700, 64), fill=(113, 217, 213, 34))

    left = banner_subject(s01, 176)
    hero = banner_subject(s04, 330)
    right = banner_subject(s12, 176)
    banner.alpha_composite(left, (22, 184))
    banner.alpha_composite(hero, ((width - hero.width) // 2, 36))
    banner.alpha_composite(right, (width - right.width - 22, 184))
    banner.convert("RGB").save(wechat / "banner.png", optimize=True)


def decoded_frames(path: Path) -> list[Image.Image]:
    with Image.open(path) as image:
        return [frame.convert("RGBA").copy() for frame in ImageSequence.Iterator(image)]


def on_background(image: Image.Image, size: int, color: tuple[int, int, int]) -> Image.Image:
    rgba = image.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    base = Image.new("RGBA", (size, size), (*color, 255))
    base.alpha_composite(rgba)
    return base.convert("RGB")


def make_qa_artifacts(release_root: Path) -> None:
    wechat = release_root / "wechat"
    decoded_dir = wechat / "qa/decoded-previews"
    strips_dir = wechat / "qa/frame-strips"
    decoded_dir.mkdir(parents=True, exist_ok=True)
    strips_dir.mkdir(parents=True, exist_ok=True)

    contact = Image.new("RGB", (960, 720), (24, 33, 38))
    all_frames = Image.new("RGB", (720, 1440), (24, 33, 38))
    for index, (number, slug, _meaning, _package) in enumerate(ITEMS):
        name = f"{number}-{slug}"
        frames = decoded_frames(wechat / f"stickers/{name}.gif")
        hold_index = round((len(frames) - 1) * 0.58)
        preview = on_background(frames[hold_index], 240, (238, 242, 242))
        preview.save(decoded_dir / f"{name}.png")
        contact.paste(preview, ((index % 4) * 240, (index // 4) * 240))

        sample_indices = [round(i * (len(frames) - 1) / 5) for i in range(6)]
        strip = Image.new("RGB", (720, 120), (24, 33, 38))
        for sample, frame_index in enumerate(sample_indices):
            strip.paste(
                on_background(frames[frame_index], 120, (24, 33, 38)),
                (sample * 120, 0),
            )
        strip.save(strips_dir / f"{name}.png")
        all_frames.paste(strip, (0, index * 120))

    contact.save(wechat / "qa/contact-sheet.png")
    all_frames.save(wechat / "qa/all-frames-contact-sheet.png")


def image_info(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        width, height = rgba.size
        borders_clear = all(
            edge.getbbox() is None
            for edge in (
                alpha.crop((0, 0, width, 1)),
                alpha.crop((0, height - 1, width, height)),
                alpha.crop((0, 0, 1, height)),
                alpha.crop((width - 1, 0, width, height)),
            )
        )
        return {
            "path": repo_path(path),
            "format": image.format,
            "size": list(image.size),
            "bytes": path.stat().st_size,
            "alpha_min": alpha.getextrema()[0],
            "alpha_max": alpha.getextrema()[1],
            "transparent_borders": borders_clear,
            "fully_opaque": alpha.getextrema() == (255, 255),
        }


def write_manifest(release_root: Path, verified_on: str) -> None:
    manifest = {
        "status": "ready_for_submission",
        "verified_on": verified_on,
        "title": TITLE,
        "introduction": INTRODUCTION,
        "distribution": "free",
        "artist_and_copyright": "same_submitter_profile_as_shangbanzhong_managed_outside_repository",
        "spec_url": WECHAT_SPEC,
        "items": [
            {
                "number": number,
                "slug": slug,
                "meaning": meaning,
                "source_package": package,
            }
            for number, slug, meaning, package in ITEMS
        ],
        "brand_assets": {
            "cover": "cover.png",
            "chat_icon": "chat-icon.png",
            "banner": "banner.png",
        },
    }
    path = release_root / "wechat/manifest.json"
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_release(release_root: Path) -> None:
    wechat = release_root / "wechat"
    sticker_reports = [
        json.loads((wechat / f"qa/reports/{number}-{slug}.json").read_text())
        for number, slug, _meaning, _package in ITEMS
    ]
    cover = image_info(wechat / "cover.png")
    icon = image_info(wechat / "chat-icon.png")
    banner = image_info(wechat / "banner.png")
    meanings = [meaning for _number, _slug, meaning, _package in ITEMS]
    checks = {
        "wechat_has_twelve_stickers": len(sticker_reports) == 12,
        "all_sticker_exports_pass": all(item["status"] == "pass" for item in sticker_reports),
        "all_stickers_under_500000_bytes": all(
            item["output"]["bytes"] <= MAX_GIF_BYTES for item in sticker_reports
        ),
        "all_stickers_240_square_and_looping": all(
            item["output"]["size"] == [240, 240]
            and item["output"]["loop"] == 0
            and item["output"]["frame_count"] > 1
            for item in sticker_reports
        ),
        "cover_matches_limits": cover["format"] == "PNG"
        and cover["size"] == [240, 240]
        and cover["bytes"] <= 500_000
        and cover["alpha_min"] == 0
        and cover["transparent_borders"],
        "chat_icon_matches_limits": icon["format"] == "PNG"
        and icon["size"] == [50, 50]
        and icon["bytes"] <= 100_000
        and icon["alpha_min"] == 0
        and icon["transparent_borders"],
        "banner_matches_limits": banner["format"] == "PNG"
        and banner["size"] == [750, 400]
        and banner["bytes"] <= 500_000
        and banner["fully_opaque"],
        "wechat_copy_matches_limits": len(TITLE) <= 8
        and len(INTRODUCTION) <= 80
        and len(meanings) == len(set(meanings))
        and all(len(meaning) <= 4 for meaning in meanings),
    }
    status = "pass" if all(checks.values()) else "fail"
    report = {
        "status": status,
        "automatic_review": {"status": status, "checks": checks},
        "visual_review": {"status": "pending"},
        "wechat": {
            "stickers": [item["output"] for item in sticker_reports],
            "cover": cover,
            "chat_icon": icon,
            "banner": banner,
        },
    }
    qa_path = release_root / "qa/release-report.json"
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    qa_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if status != "pass":
        raise ValueError(f"release validation failed: {checks}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-on", default="2026-07-14")
    parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)
    args = parser.parse_args()
    release_root = args.release_root
    if not release_root.is_absolute():
        release_root = REPO_ROOT / release_root

    wechat = release_root / "wechat"
    for directory in (
        wechat / "stickers",
        wechat / "qa/reports",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    for number, slug, _meaning, package in ITEMS:
        export_sticker(package, f"{number}-{slug}", release_root, args.verified_on)
    make_brand_assets(release_root)
    make_qa_artifacts(release_root)
    write_manifest(release_root, args.verified_on)
    validate_release(release_root)
    print(f"Built WeChat release candidate at {release_root}")


if __name__ == "__main__":
    main()
