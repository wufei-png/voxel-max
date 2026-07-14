# Animated Sticker Production

This context describes the shared language for producing reusable subjects and one or more animated sticker packs from each subject.

## Language

**主体（Subject）**:
能够在一套或多套表情包中保持同一身份的主要表现对象；可以是人物、宠物、吉祥物、物体或 Logo，不默认等同于人形角色。
_Avoid_: 用“角色”泛指所有主体、表情包、风格

**主体项目（Subject Project）**:
围绕一个主体组织身份、研究、母版和多套表情包的独立工作边界。
_Avoid_: 表情包、母版目录、风格模板

**内部 ID（Internal ID）**:
主体或表情包在仓库中的稳定英文标识；公开名称可以尚未确定或日后改变。
_Avoid_: 临时目录名、必须面向用户展示的名称

**身份规范（Identity Spec）**:
定义主体固定特征、允许变化和禁止漂移项的当前规则。
_Avoid_: 动作卡、平台规格、研究笔记

**母版（Master）**:
已经审核通过、可用于锁定主体身份的基准图；同一主体可以拥有多个互补母版。
_Avoid_: 概念参考、任意底图、样张、生成过程图

**概念参考（Concept Reference）**:
用于探索主体方向、但尚未获得母版地位的输入图或候选图。
_Avoid_: 母版、身份真值

**风格规范（Style Spec）**:
描述轮廓、材质、网格、色板、光影等视觉语言的规则；风格不是主体身份，也不是单张母版。
_Avoid_: 母版、主体、滤镜名称

**表情包（Sticker Pack）**:
属于一个主体、围绕一个主题或使用场景组织、可以独立规划和发布的一组表情。
_Avoid_: 主体项目、跨主体素材池

**表情（Sticker）**:
在一套表情包内表达一个主要聊天语义的单个静态或动态作品。
_Avoid_: 关键帧、整套表情包、发布平台文件

**工作资产（Working Asset）**:
制作过程中的锚点、拆分组件、中间帧或 QA 材料；它不自动成为身份或发布真值。
_Avoid_: 母版、发布包

**源包（Source Package）**:
通过项目 QA、保留透明源帧和动作记录、可继续编辑与派生的平台无关表情产物。
_Avoid_: 工作目录、平台压缩文件

**发布包（Release Package）**:
从已审核源包派生、满足某个具体平台约束并包含必要发布材料的交付集合。
_Avoid_: 源包、未审核导出、整项主体项目
