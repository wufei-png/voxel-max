---
name: animated-sticker-maker
description: Make a transparent animated sticker package from one static reference image and one natural-language prompt.
---

# Animated Sticker Maker

Turn one reference image and one motion prompt into a short, transparent animated sticker. Derive the identity lock, motion plan, working background, frame timing, QA plan, and export settings internally; do not require the user to supply them.

Resolve every script and reference path against the directory containing this `SKILL.md`.

## Inputs and boundaries

Require only:

1. `reference_image`: one static image containing a clear primary subject.
2. `prompt`: natural language describing the intended expression, action, text, loop, or target platform.

Support people, pets, mascots, illustrations, objects, and logos. If the image has multiple plausible subjects and the prompt does not identify one, ask once before generating. Do not promise stable multi-subject acting, scene animation, or camera motion in v1.

Use `$imagegen` as the only supported generative raster backend. Use Pillow and NumPy scripts for deterministic processing. Do not make OpenCV a required dependency.

## Default package

Create this structure unless the prompt explicitly overrides it:

```text
output/<name>/
├── sticker.webp
├── source/
│   ├── frames/
│   │   ├── 000.png
│   │   └── ...
│   └── motion.json
├── qa/
│   ├── contact-sheet.png
│   └── report.json
└── exports/                  # only when a platform or extra format is requested
    └── <platform>/
```

Use `1024×1024` RGBA for both source frames and the default animated WebP. Use 4–8 unique frames, per-frame durations, a total duration of about 1.2–2.0 seconds, and a 400–700 ms hold on the clearest semantic frame. Loop by default. Do not create `preview.gif` unless requested or required by the target platform.

## Steps

### 1. Derive the identity lock

Inspect the reference at full size and small-icon size. Record the subject, signature silhouette, palette, material, facial or functional anchors, fixed marks, and forbidden drift. Separate identity features from incidental background details.

Complete this step only when every visible feature that makes the subject recognizable is classified as fixed, flexible, or removable.

### 2. Write the motion plan

Read [references/motion-plan.md](references/motion-plan.md). Convert the prompt into one primary semantic beat, a small set of anchor poses, deterministic transitions, exact text layers, frame durations, and loop behavior. Write the plan before producing final frames.

Use generation only for genuinely new poses, occlusion, or organic deformation. Use deterministic transforms for translation, scale, opacity, brightness, exact text, simple effects, timing, and packaging.

Complete this step only when each frame has one purpose and every requested semantic element appears in the plan.

### 3. Produce and approve anchors

Read the `$imagegen` instructions before generating. Always include the original reference when asking for a new anchor. Ask for a front-facing, isolated subject on either transparency or a flat high-distance work color. Generate the fewest anchors needed.

Inspect every anchor immediately against the identity lock. Reject identity drift before building temporal frames; do not hope that animation will hide it. Pause for user review only when a choice changes the subject's identity or the requested meaning, not for routine numeric tuning.

If a generated anchor preserves one clean local expression or prop but drifts as a whole, reject it as a full anchor. You may salvage only that isolated component onto an approved identity-stable anchor when its boundary can be extracted without seams or duplicate features. Record the rejected source as a component source, the extraction rule, and the approved base anchor in the motion plan; never relabel the rejected full image as approved.

Complete this step only when all full-frame anchors are individually usable and every salvaged component has an approved base, a bounded role, and a deterministic extraction method.

### 4. Build clean RGBA assets

If an anchor already has correct alpha, preserve it. Otherwise read [references/transparency.md](references/transparency.md), choose a work color far from the subject palette, and run `scripts/chroma_key.py`. Keep shadows separate when the prompt or platform needs independent shadow control.

Complete this step only when the subject has no opaque background, color spill, bright fringe, clipped protrusion, or canvas-edge contact.

### 5. Compose the animation

Create one RGBA PNG per unique frame. Preserve the subject's aspect ratio unless the motion explicitly calls for deformation. Keep exact text in deterministic layers so spelling, placement, and timing remain controlled. Favor anticipation, one clear semantic hold, and a short recovery over evenly timed motion.

When a companion object presses, sits on, or touches the subject, align it against the local silhouette beneath its footprint. Do not infer contact from the subject's global bounding-box edge when the surface is curved, notched, or deformed.

Complete this step only when the sequence reads correctly without filenames or explanation and the loop has no unintended jump.

### 6. Package and run automatic QA

Run:

```bash
python <skill-dir>/scripts/package_sticker.py \
  --frames-dir <working-frames> \
  --motion <motion.json> \
  --output <output/name>
```

Use the nonstandard timing or frame-count flags only when the user's prompt explicitly overrides the defaults. Do not continue to platform export when automatic QA fails.

Complete this step only when `sticker.webp`, copied source frames, `motion.json`, the contact sheet, and the automatic report all exist and the report passes.

Packaging replaces the generated QA report and therefore invalidates any earlier visual-review decision for that output. Re-run and record visual QA after every repack; never preserve a prior pass across changed frames.

### 7. Perform visual QA and deliver

Read [references/qa.md](references/qa.md). Review the animation, contact sheet, semantic hold, alpha edges on light and dark backgrounds, and the subject at small-icon size. Record the visual decision in `qa/report.json`; automatic checks do not replace this review.

Record the decision with:

```bash
python <skill-dir>/scripts/record_visual_review.py <output/name/qa/report.json> \
  --status pass \
  --identity "..." --meaning "..." --loop "..." --alpha "..." --small-size "..."
```

If a platform is requested, read [references/platform-exports.md](references/platform-exports.md), verify current official constraints, and write only derived files beneath `exports/<platform>/`. Do not resize or recompress the platform-neutral sources.

For a platform that accepts animated GIF, export from the reviewed package instead of the WebP:

```bash
python <skill-dir>/scripts/export_platform_gif.py \
  --package <output/name> \
  --platform <platform> \
  --size <WIDTHxHEIGHT> \
  --max-bytes <limit> \
  --preview-output <derived-preview.png> \
  --preview-max-bytes <preview-limit> \
  --spec-url <official-url> \
  --verified-on <YYYY-MM-DD>
```

The exporter requires the aggregate package status, automatic review, and visual review to all be `pass`. It preserves source timing, uses one shared GIF palette to reduce frame-to-frame color shimmer, chooses the highest tested color count that meets the byte limit, and records the source review states, export parameters, and hashes. Omit the preview arguments when the platform does not require one. Use `--allow-unreviewed` only for explicit diagnostics, never for a release deliverable. If no palette candidate fits, change size, timing, or frame count only through an explicit reviewed decision; do not silently degrade the semantic hold.

Complete the task only when the package is usable, the visual review is recorded, and every requested export passes its current platform constraints.

## Escalation rule

Ask the user only when a missing choice changes the intended subject, meaning, or irreversible public output. Make safe project-level adjustments to timing, position, scale, color-key thresholds, and compression without interrupting the run.
