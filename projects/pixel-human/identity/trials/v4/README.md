# 像素小人 v4 身份动态试片

- 状态：`approved_motion / crashed_reassigned_to_kowtow`
- 用户验收：`2026-07-15`
- 身份输入：[`../../masters/master-v1-32.png`](../../masters/master-v1-32.png)
- 工作框：`48×48`
- 试片数量：3

v4 只重做“崩了”的倒地朝向：人物保持正面中轴，从批准母版坐直姿态开始向前俯冲；脸区在下落中缩短，最终完全隐藏，只显示压在键盘上的全黑头顶。它取代 v3 的侧脸落下版本。

`收到`与`工作中`逐帧复用 v2，不作视觉修改。用户已确认 v4 完成后三张试片动作门槛全部通过。后续包评审认为正面朝下更像“磕头”，因此该动作在当前首包中去掉键盘并改用于 `S09 磕头`；`S07 崩了` 改用 v3 的侧趴动作。

## 试片

| 内部 ID | 语义 | 主动作 | 结果 |
| --- | --- | --- | --- |
| `received` | 收到 | 点头并显示由角色发出的 `GOT / IT!` 气泡 | 通过 |
| `working` | 工作中 | 前倾并持续敲键盘 | 通过 |
| `crashed` | 崩了 | 从坐直正面姿态前倾，脸区收短，最终以全黑头顶正面趴在键盘上 | 通过 |

三张统一为 5 帧、4 个独特姿态、总时长 `1.2s`，时长为 `480 / 120 / 120 / 120 / 360ms`。首末帧相同，兼顾静态首帧和闭环。

## 审阅入口

- [无标签深浅背景审阅 GIF](review/unlabeled-review-light-dark.gif)
- [`50×50` 无标签深浅背景审阅 GIF](review/unlabeled-review-50-light-dark.gif)
- [浅色背景逐帧接触表](review/frame-contact-sheet-light.png)
- [深色背景逐帧接触表](review/frame-contact-sheet-dark.png)
- [审阅列顺序](review/order.md)

接触表从上到下依次为 `收到 / 工作中 / 崩了`，每行从左到右为 `00–04` 帧。每个子目录保存原生帧、APNG 和三类 GIF 审阅输出。[`manifest.json`](manifest.json) 与 [`../../../scripts/render_identity_trials_v4.py`](../../../scripts/render_identity_trials_v4.py) 负责确定性复现。
