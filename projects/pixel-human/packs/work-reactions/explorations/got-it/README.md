# `收到 / GOT IT!` 独立探索

- 状态：`exploration_complete / v05_selected`
- 工作框：`48×48 RGBA`
- 约束：无五官、整像素、二值 Alpha、最近邻审阅
- 基准：批准母版 `identity/masters/master-v1-32.png`

本目录只比较 `S01 收到` 的文字叙事、气泡结构与入场方式。用户最终选择 `v05-chat-card` 进入 [`../../releases/v1/`](../../releases/v1/)；原始版本与其他探索继续保留作追溯，不进入首发包。v06 是第一版混合方案，v07 在保留同样视觉和动画的同时，把聊天框及尾巴恢复到原版精确距离。所有候选最终语义帧均长停。

## 统一审阅入口

- [七案深浅背景动画对比](review/comparison-light-dark.gif)
- [`50×50` 七案深浅背景动画对比](review/comparison-50-light-dark.gif)
- [最终帧深浅背景对比](review/comparison-final-light-dark.png)
- [原版 / v05 / v06 重点动画对比](review/focus-original-v05-v06-light-dark.gif)
- [原版 / v05 / v06 最终帧对比](review/focus-original-v05-v06-final-light-dark.png)
- [原版 / v05 / v06 / v07 距离对比](review/focus-original-v05-v06-v07-light-dark.gif)
- [原版 / v05 / v06 / v07 最终帧](review/focus-original-v05-v06-v07-final-light-dark.png)
- [浅色逐帧表](review/frame-contact-sheet-light.png)
- [深色逐帧表](review/frame-contact-sheet-dark.png)
- [确定性生成清单](manifest.json)

统一图从左到右、逐帧表从上到下均为下列顺序。

## 方案比较

| 顺序 | 候选 | 文字过程 | 框体与入场 | 主要判断 |
| --- | --- | --- | --- | --- |
| 1 | `v01-chamfer-typewriter` | `G → GO → GOT → I → IT → IT!` | 右上切角气泡先从说话端展开 | 逐字符最完整，语义清楚，节奏较细 |
| 2 | `v02-split-word-chips` | `GOT → IT!` | 两块独立词条依次弹出，第二块承担主尾巴 | 单词层级最强，像一句干脆确认 |
| 3 | `v03-comic-burst` | `GOT → IT!` | 三段放大的棱角爆发框，长尖角明确指向角色 | 力度最大，但更像喊话，可能偏离冷面人格 |
| 4 | `v04-slide-caption` | `GOT → GOT IT → GOT IT!` | 横向对话轨从尾巴处展开 | 一行可读，入场利落；横条视觉占用最大 |
| 5 | `v05-chat-card` | 输入点 `…` 后切为 `GOT / IT!` | 左侧消息卡从角色一侧长出，带蓝色标题边 | 最像聊天产品，但“系统卡片”感略强 |
| 6 | `v06-right-linked-chat-card` | 输入点依次出现，再切为两行 `GOT / IT!` | 原版右侧黑色主边框 + v05 紫色错层/蓝色标题边 + 原版阶梯像素连线 | 同时保留角色发言方向和消息卡过程感 |
| 7 | `v07-original-distance-chat-card` | 与 v06 相同 | 主框和五个尾巴像素使用原版精确坐标，保留 v05 错层/蓝边 | 修正 v06 框体离头过近的问题 |

## 初步推荐排序

1. **`v02-split-word-chips`**：最适合“收到”的短促确认。两次词块入场天然对应 `GOT / IT!`，在 `50×50` 下比逐字符更稳，同时仍保留鲜明的角色发言尾巴。
2. **`v01-chamfer-typewriter`**：如果优先满足“像下班了一样逐渐出字”，这是最完整的版本；代价是前半段信息形成稍慢。
3. **`v04-slide-caption`**：一行文字最容易快速扫读，适合更冷静、UI 化的工作聊天语气；横条会压低角色在画面里的主导性。
4. **`v05-chat-card`**：输入点到回复的过程叙事最好，但更像聊天软件组件，不如前两案像角色本人说话。
5. **`v03-comic-burst`**：动势强、轮廓辨识度高，适合强烈“收到！”；但爆发感与本角色克制、略慢的身份方向最不一致。

用户当前保留集合至少包括原始版本和 `v05-chat-card`。v06 保留为第一版混合追溯，v07 是按原版框头距离修正后的混合候选。

## 文件结构

每个 `candidates/<variant>/` 都包含：

- `frames/frame-XX.png`：`48×48` 透明源帧；
- `<variant>.apng`：透明动画；
- `<variant>-review.gif`：`480×480` 最近邻透明审阅；
- `<variant>-review-light-dark.gif`：`480×480` 深浅背景并排；
- `<variant>-review-50-light-dark.gif`：`50×50` 深浅背景并排。

## 复现

```bash
python3 projects/pixel-human/packs/work-reactions/explorations/got-it/render_variants.py
```

脚本固定读取批准母版并校验 SHA-256；每帧检查 `48×48 RGBA`、二值 Alpha 和允许色板，`manifest.json` 记录每张透明源帧的 SHA-256。
