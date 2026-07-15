# Motion plan

Write `motion.json` before packaging. Use this minimum shape:

```json
{
  "id": "short-sticker-id",
  "prompt": "Original natural-language request",
  "reference_image": "path/to/reference.png",
  "canvas": [1024, 1024],
  "loop": true,
  "identity_lock": {
    "subject": "Primary subject",
    "fixed": ["signature silhouette", "palette", "fixed marks"],
    "flexible": ["eyes", "pose", "temporary effects"],
    "forbidden": ["identity drift", "unrequested anatomy or props"]
  },
  "generation_plan": {
    "anchors": ["neutral", "new organic pose"],
    "deterministic": ["text", "translation", "opacity", "timing"]
  },
  "transparency": {
    "strategy": "existing-alpha or chroma-key",
    "work_color": "#RRGGBB or null"
  },
  "frames": [
    {
      "file": "frames/000.png",
      "duration_ms": 140,
      "description": "What changes and why this frame exists"
    }
  ]
}
```

When a deterministic high-frame render exists in the packaged `source/` directory, add this optional sibling of `frames`:

```json
"render": {
  "frame_dir": "rendered-frames",
  "frame_count": 48,
  "frame_durations_ms": [30, 40, 30],
  "total_duration_ms": 1600
}
```

The duration array must contain one positive integer per rendered PNG and sum to `total_duration_ms`. `frame_dir` must be relative to packaged `source/` and may not escape it. The shortened array above only illustrates timing variation; a real 48-frame track must contain 48 duration values. A render track is optional derived evidence, not a replacement for the 4–8 authored semantic keyframes.

Planning rules:

- Commit to one primary semantic beat. Treat secondary effects as support.
- Use 4–8 unique frames by default; do not duplicate identical frames to simulate a hold. Increase `duration_ms` instead.
- Reserve 400–700 ms for the frame that communicates the meaning most clearly.
- Generate only anchors that cannot be obtained safely through deterministic transforms.
- If a rejected full anchor contributes a usable local component, record it explicitly as a component source together with the approved base anchor and deterministic extraction rule. Do not list the rejected image as an approved full anchor.
- Render exact text outside the image generator unless organic text deformation is itself the requested effect.
- Default to a loop. Plan the final recovery frame against the first frame rather than treating it as an afterthought.
- Keep companion objects visually subordinate unless the prompt explicitly makes them co-subjects.
- For physical contact, place a companion against the subject's local surface under its footprint; a global alpha bounding box is not a reliable contact plane for curved, notched, or deformed subjects.
- Keep a high-frame render track only when interpolation or deterministic compositing adds visible value. Review its timing and visual result separately from the authored keyframes.
