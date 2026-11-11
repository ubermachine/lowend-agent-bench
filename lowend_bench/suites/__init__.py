"""
Benchmark suites package.
"""

from lowend_bench.suites.diff_editing import run_diff_suite, DiffTestResult
from lowend_bench.suites.tool_calling import run_tool_suite, ToolTestResult
from lowend_bench.suites.context_stress import run_context_suite, ContextStressResult
from lowend_bench.suites.adversarial_agent import run_adversarial_suite, AdversarialTestResult

__all__ = [
    "run_diff_suite",
    "DiffTestResult",
    "run_tool_suite",
    "ToolTestResult",
    "run_context_suite",
    "ContextStressResult",
    "run_adversarial_suite",
    "AdversarialTestResult",
]
