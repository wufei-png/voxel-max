# `磕头` 手臂与落地姿态优化

- 状态：`exploration_complete / v02_selected`
- 原发布源：`v01-current`
- 选定版本：`v02-grounded-palms`，已固化为 [`../../work/v6/`](../../work/v6/)
- 工作框：`48×48 RGBA`

当前版落地帧两侧的淡黄色短条原本代表手掌，但手掌过薄，且与前臂的连接不够清楚，容易读成用于区分“崩了”的装饰冲击线。`v02-grounded-palms` 删除这类附加符号，把区分依据收敛到动作本身：

1. 全程保持正面对称，不使用侧脸。
2. 不出现键盘。
3. 紫色前臂连续伸到地面，淡黄色手掌改为可辨认的块状接触面。
4. 从坐直、准备、前倾到伏地，再抬起并重复下拜。
5. 落地帧只显示全黑头顶，不增加无来源的冲击线。

## 审阅

- [当前版 / 优化版深浅背景动态对照](review/current-vs-grounded-palms-light-dark.gif)
- [`50×50` 动态对照](review/current-vs-grounded-palms-50-light-dark.gif)
- [浅色逐帧对照](review/frame-contact-sheet-light.png)
- [深色逐帧对照](review/frame-contact-sheet-dark.png)

对照图左列或第一行为当前版，右列或第二行为优化版。

本探索由 [`render_variants.py`](render_variants.py) 确定性生成；用户确认 v02 后，生产实现已固化到 [`../../scripts/render_pack_v6.py`](../../scripts/render_pack_v6.py)，并替换 [`../../releases/v1/`](../../releases/v1/) 的 S09。
