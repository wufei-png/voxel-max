#!/usr/bin/env python3
"""Build the approved WeChat release for Fangxin Shangbanzhong v1."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[5]


ITEMS = (
    ("01", "shoudao", "收到", "s01-shoudao"),
    ("02", "biecui", "别催", "s02-biecui-square-to-squint"),
    ("03", "sikaozhong", "思考中", "s03-sikaozhong"),
    ("04", "paotongle", "跑通了", "s04-paotongle"),
    ("05", "kazhule", "卡住了", "s05-kazhule"),
    ("06", "guorele", "过热了", "s06-cpushaole"),
    ("07", "yiduzhuangsi", "已读装死", "s07-yiduzhuangsi"),
    ("08", "yabianle", "压扁了", "s08-bug-squash"),
)

WECHAT_SPEC = (
    "https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/"
    "readtemplate?t=guide/index.html#/makingSpecifications"
)
def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def export_stickers(repo: Path, release_root: Path, verified_on: str) -> None:
    exporter = repo / ".agents/skills/animated-sticker-maker/scripts/export_platform_gif.py"
    output_root = repo / "projects/fangxin/packs/shangbanzhong/output"
    platform_release = release_root / "wechat"
    stickers_dir = platform_release / "stickers"
    reports_dir = platform_release / "qa/reports"
    previews_dir = platform_release / "qa/previews"
    stickers_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)

    for number, slug, _meaning, package_name in ITEMS:
        package = output_root / package_name
        package_export = package / "exports/wechat"
        package_export.mkdir(parents=True, exist_ok=True)
        sticker_output = package_export / "sticker.gif"
        report_output = package_export / "sticker.export-report.json"
        preview_output = package_export / "qa-preview.png"
        run(
            [
                "python3",
                str(exporter),
                "--package",
                str(package.relative_to(repo)),
                "--platform",
                "wechat",
                "--size",
                "240x240",
                "--max-bytes",
                "500000",
                "--output",
                str(sticker_output.relative_to(repo)),
                "--report-output",
                str(report_output.relative_to(repo)),
                "--spec-url",
                WECHAT_SPEC,
                "--verified-on",
                verified_on,
                "--preview-output",
                str(preview_output.relative_to(repo)),
            ],
            repo,
        )

        release_name = f"{number}-{slug}"
        shutil.copy2(sticker_output, stickers_dir / f"{release_name}.gif")
        shutil.copy2(report_output, reports_dir / f"{release_name}.json")
        shutil.copy2(preview_output, previews_dir / f"{release_name}.png")


def build_brand_assets(repo: Path, release_root: Path) -> None:
    work = repo / "projects/fangxin/packs/shangbanzhong/work"
    wechat = release_root / "wechat"
    wechat.mkdir(parents=True, exist_ok=True)

    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(work / "v6-happy-rgba.png"),
            "-vf",
            "scale=240:240:flags=lanczos,format=rgba",
            "-frames:v",
            "1",
            str(wechat / "cover.png"),
        ],
        repo,
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(work / "v6-neutral-rgba.png"),
            "-vf",
            "scale=50:50:flags=lanczos,format=rgba",
            "-frames:v",
            "1",
            str(wechat / "chat-icon.png"),
        ],
        repo,
    )

    banner_filter = (
        "[0:v]"
        "drawbox=x=46:y=82:w=18:h=18:color=0x74e7e0@0.28:t=fill,"
        "drawbox=x=72:y=82:w=18:h=18:color=0x74e7e0@0.42:t=fill,"
        "drawbox=x=98:y=82:w=18:h=18:color=0x74e7e0@0.62:t=fill,"
        "drawbox=x=58:y=294:w=122:h=2:color=0x71d9d5@0.18:t=fill,"
        "drawbox=x=610:y=90:w=64:h=64:color=0x5dff9b@0.10:t=fill,"
        "drawbox=x=622:y=102:w=40:h=40:color=0x5dff9b@0.20:t=fill,"
        "drawbox=x=634:y=114:w=16:h=16:color=0x78ffae@0.90:t=fill,"
        "drawbox=x=570:y=320:w=118:h=2:color=0x71d9d5@0.14:t=fill[bg];"
        "[1:v]scale=390:390:flags=lanczos[hero];"
        "[2:v]scale=180:180:flags=lanczos[bug];"
        "[bg][hero]overlay=180:5:format=auto[mid];"
        "[mid][bug]overlay=15:205:format=auto,format=rgba[out]"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "gradients=s=750x400:c0=0x061c28:c1=0x0d5964:x0=0:y0=0:x1=750:y1=400:d=1",
            "-loop",
            "1",
            "-i",
            str(work / "v6-happy-rgba.png"),
            "-loop",
            "1",
            "-i",
            str(work / "s08-bug-rgba.png"),
            "-filter_complex",
            banner_filter,
            "-map",
            "[out]",
            "-frames:v",
            "1",
            str(wechat / "banner.png"),
        ],
        repo,
    )


def build_contact_sheet(repo: Path, release_root: Path) -> None:
    wechat = release_root / "wechat"
    decoded_previews = wechat / "qa/decoded-previews"
    decoded_previews.mkdir(parents=True, exist_ok=True)
    for number, slug, _meaning, _package_name in ITEMS:
        name = f"{number}-{slug}"
        report = json.loads(
            (wechat / f"qa/reports/{name}.json").read_text(encoding="utf-8")
        )
        preview_index = report["preview"]["frame"] - 1
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(wechat / f"stickers/{name}.gif"),
                "-vf",
                f"select=eq(n\\,{preview_index})",
                "-fps_mode",
                "vfr",
                "-frames:v",
                "1",
                str(decoded_previews / f"{name}.png"),
            ],
            repo,
        )

    inputs: list[str] = []
    for number, slug, _meaning, _package_name in ITEMS:
        inputs.extend(["-i", str(decoded_previews / f"{number}-{slug}.png")])
    layout = "|".join(
        f"{(index % 4) * 240}_{(index // 4) * 240}" for index in range(len(ITEMS))
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            f"xstack=inputs=8:layout={layout}:fill=0x182126",
            "-frames:v",
            "1",
            str(wechat / "qa/contact-sheet.png"),
        ],
        repo,
    )

    frame_strips = wechat / "qa/frame-strips"
    frame_strips.mkdir(parents=True, exist_ok=True)
    strip_inputs: list[str] = []
    for number, slug, _meaning, _package_name in ITEMS:
        name = f"{number}-{slug}"
        strip = frame_strips / f"{name}.png"
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(wechat / f"stickers/{name}.gif"),
                "-vf",
                "scale=120:120:flags=neighbor,tile=6x1:padding=0:margin=0:color=0x182126",
                "-frames:v",
                "1",
                str(strip),
            ],
            repo,
        )
        strip_inputs.extend(["-i", str(strip)])
    strip_layout = "|".join(f"0_{index * 120}" for index in range(len(ITEMS)))
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *strip_inputs,
            "-filter_complex",
            f"xstack=inputs=8:layout={strip_layout}:fill=0x182126",
            "-frames:v",
            "1",
            str(wechat / "qa/all-frames-contact-sheet.png"),
        ],
        repo,
    )


def repository_path(path: Path) -> str:
    """Return a portable repository-relative path when possible."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def image_record(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        width, height = rgba.size
        border_is_transparent = all(
            edge.getbbox() is None
            for edge in (
                alpha.crop((0, 0, width, 1)),
                alpha.crop((0, height - 1, width, height)),
                alpha.crop((0, 0, 1, height)),
                alpha.crop((width - 1, 0, width, height)),
            )
        )
        return {
            "path": repository_path(path),
            "format": image.format,
            "size": [width, height],
            "bytes": path.stat().st_size,
            "alpha_min": alpha.getextrema()[0],
            "alpha_max": alpha.getextrema()[1],
            "border_is_transparent": border_is_transparent,
            "fully_opaque": alpha.getextrema() == (255, 255),
        }


def gif_record(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        return {
            "path": repository_path(path),
            "format": image.format,
            "size": list(image.size),
            "bytes": path.stat().st_size,
            "frame_count": getattr(image, "n_frames", 1),
            "loop": image.info.get("loop"),
        }


def validate_release(release_root: Path) -> None:
    wechat_stickers = [
        gif_record(release_root / f"wechat/stickers/{number}-{slug}.gif")
        for number, slug, _meaning, _package_name in ITEMS
    ]
    cover = image_record(release_root / "wechat/cover.png")
    icon = image_record(release_root / "wechat/chat-icon.png")
    banner = image_record(release_root / "wechat/banner.png")
    meanings = [meaning for _number, _slug, meaning, _package_name in ITEMS]
    introduction = "方芯是一枚认真上班的小芯片，负责收到、处理中、跑通，以及偶尔卡住和装死。"

    checks = {
        "wechat_has_eight_stickers": len(wechat_stickers) == 8,
        "wechat_stickers_match_limits": all(
            item["format"] == "GIF"
            and item["size"] == [240, 240]
            and item["bytes"] <= 500_000
            and item["frame_count"] > 1
            and item["loop"] == 0
            for item in wechat_stickers
        ),
        "cover_matches_limits": cover["format"] == "PNG"
        and cover["size"] == [240, 240]
        and cover["bytes"] <= 500_000
        and cover["alpha_min"] == 0
        and cover["border_is_transparent"],
        "chat_icon_matches_limits": icon["format"] == "PNG"
        and icon["size"] == [50, 50]
        and icon["bytes"] <= 100_000
        and icon["alpha_min"] == 0
        and icon["border_is_transparent"],
        "banner_matches_limits": banner["format"] == "PNG"
        and banner["size"] == [750, 400]
        and banner["bytes"] <= 500_000
        and banner["fully_opaque"],
        "wechat_copy_matches_limits": len("方芯上班中") <= 8
        and len(introduction) <= 80
        and len(meanings) == len(set(meanings))
        and all(len(meaning) <= 4 for meaning in meanings),
    }
    status = "pass" if all(checks.values()) else "fail"
    report = {
        "status": status,
        "automatic_review": {"status": status, "checks": checks},
        "visual_review": None,
        "wechat": {
            "stickers": wechat_stickers,
            "cover": cover,
            "chat_icon": icon,
            "banner": banner,
        },
    }
    report_path = release_root / "qa/release-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if status != "pass":
        raise ValueError(f"release validation failed: {checks}")


def write_manifests(release_root: Path, verified_on: str) -> None:
    common_items = [
        {
            "number": number,
            "slug": slug,
            "meaning": meaning,
            "source_package": package_name,
        }
        for number, slug, meaning, package_name in ITEMS
    ]
    wechat = {
        "status": "published",
        "verified_on": verified_on,
        "title": "方芯上班中",
        "introduction": "方芯是一枚认真上班的小芯片，负责收到、处理中、跑通，以及偶尔卡住和装死。",
        "distribution": "free",
        "artist_and_copyright": "managed_by_submitter_outside_repository",
        "spec_url": WECHAT_SPEC,
        "items": common_items,
        "brand_assets": {
            "cover": "cover.png",
            "chat_icon": "chat-icon.png",
            "banner": "banner.png",
        },
    }
    path = release_root / "wechat/manifest.json"
    path.write_text(json.dumps(wechat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-on", default="2026-07-14")
    parser.add_argument(
        "--release-root",
        type=Path,
        default=Path("projects/fangxin/packs/shangbanzhong/releases/v1"),
    )
    args = parser.parse_args()

    repo = REPO_ROOT
    release_root = args.release_root
    if not release_root.is_absolute():
        release_root = repo / release_root
    release_root.mkdir(parents=True, exist_ok=True)

    export_stickers(repo, release_root, args.verified_on)
    build_brand_assets(repo, release_root)
    build_contact_sheet(repo, release_root)
    write_manifests(release_root, args.verified_on)
    validate_release(release_root)
    print(f"Built platform releases at {release_root}")


if __name__ == "__main__":
    main()
