# Changelog

## v0.5.1 (2026-05-29)

### Rust 版测试覆盖提升
- 测试从 48 提升至 68（+42%），新增 20 个测试
- pricing: 中文模型别名、大额计算、零节省场景
- tokenizer: 中英混合、标点符号、特殊字符
- pruner: 并行枚举、长文本分割、全策略测试
- reporter: 无节省报告、JSON 序列化验证

### VS Code 扩展
- 右键菜单剪枝（选中文本/整个文件）
- 命令面板演示入口
- 可配置模型/策略/CLI 路径
- 打包为 .vsix 文件，支持拖拽安装

### 网站
- 个人简历网站上线 GitHub Pages
- AI 岗位匹配器接入 DeepSeek API

### 商业级打磨
- 测试覆盖提升至 85%+（新增 CLI 测试和 reporter 测试）
- README 重构为产品导向的双语页面
- PyPI 构建验证通过（classifiers / README / LICENSE 完善）
- GitHub Actions CI 配置（自动测试 + 代码检查）
- CHANGELOG 和 LICENSE 文件正式化

### 功能改进
- terminal filter 适配更多真实场景（npm WARN / pip / docker build）
- ParallelEnum 策略重写为块感知算法，正确支持多行枚举条目
- 新增 `demo` 命令：内置真实场景演示，一步展示节省效果
- 新增 `integrate` 命令：生成 shell alias，一行 source 即可日常使用
- stdin 管道输入完全支持：`command | tokenrazor prune`

### 中文生态
- 新增 cnpm（淘宝镜像）工具链适配
- 新增 pip（国内源）工具链适配
- 新增中文脚手架（uni-app / Taro / Umi / ice.js）规则
- 国内镜像站自动识别（npmmirror / aliyun / tencent / huawei / ustc）

### 开发者体验
- 新增 `__main__.py`：支持 `python3 -m tokenrazor`
- CLI 默认裁剪策略增加 `parallel_enum`
- Reporter 输出增加费用节省可视化
- 费用计算器支持 20+ 模型定价，含别名映射

---

## v0.4.0 (2026-05-28)

- 日常可用管道支持
- demo / integrate 命令
- ParallelEnum 策略修复

## v0.3.0 (2026-05-28)

- Token 费用计算器
- ParallelEnum 剪枝策略
- 中文工具链规则扩充

## v0.2.0 (2026-05-28)

- 项目感知引擎
- 终端输入过滤
- 全栈工具链规则库（10 个工具链）
- CLI 多命令支持

## v0.1.0 (2026-05-27)

- 初始版本
- CoT 剪枝核心（filler + dead_end）
- DeepSeek R1 / OpenAI o1 格式支持
