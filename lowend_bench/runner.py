"""
Benchmark Suite Runner and Orchestrator.
"""

from typing import Optional
from lowend_bench.client import LLMClient
from lowend_bench.suites import (
    run_diff_suite,
    run_tool_suite,
    run_context_suite,
    run_adversarial_suite,
)
from lowend_bench.reporter import BenchReporter


def run_all(
    endpoint: str = "http://127.0.0.1:8080/v1",
    api_key: str = "none",
    model: str = "default",
    suite: str = "all",
    max_reflection: int = 2,
    timeout: float = 120.0,
    export_path: Optional[str] = None,
):
    client = LLMClient(endpoint=endpoint, api_key=api_key, model=model, timeout=timeout)

    print(f"[i] Checking connectivity to endpoint: {endpoint} ...")
    if not client.health_check():
        print(f"[!] Warning: Health check endpoint did not return 200 OK. Attempting to proceed anyway...")
    else:
        print("[✓] Server is reachable and healthy.")

    reporter = BenchReporter(endpoint=endpoint, model=model)
    reporter.print_header()

    diff_res = None
    tool_res = None
    context_res = None
    adv_res = None

    if suite in ("all", "diff"):
        diff_res = run_diff_suite(client, max_reflection=max_reflection)
        reporter.print_diff_results(diff_res)

    if suite in ("all", "tools"):
        tool_res = run_tool_suite(client)
        reporter.print_tool_results(tool_res)

    if suite in ("all", "context"):
        context_res = run_context_suite(client)
        reporter.print_context_results(context_res)

    if suite in ("all", "adversarial"):
        adv_res = run_adversarial_suite(client)
        reporter.print_adversarial_results(adv_res)

    if export_path:
        md_content = reporter.generate_markdown(
            diff_results=diff_res,
            tool_results=tool_res,
            context_results=context_res,
            adversarial_results=adv_res,
        )
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[✓] Markdown scorecard successfully exported to: {export_path}")
