# Visual QA

Run every applicable check before declaring the package complete.

## Identity

- Compare every anchor and the contact sheet with the reference image.
- 角色签名轮廓必须结合母版判断。
- Confirm fixed marks, palette, material, face or functional anchors, and proportions remain recognizable.
- Treat automatic image metrics as candidate signals, not final identity judgments.

## Meaning and timing

- Confirm the animation communicates the requested meaning without its filename or an explanation.
- Confirm text is exact, readable, correctly ordered, and visible long enough.
- Confirm the primary semantic frame has the longest intentional hold.
- Confirm anticipation, action, hold, and recovery do not introduce an unrelated second meaning.
- Replay the loop several times and reject unintended jumps, flashes, or position resets.

## Alpha and composition

- Inspect edges over light, dark, and checkerboard backgrounds.
- Reject background remnants, work-color spill, bright halos, clipped details, and canvas-edge contact.
- Confirm every source frame uses the same RGBA canvas and subject baseline unless motion requires otherwise.
- Confirm shadows do not become opaque background patches.
- For salvaged local components, inspect the composited boundary on light and dark backgrounds and reject seams, duplicated features, leftover source pixels, or base-subject drift.
- For pressing, sitting, carrying, or contact actions, reject unintended air gaps and implausible deep intersections at the semantic hold. Judge contact against the local silhouettes, not only global bounding boxes.

## Small-size readability

- Inspect the semantic hold at 50×50 and at the target platform's smallest display size.
- Treat 50×50 as a stress test for the signature silhouette, main expression, and primary semantic signal; do not require long text to remain letter-perfect at that size.
- Require exact text to remain readable at the target platform's actual smallest display size. If that size is not yet known, record platform text readability as pending instead of using 50×50 as a substitute.
- Remove decorative signals that compete with the primary subject when reduced.

## Recording the decision

After review, update `qa/report.json`:

- Set `visual_review.status` to `pass` or `fail`.
- Add concise notes for identity, meaning, loop, alpha, and small-size checks.
- Set the top-level `status` to `pass` only when both automatic and visual review pass.
- Treat every repack as a new review boundary: the generated report resets visual review to pending and must be reviewed again.
