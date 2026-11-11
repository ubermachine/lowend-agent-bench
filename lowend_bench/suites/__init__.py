"""
Comprehensive benchmark suites package.
"""

from lowend_bench.suites.diff_editing import run_diff_suite, DiffTestResult
from lowend_bench.suites.tool_calling import run_tool_suite, ToolTestResult
from lowend_bench.suites.frontier_v4 import run_frontier_v4_suite
from lowend_bench.suites.trace_replay import run_trace_replay_suite
from lowend_bench.suites.vault_challenge import run_vault_challenge_suite
from lowend_bench.suites.context_stress import run_context_suite, ContextStressResult
from lowend_bench.suites.adversarial_agent import run_adversarial_suite, AdversarialTestResult

__all__ = [
    "run_diff_suite",
    "DiffTestResult",
    "run_tool_suite",
    "ToolTestResult",
    "run_frontier_v4_suite",
    "run_trace_replay_suite",
    "run_vault_challenge_suite",
    "run_context_suite",
    "ContextStressResult",
    "run_adversarial_suite",
    "AdversarialTestResult",
]
