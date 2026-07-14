# 微信发布资料

状态：`ready_for_submission`；等待提交者在微信表情开放平台上传

## 后台字段

- 专辑名称：`方芯回你了`
- 专辑介绍：`方芯不只会上班，也会认真回你：同意、拒绝、笑死、感谢、鼓励，以及好好说晚安。`
- 发布方式：免费
- 艺术家与版权署名：沿用《方芯上班中》的提交者资料，在后台填写，不从仓库复制

## 表情上传顺序

| 序号 | 文件 | 含义词 |
| --- | --- | --- |
| 01 | `stickers/01-ok.gif` | 好的 |
| 02 | `stickers/02-buxing.gif` | 不行 |
| 03 | `stickers/03-wuyu.gif` | 无语 |
| 04 | `stickers/04-xiaosi.gif` | 笑死 |
| 05 | `stickers/05-xiexie.gif` | 谢谢 |
| 06 | `stickers/06-meishi.gif` | 没事 |
| 07 | `stickers/07-jiayou.gif` | 加油 |
| 08 | `stickers/08-xinkule.gif` | 辛苦了 |
| 09 | `stickers/09-lihai.gif` | 厉害 |
| 10 | `stickers/10-baoqian.gif` | 抱歉 |
| 11 | `stickers/11-zhendejiade.gif` | 真的假的 |
| 12 | `stickers/12-wanan.gif` | 晚安 |

## 品牌素材

- 表情封面图：`cover.png`，S04 开心眼姿态，无文字
- 聊天面板图标：`chat-icon.png`，开心眼与青白核心
- 详情页横幅：`banner.png`，深青背景上的 S01、S04、S12，无文字

## 上传前检查

1. 在微信后台重新确认表情数量、GIF 尺寸与体积、封面、图标和横幅的实时限制。
2. 按上表顺序上传 12 张 GIF，并逐张填写唯一含义词。
3. 上传三张品牌素材，确认平台预览未发生裁切、白边或透明背景异常。
4. 核对专辑名称、介绍、免费发布方式以及艺术家和版权资料。
5. 投稿前对照 `qa/contact-sheet.png` 和 `qa/all-frames-contact-sheet.png` 做最后一次人工检查。

`qa/`、`manifest.json` 和本说明不上传。微信正式受理并通过后，再将本包与上级项目状态从 `ready_for_submission` 更新为 `published`。
