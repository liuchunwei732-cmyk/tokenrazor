"""TokenRazor — AI 编程的上下文智能编排层。

不只省 Token，更让 AI 看懂你的项目。
中文生态、隐私优先、全栈覆盖、双向优化。

模块：
    Pruner          — CoT 剪枝引擎（输出侧优化）
    TerminalFilter  — 终端输出过滤器（输入侧优化）
    ProjectContext  — 项目感知引擎
    detect_project  — 便捷项目检测
"""

__version__ = "0.2.0"
__author__ = "Kevin Liu"

from .core import Pruner, Report, split_cot_answer
from .input_filter import TerminalFilter
from .context import ProjectContext, detect_project

__all__ = [
    "Pruner",
    "Report",
    "split_cot_answer",
    "TerminalFilter",
    "ProjectContext",
    "detect_project",
]
