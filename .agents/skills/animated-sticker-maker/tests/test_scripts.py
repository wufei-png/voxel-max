from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = SKILL_DIR / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


package_sticker = load_script("package_sticker")
export_platform_gif = load_script("export_platform_gif")


def make_frame(path: Path, color: tuple[int, int, int, int], size: int = 16) -> None:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(2, size - 2):
        for x in range(2, size - 2):
            image.putpixel((x, y), color)
    image.save(path)


class PackageStickerTests(unittest.TestCase):
    def test_frame_paths_cannot_escape_the_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frames_dir = root / "frames"
            frames_dir.mkdir()
            outside = root / "outside.png"
            make_frame(outside, (20, 80, 70, 255))
            with self.assertRaisesRegex(ValueError, "must stay beneath"):
                package_sticker.resolve_frame(frames_dir, "../outside.png")

    def test_package_normalizes_motion_paths_and_semantic_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frames_dir = root / "input"
            frames_dir.mkdir()
            names = ["rest.png", "tilt.png", "hold.png", "return.png"]
            colors = [
                (20, 80, 70, 255),
                (40, 100, 90, 255),
                (60, 120, 110, 255),
                (80, 140, 130, 255),
            ]
            for name, color in zip(names, colors):
                make_frame(frames_dir / name, color)

            motion_path = root / "motion.json"
            motion_path.write_text(
                json.dumps(
                    {
                        "loop": True,
                        "semantic_hold_frame": "hold.png",
                        "frames": [
                            {"file": name, "duration_ms": 300} for name in names
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "package"
            args = argparse.Namespace(
                frames_dir=frames_dir,
                motion=motion_path,
                output=output,
                expected_size=(16, 16),
                quality=92,
                allow_nonstandard_frame_count=False,
                allow_nonstandard_timing=False,
            )

            self.assertEqual(package_sticker.package(args), 0)
            packaged = json.loads(
                (output / "source" / "motion.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                [entry["file"] for entry in packaged["frames"]],
                [f"frames/{index:03d}.png" for index in range(4)],
            )
            self.assertEqual(packaged["semantic_hold_frame"], "frames/002.png")
            _, preview_index = export_platform_gif.automatic_preview_frame(
                output, packaged, (16, 16)
            )
            self.assertEqual(preview_index, 2)
            for index, color in enumerate(colors):
                with Image.open(
                    output / "source" / "frames" / f"{index:03d}.png"
                ) as copied:
                    self.assertEqual(copied.getpixel((8, 8)), color)


class ExportPlatformGifTests(unittest.TestCase):
    def make_reviewed_package(self, root: Path) -> tuple[Path, Path]:
        package = root / "package"
        frames_dir = package / "source" / "frames"
        render_dir = package / "source" / "rendered-frames"
        qa_dir = package / "qa"
        frames_dir.mkdir(parents=True)
        render_dir.mkdir(parents=True)
        qa_dir.mkdir(parents=True)
        make_frame(frames_dir / "000.png", (20, 80, 70, 255))
        make_frame(frames_dir / "001.png", (80, 140, 130, 255))
        for index in range(4):
            make_frame(
                render_dir / f"{index:03d}.png",
                (20 + index * 20, 80 + index * 10, 70 + index * 10, 255),
            )
        (package / "source" / "motion.json").write_text(
            json.dumps(
                {
                    "loop": True,
                    "frames": [
                        {"file": "frames/000.png", "duration_ms": 600},
                        {"file": "frames/001.png", "duration_ms": 600},
                    ],
                    "render": {
                        "frame_dir": "rendered-frames",
                        "frame_count": 4,
                        "frame_durations_ms": [300, 300, 300, 300],
                        "total_duration_ms": 1200,
                    },
                }
            ),
            encoding="utf-8",
        )
        (qa_dir / "report.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "automatic_review": {"status": "pass"},
                    "visual_review": {"status": "pass"},
                }
            ),
            encoding="utf-8",
        )
        track_report = qa_dir / "render-report.json"
        track_report.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "checks": {"frame_count": True, "duration": True},
                    "visual_review": {"status": "pass"},
                }
            ),
            encoding="utf-8",
        )
        return package, track_report

    def test_top_level_pass_without_automatic_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, _ = self.make_reviewed_package(Path(temporary))
            (package / "qa" / "report.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "visual_review": {"status": "pass"},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "checks_pass=False"):
                export_platform_gif.load_reviewed_package(
                    package, allow_unreviewed=False
                )

    def test_render_track_requires_its_own_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package, track_report = self.make_reviewed_package(Path(temporary))
            source_report_path = package / "qa" / "report.json"
            source_report = json.loads(source_report_path.read_text(encoding="utf-8"))
            source_report.pop("automatic_review")
            source_report["checks"] = {"frames": True, "timing": True}
            source_report_path.write_text(json.dumps(source_report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "requires --track-report"):
                export_platform_gif.load_reviewed_package(
                    package, allow_unreviewed=False, frame_track="render"
                )

            frames, durations, _, source_review, track_review = (
                export_platform_gif.load_reviewed_package(
                    package,
                    allow_unreviewed=False,
                    frame_track="render",
                    track_report=track_report,
                )
            )
            self.assertEqual(len(frames), 4)
            self.assertEqual(durations, [300, 300, 300, 300])
            self.assertEqual(source_review["aggregate"], "pass")
            self.assertTrue(source_review["checks_pass"])
            assert track_review is not None
            self.assertTrue(track_review["checks_pass"])

    def test_resample_timeline_preserves_duration_and_semantic_order(self) -> None:
        frames = [Image.new("RGBA", (2, 2), (value, 0, 0, 255)) for value in (1, 2, 3)]
        sampled, durations = export_platform_gif.resample_timeline(
            frames, [100, 300, 600], fps=5
        )
        self.assertEqual([frame.getpixel((0, 0))[0] for frame in sampled], [1, 2, 3, 3, 3])
        self.assertEqual(sum(durations), 1000)
        self.assertTrue(all(duration % 10 == 0 for duration in durations))

    def test_adaptive_export_lowers_fps_before_palette_floor(self) -> None:
        frames = [Image.new("RGBA", (2, 2), (index, 0, 0, 255)) for index in range(30)]
        durations = [40] * 30

        def fake_write(
            candidate_frames, candidate_durations, path, colors, alpha_threshold, loop
        ):
            del candidate_durations, alpha_threshold, loop
            path.write_bytes(b"x" * (len(candidate_frames) * colors * 10))

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "sticker.gif"
            with mock.patch.object(export_platform_gif, "write_gif", side_effect=fake_write):
                _, selected_durations, colors, byte_size, fps, attempts = (
                    export_platform_gif.export_gif(
                        frames,
                        durations,
                        output,
                        max_bytes=20_000,
                        alpha_threshold=96,
                        loop=True,
                        min_colors=64,
                        fps_candidates=(30, 20),
                    )
                )
            self.assertEqual((fps, colors), (20, 64))
            self.assertEqual(byte_size, 15_360)
            self.assertEqual(sum(selected_durations), 1200)
            self.assertTrue(all(attempt["colors"] >= 64 for attempt in attempts))

    def test_fps_candidates_must_be_unique_and_descending(self) -> None:
        self.assertEqual(export_platform_gif.parse_fps_candidates("30,24,15"), (30, 24, 15))
        with self.assertRaises(argparse.ArgumentTypeError):
            export_platform_gif.parse_fps_candidates("24,30")
        with self.assertRaises(argparse.ArgumentTypeError):
            export_platform_gif.parse_fps_candidates("30,30")


if __name__ == "__main__":
    unittest.main()
