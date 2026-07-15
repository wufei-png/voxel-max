# `work-reactions` v1 动态候选

- 状态：`superseded_by_v2`
- 工作框：`48×48`
- 数量：8
- 动作卡：[`../../motion-spec.md`](../../motion-spec.md)

`S01 收到 / S02 工作中 / S07 崩了` 逐帧复用批准身份试片 v4。`S03 稍等 / S04 开会中 / S05 搞定了 / S06 无语 / S08 下班了` 是首轮新增候选。

用户评审后，本版已被 [`../v2/README.md`](../v2/README.md) 取代。

## 审阅入口

- [八张无标签深浅背景动画板](review/unlabeled-pack-review-light-dark.gif)
- [`50×50` 八张无标签深浅背景动画板](review/unlabeled-pack-review-50-light-dark.gif)
- [浅色逐帧接触表](review/frame-contact-sheet-light.png)
- [深色逐帧接触表](review/frame-contact-sheet-dark.png)
- [无标签顺序](review/order.md)
- [生成清单](manifest.json)

八宫格上半为浅色背景、下半为深色背景；每个背景内从左到右、从上到下均为 `S01–S08`。逐帧表每行一张，每行从左到右为 `00–04` 帧。

本目录由 [`../../scripts/render_pack_v1.py`](../../scripts/render_pack_v1.py) 确定性生成。
