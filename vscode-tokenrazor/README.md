# TokenRazor VS Code 扩展

在 VS Code 里直接使用 TokenRazor 剪枝 AI 输出，右键即用。

## 功能

- **右键剪枝**：选中 AI 输出文本 → 右键 → `TokenRazor: 剪枝选中文本`
- **文件剪枝**：编辑器标题栏 → `TokenRazor: 剪枝当前文件`
- **命令面板**：`Ctrl+Shift+P` → `TokenRazor: 运行演示`

剪枝结果在新标签中打开，顶部显示 token 节省统计。

## 安装

```bash
# 确保 tokenrazor CLI 已安装
pip install tokenrazor

# 验证
tokenrazor --version
```

在 VS Code 中安装本扩展后即可使用。

## 配置

设置 → 搜索 `tokenrazor`：

| 设置 | 默认值 | 说明 |
|------|--------|------|
| `tokenrazor.model` | `gpt-4o` | 费用估算模型 |
| `tokenrazor.strategies` | `filler,dead_end,parallel_enum` | 剪枝策略 |
| `tokenrazor.cliPath` | `tokenrazor` | CLI 路径 |

## 开发

```bash
cd vscode-tokenrazor
code .                    # 在 VS Code 中打开
F5                       # 启动扩展开发模式
```

## 发布

```bash
npm install -g @vscode/vsce
vsce package             # 打包为 .vsix
vsce publish             # 发布到 marketplace
```
