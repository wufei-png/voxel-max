# `work-reactions` v2 动态候选

- 状态：`candidate_review`
- 工作框：`48×48`
- 数量：9
- 动作卡：[`../../motion-spec.md`](../../motion-spec.md)

v2 根据 v1 用户评审修改：缩小“开会中”右耳罩；“搞定了”从空白开始逐段绘制对号；“崩了”恢复侧趴键盘；新增与键盘无关、双手对称撑地且带落地冲击块的“磕头”；“下班了”改为 12 帧起身、背包、离场和 `下 / 下班 / 下班了` 逐字显示。

## 审阅入口

- [九张无标签深浅背景动画板](review/unlabeled-pack-review-light-dark.gif)
- [`50×50` 九张无标签深浅背景动画板](review/unlabeled-pack-review-50-light-dark.gif)
- [浅色逐帧接触表](review/frame-contact-sheet-light.png)
- [深色逐帧接触表](review/frame-contact-sheet-dark.png)
- [无标签顺序](review/order.md)
- [生成清单](manifest.json)

动画板左侧为浅色 3x3，右侧为相同顺序的深色 3x3。逐帧表每行一张；短动画在未使用的右侧列保持空白。“下班了”使用 12 帧和 `80–600ms` 分段时长，其他动作不被强行提高帧数。

本目录由 [`../../scripts/render_pack_v2.py`](../../scripts/render_pack_v2.py) 确定性生成。
