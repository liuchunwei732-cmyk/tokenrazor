const vscode = require('vscode');
const { execSync } = require('child_process');

/**
 * TokenRazor VS Code 扩展
 *
 * 功能:
 * - 右键菜单 "剪枝选中文本" — 调用 tokenrazor prune
 * - 编辑器标题栏 "剪枝当前文件" — 处理整个文件
 * - 命令面板 "运行演示" — 展示 TokenRazor 效果
 */

function activate(context) {
    console.log('TokenRazor 扩展已激活 🧹');

    // 获取配置
    function getConfig() {
        const config = vscode.workspace.getConfiguration('tokenrazor');
        return {
            model: config.get('model', 'gpt-4o'),
            strategies: config.get('strategies', ['filler', 'dead_end', 'parallel_enum']),
            cliPath: config.get('cliPath', 'tokenrazor'),
        };
    }

    // 运行 tokenrazor CLI
    function runTokenRazor(text, model) {
        const cfg = getConfig();
        const strategies = cfg.strategies.join(',');
        const cmd = `echo ${JSON.stringify(text)} | ${cfg.cliPath} prune --model ${model || cfg.model} --strategy ${strategies} --json 2>/dev/null`;

        try {
            const stdout = execSync(cmd, { encoding: 'utf-8', timeout: 30000 });
            return JSON.parse(stdout);
        } catch (err) {
            // fallback: 管道可能在大文本下有问题，试文件模式
            const fs = require('fs');
            const tmpFile = `/tmp/tokenrazor-vscode-${Date.now()}.txt`;
            fs.writeFileSync(tmpFile, text, 'utf-8');
            try {
                const cmd2 = `${cfg.cliPath} prune "${tmpFile}" --model ${model || cfg.model} --strategy ${strategies} --json 2>/dev/null`;
                const stdout2 = execSync(cmd2, { encoding: 'utf-8', timeout: 30000 });
                fs.unlinkSync(tmpFile);
                return JSON.parse(stdout2);
            } catch (err2) {
                fs.unlinkSync(tmpFile);
                throw new Error(`TokenRazor 执行失败: ${err2.message}`);
            }
        }
    }

    // 显示结果
    function showResult(text, result, label) {
        const pruned = result.pruned_text || result.pruned || '';
        const stats = result.compression || result.stats || {};
        const cost = result.cost || {};

        // 在新建文档中显示剪枝结果
        const doc = vscode.workspace.openTextDocument({
            content: `// TokenRazor 剪枝结果 — ${label}
// 原始: ${stats.original_tokens || '?'} tokens
// 剪后: ${stats.pruned_tokens || '?'} tokens
// 节省: ${stats.saved_tokens || '?'} tokens (${stats.saved_percent || '?'}%)
// 模型: ${cost.model || '?'}
// 节省费用: $${(cost.saved_cost || 0).toFixed(6)}
// ═══════════════════════════════════════

${pruned}
            `.trim(),
            language: 'plaintext',
        });

        doc.then(d => {
            vscode.window.showTextDocument(d);
            const saved = stats.saved_tokens || 0;
            const pct = stats.saved_percent || 0;
            vscode.window.showInformationMessage(
                `TokenRazor: 节省 ${saved} tokens (${pct}%) 💰 $${(cost.saved_cost || 0).toFixed(6)}`,
                '查看详情'
            ).then(selection => {
                if (selection === '查看详情') {
                    vscode.commands.executeCommand('markdown.showPreviewToSide', d.uri);
                }
            });
        });
    }

    // 命令 1: 剪枝选中文本
    const pruneSelection = vscode.commands.registerCommand('tokenrazor.pruneSelection', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('没有打开的编辑器');
            return;
        }

        const selection = editor.selection;
        const text = editor.document.getText(selection);

        if (!text || text.trim().length === 0) {
            vscode.window.showErrorMessage('请先选中要剪枝的文本');
            return;
        }

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'TokenRazor 剪枝中...',
            cancellable: false,
        }, async () => {
            try {
                const result = runTokenRazor(text);
                showResult(text, result, '选中文本');
            } catch (err) {
                vscode.window.showErrorMessage(`TokenRazor 错误: ${err.message}`);
            }
        });
    });

    // 命令 2: 剪枝当前文件
    const pruneFile = vscode.commands.registerCommand('tokenrazor.pruneFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('没有打开的编辑器');
            return;
        }

        const text = editor.document.getText();
        if (!text || text.trim().length === 0) {
            vscode.window.showErrorMessage('当前文件为空');
            return;
        }

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'TokenRazor 剪枝中...',
            cancellable: false,
        }, async () => {
            try {
                const result = runTokenRazor(text);
                showResult(text, result, editor.document.fileName);
            } catch (err) {
                vscode.window.showErrorMessage(`TokenRazor 错误: ${err.message}`);
            }
        });
    });

    // 命令 3: 运行演示
    const demo = vscode.commands.registerCommand('tokenrazor.demo', async () => {
        const demoText = `好的，我来分析这个需求并给出实现方案。

首先让我想想这个功能的核心逻辑是什么。
这个功能需要处理用户上传的 CSV 文件，解析后存入数据库。

让我再梳理一下数据流向。
用户上传 → 文件校验 → 格式转换 → 数据清洗 → 批量插入 → 结果返回。

方案一：同步处理。
用户上传后等待处理完成。优点：实现简单。缺点：大文件阻塞。

方案二：异步处理。
上传后立即返回。优点：体验好。缺点：需要消息队列。

方案三：混合方案。
小文件同步，大文件异步。优点：平衡方案。

我选择方案三作为最终方案，因为它平衡了实现成本和用户体验。

让我再想想有没有遗漏的边界情况。
嗯，空文件、CSV 格式错误、数据库连接失败都需要处理。

好的，这些边界都考虑到了。现在开始写代码。
答案：选择方案三`;

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'TokenRazor 演示中...',
            cancellable: false,
        }, async () => {
            try {
                const result = runTokenRazor(demoText, 'gpt-4o');
                showResult(demoText, result, '内置演示');
            } catch (err) {
                vscode.window.showErrorMessage(`TokenRazor 错误: ${err.message}`);
            }
        });
    });

    context.subscriptions.push(pruneSelection, pruneFile, demo);
}

function deactivate() {}

module.exports = { activate, deactivate };
