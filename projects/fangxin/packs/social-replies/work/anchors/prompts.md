# 代表性试片锚点生成记录

生成后端：Codex 内置 `$imagegen`  
身份参考：`projects/fangxin/identity/masters/fangxin-v6.png`  
工作底：均匀纯洋红 `#FF00FF`，后期确定性去底

本文档只记录《方芯回你了》的试片锚点，不属于通用 Skill 提示模板。

## S03 无语

结果：`source-chroma/s03-wuyu-generated-v2.png`  
去底：`rgba/s03-wuyu-generated-v2-rgba.png`  
决定：拒绝为整张锚点。核心比例相对身份规范偏大，软塌差异不足以稳定排除困倦；只保留为轮廓方向参考。最终试片使用 `rgba/half-eyes-rgba.png` 做确定性局部软塌。

最终迭代提示：

```text
Use case: identity-preserve
Asset type: corrected animation anchor for Voxel Max S03 speechless
Input images: Image 1 is the edit target; Image 2 is the strict identity reference.
Primary request: Correct only the pose. Return the mascot to a front-facing, vertically oriented composition with the top edge approximately horizontal. Do not rotate or tilt the whole character as a rigid object. Instead, make the lower body softly sag and pool slightly toward the viewer's left, while the upper-right notch region stays upright and recognizable. The deformation must look like a coherent soft block losing support asymmetrically: left lower side compressed and drooping, right side still holding shape. Keep the body mostly square and tall enough for the core and eyes. The expression is dry speechless resignation, not sleep, injury, or being crushed.
Preserve from Image 2: exact turquoise hue and soft 2.5D material, right-top inward notch, centered core with external rounded-square frame, two dark glossy physical eye modules and their spacing, front lighting language.
Expression: restrained half-closed horizontal eyes; dim cyan-gray core.
Backdrop: keep the perfectly flat uniform #FF00FF chroma-key background, no shadow, no floor, no gradient, no reflection.
Constraints: change only the deformation and orientation; single centered subject; no text, no symbols, no props, no smoke, no glitch, no hands, no legs, no mouth, no eyebrows, no second subject; no magenta spill; generous padding.
Avoid: rigid whole-body tilt, fully prone rectangle, melting puddle, flat app icon, mirrored notch, missing notch, stretched core, changed eye spacing.
```

## S07 加油

结果：`source-chroma/s07-jiayou-generated-v1.png`  
去底：`rgba/s07-jiayou-generated-v1-rgba.png`  
决定：批准为 S07 试片专用前倾锚点。它不是新母版，也不自动批准给其他表情复用。

生成提示：

```text
Use case: stylized-concept
Asset type: identity-preserving animation anchor for Voxel Max S07 encouragement sticker
Input image: Image 1 is the strict identity reference and must remain the same subject.
Primary request: Create one isolated pose of the exact same turquoise 2.5D rounded-square AI mascot at the peak of a restrained forward-and-up encouragement push. The body has just compressed to gather energy and now leans forward toward the viewer while rising slightly, like a soft block confidently urging someone onward. No running, no limbs, no rocket, no speed lines. The action must feel supportive and determined, not like the mascot itself completed a task.
Scene/backdrop: perfectly flat solid #FF00FF chroma-key background, uniform edge to edge, no floor plane, no shadow, no reflection, no gradient, no texture.
Identity invariants: preserve the right-top inward notch on the same side and keep it clearly readable; preserve the centered rounded-square cyan-white status core and external frame; preserve two dark glossy physical eye modules, their spacing, and their material; preserve turquoise body hue #62E6D8, deep teal shading, soft 2.5D thickness, rounded silhouette, and original lighting language.
Pose and expression: subtle 2.5D forward pitch with the upper body visually leading and the lower body acting as a compressed base; focused eyes slightly narrowed inward but not > <; bright cyan-white core, no success green.
Composition: one centered subject on a square canvas with generous padding and no edge contact.
Constraints: one subject, one primary motion, no text, no Chinese, no English, no symbols, no props, no smoke, no trail, no extra pixels, no hands, no legs, no mouth, no eyebrows, no second character, no complex UI, no white background, no cast shadow, no magenta reflected onto the subject.
Avoid: success celebration, jumping straight upward, running pose, green completion core, happy ^ ^ eyes, whole-body rigid rotation, mirrored notch, missing notch, stretched core, changed eye spacing, flat app icon, Minecraft or pixel-art style.
```
