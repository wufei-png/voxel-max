# 像素小人 v1 身份动态试片

- 状态：`superseded_by_v2`
- 身份输入：[`../../masters/master-v1-32.png`](../../masters/master-v1-32.png)
- 工作框：`48×48`
- 试片数量：3
- 文字：无
- 首发平台：微信优先，但本目录资产保持平台中立

本轮不是表情包生产，也不创建 `S01` 等包内编号。用户评审后认为“卡住了”含义不清、“收到”需要由角色发出的 `Got it!` 字符，并将“我看一下”改名为“工作中”。本轮已由 [`../v2/README.md`](../v2/README.md) 取代，只保留为试片迭代追溯。

## 试片

| 内部 ID | 语义 | 主动作 | 主要风险 |
| --- | --- | --- | --- |
| `received` | 收到 | 头部下点、回弹、再停在确认姿态 | 幅度太小会像普通待机 |
| `take-a-look` | 我看一下 | 头部前压，双手落到屏幕边并交替轻动 | 屏幕或手臂可能压过角色身份 |
| `stuck` | 卡住了 | 头身轻微错位、身体冻结、汗滴下落 | 容易被读成泛紧张，而不是卡住 |

三张统一使用 5 帧、4 个独特姿态、总时长 `1.2s`：

| 帧 | 时长 | 作用 |
| --- | ---: | --- |
| `00` | `480ms` | 第一帧即主语义姿态并长停 |
| `01` | `120ms` | 离开主姿态 |
| `02` | `120ms` | 动作峰值或信息变化 |
| `03` | `120ms` | 回弹或第二次微动作 |
| `04` | `360ms` | 回到主语义姿态并闭环 |

## 审阅入口

建议先看无标签随机顺序板，再查看单张名称：

- [无标签深浅背景审阅 GIF](review/unlabeled-review-light-dark.gif)
- [`50×50` 无标签深浅背景审阅 GIF](review/unlabeled-review-50-light-dark.gif)
- [审阅列顺序](review/order.md)
- [浅色背景逐帧接触表](review/frame-contact-sheet-light.png)
- [深色背景逐帧接触表](review/frame-contact-sheet-dark.png)

接触表从上到下依次为 `收到 / 我看一下 / 卡住了`，每行从左到右为 `00–04` 帧。

单张输出：

- `received/received.apng`、`received/received-review.gif`、深浅与 `50×50` 审阅 GIF
- `take-a-look/take-a-look.apng`、`take-a-look/take-a-look-review.gif`、深浅与 `50×50` 审阅 GIF
- `stuck/stuck.apng`、`stuck/stuck-review.gif`、深浅与 `50×50` 审阅 GIF

每个子目录的 `frames/` 保存 `48×48` RGBA 原生帧。[`manifest.json`](manifest.json) 记录批准母版哈希、帧序列、时长、色板和审阅顺序；所有内容由 [`../../../scripts/render_identity_trials.py`](../../../scripts/render_identity_trials.py) 确定性生成。

## 通过门槛

1. 三张在无名称、无文字条件下能够互相区分。
2. 黑发、空白脸区、颈肩比例、紫衣和 4 像素中缝仍属于同一角色。
3. 第一帧在静止时已有主要语义，循环没有明显跳变。
4. 原生帧只有完全透明或完全不透明 Alpha；透明边缘不闪烁。
5. `50×50` 与深浅背景中主体不坍缩，道具不能压过角色。

任一项未通过，先修改动作和构图；不得用五官或文字直接补救。三张全部通过后，才进入首包 8 张规划。
