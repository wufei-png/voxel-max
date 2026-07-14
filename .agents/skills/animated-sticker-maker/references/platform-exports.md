# Platform exports

Platform limits drift. Verify the current official specification when the prompt names a platform; do not rely on remembered dimensions, formats, frame limits, or byte limits.

Export rules:

1. Keep `source/frames/`, `source/motion.json`, and `sticker.webp` unchanged.
2. Write every platform derivative beneath `exports/<platform>/`.
3. Preserve frame order and per-frame durations unless the platform rejects them.
4. Resize proportionally and retain a transparent safe area where the platform supports alpha.
5. If the platform requires GIF, inspect palette banding, matte color, edge halos, and text readability after conversion.
6. If a byte limit forces quality reduction, reduce metadata and redundant colors first, then dimensions or frame count; do not silently remove the semantic hold.
7. Record the verified source URL, verification date, export parameters, and resulting byte size in an export report.
8. Build animated GIF derivatives from the reviewed RGBA source frames, not from `sticker.webp`; transcoding an already compressed animation compounds artifacts.
9. Use one shared palette across GIF frames so stable surfaces do not change color between frames. Prefer the highest palette size that satisfies the platform byte limit.
10. Derive a required static preview from the longest semantic-hold frame unless the motion plan names a better representative frame. If the animation contains exact text, prefer a frame where that text is complete.
11. Require the aggregate package status, automatic review, and visual review to all pass before release export. A legacy or partial report with only top-level `status: pass` is not enough.

Use `scripts/export_platform_gif.py` for constrained GIF plus optional preview PNG exports. It refuses incomplete review state by default and writes all three source-review states into a report beside each GIF, such as `01.export-report.json`, so batch exports do not overwrite one another. `--allow-unreviewed` is a diagnostic escape hatch, not a release mode. Re-open the resulting GIF and preview at actual target size; a byte-limit pass alone does not validate palette banding, binary-alpha edges, or text readability.

Do not create a platform directory when no platform or extra format was requested.
