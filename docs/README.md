# 文档入口

这是仓库唯一的文档入口。仓库面向多主体、多母版和多套表情包生产；Agent 必须先确定任务属于哪个主体，再读取对应项目，不能把方芯规则套到像素小人或其他未来主体上。

更新时间：`2026-07-14`

## 当前项目

| 内部 ID | 状态 | 当前事实 | 入口 |
| --- | --- | --- | --- |
| `fangxin` | 第二套微信候选待提交 | 方芯身份与 v6 母版已锁定；《方芯上班中》已通过微信发布链路；《方芯回你了》12 张 GIF、品牌素材与发布 QA 已完成，状态为 `ready_for_submission` | [`../projects/fangxin/README.md`](../projects/fangxin/README.md) |
| `pixel-human` | 规划中 | 与真人无关、公开名待定的原创像素主体；当前图片仍是概念参考，不是母版；先锁定身份并验证 3 张代表性试片 | [`../projects/pixel-human/README.md`](../projects/pixel-human/README.md) |
| `motherboard2` | 概念候选 | 只保留青绿色 2.5D 方形生物概念图；尚未命名、没有批准母版，不进入生产 | [`../projects/motherboard2/README.md`](../projects/motherboard2/README.md) |
| `$animated-sticker-maker` | `v0.5` | 方芯与微信导出已验证；飞书不作为门槛；待像素小人完成跨风格试片后评估 `v1` | [`current/skill-contract.md`](current/skill-contract.md) |

## 当前工作

1. 提交者在微信后台复核实时规格并上传《方芯回你了》v1 候选；平台正式受理并通过后更新为 `published`，不修改已完成的《方芯上班中》。
2. 评审像素小人研究材料，锁定身份规范、原生像素网格和正式母版，再制作 3 张代表性动态试片。
3. `motherboard2` 保持概念状态，除非用户明确启动该主体。

## 权威顺序

发生冲突时按下面顺序处理：

1. 用户在当前任务中的明确决定。
2. `docs/current/` 中负责该跨项目主题的文档。
3. 目标主体 `projects/<subject>/README.md` 和它指向的身份或表情包文档。
4. `.agents/skills/animated-sticker-maker/` 的实际运行规则；若与 [`current/skill-contract.md`](current/skill-contract.md) 冲突，先修复冲突。
5. `docs/guides/` 中与当前操作相关的指南。

任何 `archive/`、`research/` 或概念参考都没有当前决策权。

## 最小阅读路径

| 任务 | 必读 | 按需补充 |
| --- | --- | --- |
| 判断仓库当前在做什么 | 本文档 | [`current/project-model.md`](current/project-model.md) |
| 修改目录、归属或项目模型 | [`current/project-model.md`](current/project-model.md)、[`../CONTEXT.md`](../CONTEXT.md) | 受影响主体 README |
| 规划方芯后续系列 | [`../projects/fangxin/README.md`](../projects/fangxin/README.md)、[`../projects/fangxin/packs/README.md`](../projects/fangxin/packs/README.md) | [`../projects/fangxin/identity/spec.md`](../projects/fangxin/identity/spec.md) |
| 查方芯已完成首包 | [`../projects/fangxin/packs/shangbanzhong/README.md`](../projects/fangxin/packs/shangbanzhong/README.md) | 动作卡或生成指南 |
| 继续像素小人 | [`../projects/pixel-human/README.md`](../projects/pixel-human/README.md) | 该项目 `research/` 中的指定材料 |
| 查看未来 2.5D 主体概念 | [`../projects/motherboard2/README.md`](../projects/motherboard2/README.md) | 仅在用户明确启动时读取概念图 |
| 修改通用 Skill 契约 | [`current/skill-contract.md`](current/skill-contract.md) | `.agents/skills/animated-sticker-maker/SKILL.md` |
| 显式运行 `$animated-sticker-maker` | `.agents/skills/animated-sticker-maker/SKILL.md` | [`current/skill-contract.md`](current/skill-contract.md) |
| 导出微信发布包 | [`guides/platform-exports.md`](guides/platform-exports.md) | 目标表情包 README；提交前重新核实官方规则 |
| 查被替代方案 | [`archive/README.md`](archive/README.md) | 仅追溯，不用于执行 |

## 目录职责

```text
voxel-max/
├── CONTEXT.md                # 跨项目术语
├── docs/
│   ├── README.md             # 状态与任务路由
│   ├── current/              # 跨项目当前决定
│   ├── guides/               # 跨项目操作指南
│   └── archive/              # 历史文档
├── projects/                 # 按主体隔离的生产项目
└── .agents/skills/           # 通用、手动触发的仓库 Skill
```

一个决定只保留在一个负责文档中，其他位置只链接。状态变化必须同时更新本文档与拥有该状态的项目 README。
