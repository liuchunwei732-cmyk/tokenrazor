/// TokenRazor CLI — Rust 实现
///
/// 命令:
///   prune    — 剪枝 AI 输出 (CoT 脱水)
///   filter   — 过滤终端输出
///   demo     — 内置演示
///   tokens   — 统计 Token
///   models   — 列出支持的模型

use std::io::Read;

use clap::{Parser, Subcommand};

mod models;
mod pricing;
mod tokenizer;
mod scanner;
mod pruner;
mod reporter;
mod filter;

use pruner::Pruner;

/// TokenRazor — AI 编程的上下文智能编排层
#[derive(Parser)]
#[command(name = "tokenrazor", version = "0.5.0", about = "🧹 TokenRazor — 不只省 Token，更让 AI 看懂你的项目")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// 剪枝 AI 输出（CoT 脱水）
    Prune {
        /// 文本文件路径
        file: Option<String>,

        /// 直接传入文本
        #[arg(short = 't', long)]
        text: Option<String>,

        /// 剪枝策略
        #[arg(short = 's', long, default_value = "filler,dead_end,parallel_enum",
              value_delimiter = ',')]
        strategy: Vec<String>,

        /// 模型名（用于费用估算）
        #[arg(long, default_value = "gpt-4o")]
        model: String,

        /// JSON 格式输出
        #[arg(long)]
        json: bool,

        /// 输出到文件
        #[arg(short = 'o', long)]
        output: Option<String>,
    },

    /// 过滤终端输出
    Filter {
        /// 日志文件路径
        file: Option<String>,

        /// 直接传入文本
        #[arg(short = 't', long)]
        text: Option<String>,
    },

    /// 内置演示，展示 TokenRazor 效果
    Demo {
        /// 模型名
        #[arg(long, default_value = "gpt-4o")]
        model: String,
    },

    /// 统计 Token 数
    Tokens {
        /// 文本文件路径
        file: Option<String>,

        /// 直接传入文本
        #[arg(short = 't', long)]
        text: Option<String>,
    },

    /// 列出支持的模型及定价
    Models {
        /// JSON 格式输出
        #[arg(long)]
        json: bool,
    },
}

fn read_input(file: Option<String>, text: Option<String>) -> Result<String, String> {
    if let Some(t) = text {
        return Ok(t);
    }
    if let Some(f) = file {
        return std::fs::read_to_string(&f)
            .map_err(|e| format!("读取文件失败 '{}': {}", f, e));
    }
    // 从 stdin 读取
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf)
        .map_err(|e| format!("读取输入失败: {}", e))?;
    if buf.trim().is_empty() {
        return Err("请通过文件、--text 参数或管道提供输入。".to_string());
    }
    Ok(buf)
}

fn cmd_prune(file: Option<String>, text: Option<String>, strategies: Vec<String>,
             model: &str, json: bool, output: Option<String>) {
    let content = match read_input(file, text) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("错误: {}", e);
            std::process::exit(1);
        }
    };

    let strategies: Vec<&str> = strategies.iter().map(|s| s.as_str()).collect();
    let pruner = Pruner::new(&strategies);
    let result = pruner.prune(&content);

    let output_str = if json {
        let report = reporter::json_report(&result, model);
        serde_json::to_string_pretty(&report).unwrap()
    } else {
        let report = reporter::text_report(&result, model);
        format!("{}\n{}\n{}", report, "─".repeat(50), result.pruned)
    };

    if let Some(path) = output {
        std::fs::write(&path, &output_str)
            .unwrap_or_else(|e| eprintln!("写入文件失败: {}", e));
        println!("结果已写入: {}", path);
    } else {
        println!("{}", output_str);
    }
}

fn cmd_filter(file: Option<String>, text: Option<String>) {
    let content = match read_input(file, text) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("错误: {}", e);
            std::process::exit(1);
        }
    };

    let result = filter::filter_log(&content);
    println!("{}", result.filtered);
}

fn cmd_demo(model: &str) {
    let demo_text = r"好的，我来分析这个需求并给出实现方案。

首先让我想想这个功能的核心逻辑是什么。
ok，这个功能需要处理用户上传的 CSV 文件，解析后存入数据库。

让我再梳理一下数据流向。
嗯，用户上传 → 文件校验 → 格式转换 → 数据清洗 → 批量插入 → 结果返回。

好的，现在我来考虑实现细节。

方案一：同步处理。
用户上传后等待处理完成。
优点：实现简单，逻辑清晰。
缺点：大文件会阻塞请求。

好的，再来看方案二：异步处理。
上传后立即返回，后台 Task 处理。
优点：用户体验好，支持大文件。
等等，缺点呢？需要消息队列，实现复杂。

现在考虑方案三：混合方案。
小文件同步，大文件异步。
优点：兼顾简单和体验。

好的我选择方案三作为最终方案。

让我再想想有没有遗漏的边界情况。
嗯，如果是空文件怎么办？需要校验。
如果 CSV 格式不对呢？需要友好提示。
如果数据库连接失败呢？需要重试机制。

好的，这些边界都考虑到了。

现在我来实现代码。
先定义文件处理函数，明确输入输出。
然后写上传接口，处理多文件并发。
好了开始写代码。";

    let pruner = Pruner::new(&["filler", "dead_end", "parallel_enum"]);
    let result = pruner.prune(demo_text);

    println!();
    println!("╔══════════════════════════════════════════════════╗");
    println!("║       TokenRazor 实时演示                      ║");
    println!("╚══════════════════════════════════════════════════╝");
    println!();

    // 原始文本预览
    println!("📥 原始 AI 输出（截取前 200 字）：");
    println!("{}", "─".repeat(50));
    let preview: String = demo_text.chars().take(200).collect();
    println!("{}...", preview);
    println!();

    println!("📤 剪枝后输出：");
    println!("{}", "─".repeat(50));
    let postview: String = result.pruned.chars().take(300).collect();
    println!("{}", postview);
    println!();

    // 统计
    let cost = pricing::cost_report(result.original_tokens, result.pruned_tokens, model);
    println!("{}", "═".repeat(50));
    println!("  📊 本次演示统计");
    println!("  {:>20}: {}", "原始 Token", result.original_tokens);
    println!("  {:>20}: {}", "剪后 Token", result.pruned_tokens);
    println!("  {:>20}: {}", "节约 Token", result.saved_tokens());
    println!("  {:>20}: {:.1}%", "压缩率", result.saved_percent());
    println!("  {:>20}: {}", "本次节省费用", pricing::format_cost(cost.saved_cost));
    println!("  {:>20}: {} 处", "移除冗余段", result.removed_spans.len());
    println!("{}", "═".repeat(50));
    println!();
    println!("💡 用法: command | tokenrazor prune --model gpt-4o");
    println!();
}

fn cmd_tokens(file: Option<String>, text: Option<String>) {
    let content = match read_input(file, text) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("错误: {}", e);
            std::process::exit(1);
        }
    };

    let n = tokenizer::count_tokens(&content);
    println!("Tokens: {}", n);
}

fn cmd_models(json: bool) {
    if json {
        let list: Vec<serde_json::Value> = models::MODELS.iter().map(|m| {
            serde_json::json!({
                "id": m.id,
                "name_cn": m.name_cn,
                "input_per_1m": m.input_per_1m,
                "output_per_1m": m.output_per_1m,
            })
        }).collect();
        println!("{}", serde_json::to_string_pretty(&list).unwrap());
    } else {
        println!("{:25} {:20} {:>10} {:>10}", "模型 ID", "中文名", "输入 $/1M", "输出 $/1M");
        println!("{}", "─".repeat(70));
        for m in models::MODELS {
            println!("{:25} {:20} {:>10.2} {:>10.2}",
                m.id, m.name_cn, m.input_per_1m, m.output_per_1m);
        }
    }
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Prune { file, text, strategy, model, json, output } => {
            cmd_prune(file, text, strategy, &model, json, output);
        }
        Commands::Filter { file, text } => {
            cmd_filter(file, text);
        }
        Commands::Demo { model } => {
            cmd_demo(&model);
        }
        Commands::Tokens { file, text } => {
            cmd_tokens(file, text);
        }
        Commands::Models { json } => {
            cmd_models(json);
        }
    }
}
