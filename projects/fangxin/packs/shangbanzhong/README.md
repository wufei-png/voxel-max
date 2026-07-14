# 《方芯上班中》

内部 ID：`shangbanzhong`  
表情包状态：`completed`  
完成日期：`2026-07-14`  
发布平台：微信表情开放平台

这是方芯的第一套正式动态表情包。8 张视觉内容、动作、源包和微信发布版均已完成，微信真实发布链路已通过。飞书没有适用的个人发布平台，不属于本包发布目标。

## 1. 冻结清单

| 包内编号 | 内容 | 微信含义词 | 源包目录 |
| --- | --- | --- | --- |
| S01 | 收到 | 收到 | `output/s01-shoudao/` |
| S02 | 别催 | 别催 | `output/s02-biecui-square-to-squint/` |
| S03 | 思考中 | 思考中 | `output/s03-sikaozhong/` |
| S04 | 跑通了 | 跑通了 | `output/s04-paotongle/` |
| S05 | 卡住了 | 卡住了 | `output/s05-kazhule/` |
| S06 | CPU 烧了 | 过热了 | `output/s06-cpushaole/` |
| S07 | 已读但装死 | 已读装死 | `output/s07-yiduzhuangsi/` |
| S08 | 被 Bug 压扁 | 压扁了 | `output/s08-bug-squash/` |

这些编号只在本包内有效。方芯后续系列从自己的 S01 开始，不向本包追加 S09。

## 2. 当前真值

- 方芯身份：[`../../identity/spec.md`](../../identity/spec.md)
- 正式母版：[`../../identity/masters/fangxin-v6.png`](../../identity/masters/fangxin-v6.png)
- 本包逐帧动作：[`motion-spec.md`](motion-spec.md)
- 本包生图提示与锚点策略：[`generation-guide.md`](generation-guide.md)
- 平台无关源包：`output/<sticker>/`
- 已批准工作锚点和 QA 材料：`work/`
- 微信发布包：`releases/v1/wechat/`
- 本包确定性生产脚本：`scripts/`

每个源包保留：

```text
output/<sticker>/
├── sticker.webp
├── source/
│   ├── frames/
│   └── motion.json
├── qa/
└── exports/wechat/
```

## 3. 生产方式

本包采用“少量批准锚点 + 确定性合成”：

- 生成模型只负责真正的新姿态、遮挡关系或有机形变。
- Pillow、NumPy 和 FFmpeg 负责去底、形变、文字、特效、时序、预览和打包。
- 平台导出从通过审核的 RGBA 源帧产生，不从 WebP 二次转码。
- 所有表情均通过自动 QA、人工视觉 QA 和聚合状态检查。

脚本写死了本包的 S01-S08、方芯锚点和发布文案，因此属于本包，不代表通用 Skill API。

## 4. 微信发布资料

- 专辑名：`方芯上班中`
- 专辑介绍：`方芯是一枚认真上班的小芯片，负责收到、处理中、跑通，以及偶尔卡住和装死。`
- 发布方式：免费
- 艺术家与版权署名：由提交者在平台后台管理，不写入仓库

微信发布包包含 8 张 GIF、封面、聊天图标、详情页横幅、清单和发布 QA。平台规格以 [`../../../../docs/guides/platform-exports.md`](../../../../docs/guides/platform-exports.md) 为准，并在重新提交前再次核实。

## 5. 完成后的变更规则

- 不为规划新系列而改写本包语义清单、动作卡或发布版。
- 修复可复现的资产、脚本或文档错误时，必须重新运行受影响的自动与视觉 QA。
- 方芯后续主题在 [`../README.md`](../README.md) 规划并建立新包。
- 本包完成不等于通用 Skill 已完成跨主体验证；Skill 版本状态由 [`../../../../docs/current/skill-contract.md`](../../../../docs/current/skill-contract.md) 负责。
