# 《小同事上班记》v1

- 角色公开名：像素小同事
- 专辑公开名：小同事上班记
- 状态：`ready_for_submission`
- 发布平台：微信表情专辑
- 发布方式：免费，不开通赞赏
- 官方规格复核日期：`2026-07-15`

## 最终选择

`S09 磕头` 已采用用户确认的块状手掌优化版；生产实现见 [`../../work/v6/`](../../work/v6/)，旧版与探索对照继续保留。

| 顺序 | 语义 | 发布来源 |
| --- | --- | --- |
| 1 | 收到 | `v05-chat-card` |
| 2 | 工作中 | 当前通过版本 |
| 3 | 稍等 | 当前通过版本 |
| 4 | 开会中 | v5 |
| 5 | 搞定了 | 当前通过版本 |
| 6 | 无语 | 当前通过版本 |
| 7 | 崩了 | 当前通过版本 |
| 8 | 下班了 | 当前通过版本 |
| 9 | 磕头 | v6 块状手掌优化版 |

## 投稿文案

- 专辑名称：`小同事上班记`
- 表情介绍：`像素小同事陪你过完一个工作日：收到、忙碌、开会、搞定、崩溃，再准时下班。`
- 发布方式：免费
- 赞赏功能：不开通

## 文件入口

- [`source/manifest.json`](source/manifest.json)：平台中立 `48×48 RGBA` 源包清单。
- [`source/review/selected-pack-light-dark.gif`](source/review/selected-pack-light-dark.gif)：九张深浅背景动画总览。
- [`wechat/manifest.json`](wechat/manifest.json)：微信投稿文件、SHA-256、体积、时序和 QA 结果。
- [`wechat/stickers/`](wechat/stickers/)：按上传顺序排列的 9 张 `240×240` GIF。
- [`wechat/brand/`](wechat/brand/)：`750×400` 横幅、`240×240` 透明封面和 `50×50` 透明聊天图标。
- [`wechat/review/brand-assets-preview.png`](wechat/review/brand-assets-preview.png)：品牌素材聚合预览。

## QA 结论

1. 9 张 GIF 均为 `240×240`，永久循环，并保留源帧数量和逐帧时序。
2. 单张 GIF 均远低于 `500 KB`；横幅、封面和聊天图标也低于各自上限。
3. 封面与聊天图标使用透明背景；横幅不含文字、不使用透明或纯白背景。
4. 原尺寸、`50×50`、浅色、深色、逐帧表和聚合动画均已复核。

本发布包由 [`../../scripts/build_release_v1.py`](../../scripts/build_release_v1.py) 确定性生成。重新生成只替换 `source/` 与 `wechat/`，不会删除本文档。
