# voxel-max

一个面向多主体、多母版和多套表情包的动态表情生产仓库。主体可以是人物、宠物、吉祥物、物体或 Logo；视觉语言可以是像素、2D、2.5D 或其他适合聊天场景的风格，不以方芯或像素小人为边界。

仓库同时维护两类内容：

- `projects/`：按主体隔离的身份规范、母版、表情包、工作资产和发布包。
- `.agents/skills/animated-sticker-maker/`：从静态参考与自然语言动作生成动态表情的通用 Skill；只在用户显式调用 `$animated-sticker-maker` 时加载。

Agent 和协作者统一从 [`docs/README.md`](docs/README.md) 开始。领域术语见 [`CONTEXT.md`](CONTEXT.md)，目录与归属规则见 [`docs/current/project-model.md`](docs/current/project-model.md)。
