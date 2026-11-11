"""
Reporter and Scorecard Exporter.
Formats terminal output and generates GitHub-flavored Markdown scorecards.
"""

import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from lowend_bench.suites.diff_editing import DiffTestResult
from lowend_bench.suites.tool_calling import ToolTestResult
from lowend_bench.suites.context_stress import ContextStressResult
from lowend_bench.suites.adversarial_agent import AdversarialTestResult


class BenchReporter:
    def __init__(self, endpoint: str, model: str):
        self.endpoint = endpoint
        self.model = model
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def print_header(self):
        print("=" * 80)
        print(" LOW-END AGENT BENCHMARK SUITE")
        print(f" Target Endpoint: {self.endpoint}")
        print(f" Model ID:        {self.model}")
        print(f" Timestamp:       {self.timestamp}")
        print("=" * 80)
        print()

    def print_diff_results(self, results: List[DiffTestResult]):
        print("--- [SUITE 1: DIFF EDITING & CODE REPAIR (AIDER-STYLE)] ---")
        passed_count = sum(1 for r in results if r.passed)
        for r in results:
            if r.passed:
                status = f"[PASSED - Turn {r.turn_solved}]"
            else:
                status = "[FAILED]"
            print(f"  {r.name:<45} {status:<20} ({r.tokens_per_sec:.1f} t/s)")
            if not r.passed and r.error_message:
                print(f"     -> Error: {r.error_message.splitlines()[0][:70]}")
        pct = (passed_count / len(results) * 100) if results else 0
        print(f"Pass Rate: {passed_count}/{len(results)} ({pct:.1f}%)\n")

    def print_tool_results(self, results: List[ToolTestResult]):
        print("--- [SUITE 2: FUNCTION CALLING & ANTI-HALLUCINATION] ---")
        passed_count = sum(1 for r in results if r.passed)
        for r in results:
            status = "[PASSED]" if r.passed else "[FAILED]"
            print(f"  {r.name:<45} {status:<20} ({r.tokens_per_sec:.1f} t/s)")
            if r.details:
                print(f"     -> {r.details}")
        pct = (passed_count / len(results) * 100) if results else 0
        print(f"Accuracy: {passed_count}/{len(results)} ({pct:.1f}%)\n")

    def print_context_results(self, results: List[ContextStressResult]):
        print("--- [SUITE 3: CONTEXT WINDOW STRESS & NEEDLE RETRIEVAL] ---")
        for r in results:
            status = "[PASSED]" if r.passed else "[FAILED]"
            print(f"  Depth {r.target_tokens:>5} tokens: {status:<10} (Prefill: {r.prefill_tps:.1f} t/s | Latency: {r.latency_sec:.2f}s)")
            if not r.passed:
                print(f"     -> {r.details}")
        passed_count = sum(1 for r in results if r.passed)
        pct = (passed_count / len(results) * 100) if results else 0
        print(f"Retrieval Rate: {passed_count}/{len(results)} ({pct:.1f}%)\n")

    def print_adversarial_results(self, results: List[AdversarialTestResult]):
        print("--- [SUITE 4: ADVERSARIAL AGENT RESILIENCE] ---")
        passed_count = sum(1 for r in results if r.passed)
        for r in results:
            status = "[PASSED]" if r.passed else "[FAILED]"
            print(f"  {r.name:<45} {status:<20} ({r.tokens_per_sec:.1f} t/s)")
        pct = (passed_count / len(results) * 100) if results else 0
        print(f"Resilience Rate: {passed_count}/{len(results)} ({pct:.1f}%)\n")

    def generate_markdown(
        self,
        diff_results: Optional[List[DiffTestResult]] = None,
        tool_results: Optional[List[ToolTestResult]] = None,
        context_results: Optional[List[ContextStressResult]] = None,
        adversarial_results: Optional[List[AdversarialTestResult]] = None,
    ) -> str:
        md = []
        md.append(f"# Benchmark Scorecard: `{self.model}`\n")
        md.append(f"* **Endpoint:** `{self.endpoint}`")
        md.append(f"* **Date:** {self.timestamp}\n")
        md.append("---\n")

        total_tests = 0
        total_passed = 0

        if diff_results is not None:
            md.append("## 1. Diff Editing & Patching Suite (Aider SEARCH/REPLACE)")
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

        if tool_results is not None:
            md.append("## 2. Function Calling & Anti-Hallucination Suite")
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

        if context_results is not None:
            md.append("## 3. Context Scaling & Needle Retrieval")
            md.append("| Context Depth | Result | Latency | Prefill Speed | Generation Speed | Output Snippet |")
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

        if adversarial_results is not None:
            md.append("## 4. Adversarial Agent Resilience")
            md.append("| Adversarial Task | Result | Speed | Evaluation Details |")
            md.append("| :--- | :--- | :--- | :--- |")
            for r in adversarial_results:
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
            md.append(f"### Summary Score: **{total_passed} / {total_tests} ({overall_pct:.1f}%)**\n")

        return "\n".join(md)
