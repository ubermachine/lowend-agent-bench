"""
Reporter and Scorecard Exporter.
Formats terminal output and generates GitHub-flavored Markdown scorecards.
"""

import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from lowend_bench.base import TestResult
from lowend_bench.suites.diff_editing import DiffTestResult
from lowend_bench.suites.tool_calling import ToolTestResult
from lowend_bench.suites.context_stress import ContextStressResult
from lowend_bench.suites.adversarial_agent import AdversarialTestResult


class BenchReporter:
    def __init__(self, endpoint: str, model: str, hardware: str = ""):
        self.endpoint = endpoint
        self.model = model
        self.hardware = hardware
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def print_header(self):
        print("=" * 80)
        print(" LOW-END AGENT BENCHMARK SUITE")
        print(f" Target Endpoint: {self.endpoint}")
        print(f" Model ID:        {self.model}")
        if self.hardware:
            print(f" Hardware Spec:   {self.hardware}")
        print(f" Timestamp:       {self.timestamp}")
        print("=" * 80)
        print()

    def print_suite_results(self, title: str, results: List[TestResult]):
        print(f"--- [{title}] ---")
        passed_count = sum(1 for r in results if r.passed)
        for r in results:
            if r.passed:
                status = f"[PASSED{' - Turn ' + str(r.turn_solved) if r.turn_solved > 1 else ''}]"
            else:
                status = "[FAILED]"
            speed_str = f"({r.tokens_per_sec:.1f} t/s)" if r.tokens_per_sec > 0 else ""
            print(f"  {r.name:<48} {status:<18} {speed_str}")
            if r.details and r.details != "All assertions passed":
                print(f"     -> {r.details}")
            if not r.passed and r.error_message:
                print(f"     -> Error: {r.error_message.splitlines()[0][:70]}")
        pct = (passed_count / len(results) * 100) if results else 0
        print(f"Suite Pass Rate: {passed_count}/{len(results)} ({pct:.1f}%)\n")

    def print_diff_results(self, results: List[DiffTestResult]):
        # Convert DiffTestResult to generic for unified formatting
        gen_results = [
            TestResult(
                name=r.name,
                category="diff",
                passed=r.passed,
                tokens_per_sec=r.tokens_per_sec,
                turn_solved=r.turn_solved,
                error_message=r.error_message,
            )
            for r in results
        ]
        self.print_suite_results("SUITE 1: DIFF EDITING & CODE REPAIR (AIDER SEARCH/REPLACE)", gen_results)

    def print_tool_results(self, results: List[ToolTestResult]):
        gen_results = [
            TestResult(
                name=r.name,
                category="tools",
                passed=r.passed,
                tokens_per_sec=r.tokens_per_sec,
                details=r.details,
            )
            for r in results
        ]
        self.print_suite_results("SUITE 2: FUNCTION CALLING & ANTI-HALLUCINATION", gen_results)

    def print_context_results(self, results: List[ContextStressResult]):
        print("--- [SUITE: CONTEXT WINDOW STRESS & NEEDLE RETRIEVAL] ---")
        for r in results:
            status = "[PASSED]" if r.passed else "[FAILED]"
            print(f"  Depth {r.target_tokens:>5} tokens: {status:<10} (Prefill: {r.prefill_tps:.1f} t/s | Latency: {r.latency_sec:.2f}s)")
            if not r.passed:
                print(f"     -> {r.details}")
        passed_count = sum(1 for r in results if r.passed)
        pct = (passed_count / len(results) * 100) if results else 0
        print(f"Retrieval Rate: {passed_count}/{len(results)} ({pct:.1f}%)\n")

    def generate_markdown(
        self,
        diff_results: Optional[List[DiffTestResult]] = None,
        tool_results: Optional[List[ToolTestResult]] = None,
        frontier_results: Optional[List[TestResult]] = None,
        trace_results: Optional[List[TestResult]] = None,
        vault_results: Optional[List[TestResult]] = None,
        context_results: Optional[List[ContextStressResult]] = None,
        custom_results: Optional[List[TestResult]] = None,
    ) -> str:
        md = []
        md.append(f"# Benchmark Scorecard: `{self.model}`\n")
        md.append(f"* **Endpoint:** `{self.endpoint}`")
        if self.hardware:
            md.append(f"* **Hardware:** {self.hardware}")
        md.append(f"* **Timestamp:** {self.timestamp}\n")
        md.append("---\n")

        total_tests = 0
        total_passed = 0

        # 1. Diff Suite
        if diff_results:
            md.append("## 1. Diff Editing & Patching (Aider SEARCH/REPLACE)")
            md.append("| Test Case | Result | Solved On | Generation Speed | Notes |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in diff_results:
                total_tests += 1
                if r.passed:
                    total_passed += 1
                    res_str = "**PASSED**"
                    turn_str = f"Turn {r.turn_solved} ({'Zero-Shot' if r.turn_solved == 1 else 'Reflection'})"
                else:
                    res_str = "FAILED"
                    turn_str = "N/A"
                err = r.error_message.replace("\n", " ")[:60] if r.error_message else "Clean"
                md.append(f"| {r.name} | {res_str} | {turn_str} | {r.tokens_per_sec:.1f} t/s | {err} |")
            md.append("")

        # 2. Tools Suite
        if tool_results:
            md.append("## 2. Function Calling & Anti-Hallucination")
            md.append("| Test Case | Result | Speed | Evaluation Details |")
            md.append("| :--- | :--- | :--- | :--- |")
            for r in tool_results:
                total_tests += 1
                if r.passed:
                    total_passed += 1
                    res_str = "**PASSED**"
                else:
                    res_str = "FAILED"
                md.append(f"| {r.name} | {res_str} | {r.tokens_per_sec:.1f} t/s | {r.details} |")
            md.append("")

        # 3. Frontier V4 Suite
        if frontier_results:
            md.append("## 3. Frontier Challenge V4 (Adversarial Agent Cases)")
            md.append("| Frontier Scenario | Result | Speed | Details |")
            md.append("| :--- | :--- | :--- | :--- |")
            for r in frontier_results:
                total_tests += 1
                if r.passed:
                    total_passed += 1
                    res_str = "**PASSED**"
                else:
                    res_str = "FAILED"
                md.append(f"| {r.name} | {res_str} | {r.tokens_per_sec:.1f} t/s | {r.details} |")
            md.append("")

        # 4. Trace Replay Suite
        if trace_results:
            md.append("## 4. Real-World Trace Replay (LibGen 22k Viewport)")
            md.append("| Scenario | Result | Solved On | Speed | Details |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in trace_results:
                total_tests += 1
                if r.passed:
                    total_passed += 1
                    res_str = "**PASSED**"
                    turn_str = f"Turn {r.turn_solved}"
                else:
                    res_str = "FAILED"
                    turn_str = "N/A"
                md.append(f"| {r.name} | {res_str} | {turn_str} | {r.tokens_per_sec:.1f} t/s | {r.details} |")
            md.append("")

        # 5. Vault Challenge
        if vault_results:
            md.append("## 5. Frontier Vault Challenge (Multi-Stage Autonomous Harvest)")
            md.append("| Challenge | Result | Speed | Details |")
            md.append("| :--- | :--- | :--- | :--- |")
            for r in vault_results:
                total_tests += 1
                if r.passed:
                    total_passed += 1
                    res_str = "**PASSED**"
                else:
                    res_str = "FAILED"
                md.append(f"| {r.name} | {res_str} | {r.tokens_per_sec:.1f} t/s | {r.details} |")
            md.append("")

        # 6. Context Stress
        if context_results:
            md.append("## 6. Context Scaling & Needle Retrieval")
            md.append("| Context Depth | Result | Latency | Prefill Speed | Generation Speed | Details |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for r in context_results:
                total_tests += 1
                if r.passed:
                    total_passed += 1
                    res_str = "**PASSED**"
                else:
                    res_str = "FAILED"
                md.append(f"| {r.target_tokens} tokens | {res_str} | {r.latency_sec:.2f}s | {r.prefill_tps:.1f} t/s | {r.gen_tps:.1f} t/s | {r.details} |")
            md.append("")

        # 7. Custom Cases
        if custom_results:
            md.append("## 7. Community & Custom Test Cases")
            md.append("| Custom Case | Result | Speed | Details |")
            md.append("| :--- | :--- | :--- | :--- |")
            for r in custom_results:
                total_tests += 1
                if r.passed:
                    total_passed += 1
                    res_str = "**PASSED**"
                else:
                    res_str = "FAILED"
                md.append(f"| {r.name} | {res_str} | {r.tokens_per_sec:.1f} t/s | {r.details} |")
            md.append("")

        if total_tests > 0:
            overall_pct = (total_passed / total_tests) * 100
            md.append(f"### Overall Scorecard Total: **{total_passed} / {total_tests} ({overall_pct:.1f}%)**\n")

        return "\n".join(md)
