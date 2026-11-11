"""
Benchmark Suite Runner and Orchestrator.
Discovers and executes standard, frontier, and custom pluggable suites.
"""

import os
from typing import Optional, List
from lowend_bench.client import LLMClient
from lowend_bench.base import TestResult
from lowend_bench.suites import (
    run_diff_suite,
    run_tool_suite,
    run_frontier_v4_suite,
    run_trace_replay_suite,
    run_vault_challenge_suite,
    run_context_suite,
)
from lowend_bench.registry import (
    load_declarative_cases,
    load_custom_python_cases,
    get_all_registered_tests,
    validate_test_case,
)
from lowend_bench.reporter import BenchReporter


def run_all(
    endpoint: str = "http://127.0.0.1:8080/v1",
    api_key: str = "none",
    model: str = "default",
    suite: str = "all",
    max_reflection: int = 2,
    timeout: float = 120.0,
    hardware: str = "",
    export_path: Optional[str] = None,
    cases_dir: str = "cases",
    custom_dir: str = "custom_cases",
):
    client = LLMClient(endpoint=endpoint, api_key=api_key, model=model, timeout=timeout)

    print(f"[i] Checking connectivity to endpoint: {endpoint} ...")
    if not client.health_check():
        print("[!] Warning: Health check endpoint did not return 200 OK. Attempting to proceed anyway...")
    else:
        print("[✓] Server is reachable and healthy.")

    reporter = BenchReporter(endpoint=endpoint, model=model, hardware=hardware)
    reporter.print_header()

    diff_res = None
    tool_res = None
    frontier_res = None
    trace_res = None
    vault_res = None
    context_res = None
    custom_res = None

    # Load custom / declarative test cases
    load_declarative_cases(cases_dir)
    load_custom_python_cases(custom_dir)

    # 1. Diff Suite
    if suite in ("all", "diff"):
        diff_res = run_diff_suite(client, max_reflection=max_reflection)
        reporter.print_diff_results(diff_res)

    # 2. Tool Calling Suite
    if suite in ("all", "tools"):
        tool_res = run_tool_suite(client)
        reporter.print_tool_results(tool_res)

    # 3. Frontier V4 Suite
    if suite in ("all", "frontier", "frontier_v4"):
        frontier_res = run_frontier_v4_suite(client)
        reporter.print_suite_results("SUITE 3: FRONTIER CHALLENGE V4 (ADVERSARIAL AGENT SCENARIOS)", frontier_res)

    # 4. Trace Replay Suite
    if suite in ("all", "trace", "trace_replay"):
        trace_res = run_trace_replay_suite(client)
        reporter.print_suite_results("SUITE 4: REAL-WORLD TRACE REPLAY (LIBGEN 22K VIEWPORT)", trace_res)

    # 5. Vault Challenge
    if suite in ("all", "vault", "vault_challenge"):
        vault_res = run_vault_challenge_suite(client)
        reporter.print_suite_results("SUITE 5: FRONTIER VAULT CHALLENGE (MULTI-TIER EXTRACTION)", vault_res)

    # 6. Context Stress Suite
    if suite in ("all", "context"):
        context_res = run_context_suite(client)
        reporter.print_context_results(context_res)

    # 7. Custom Registered Tests
    registered = get_all_registered_tests()
    if registered and suite in ("all", "custom"):
        custom_res = []
        for test_case in registered:
            print(f"  Running custom test: {test_case.name} ...")
            res = test_case.run(client)
            custom_res.append(res)
        reporter.print_suite_results("SUITE 7: COMMUNITY & CUSTOM TEST CASES", custom_res)

    # Export report if requested
    if export_path:
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
        md_content = reporter.generate_markdown(
            diff_results=diff_res,
            tool_results=tool_res,
            frontier_results=frontier_res,
            trace_results=trace_res,
            vault_results=vault_res,
            context_results=context_res,
            custom_results=custom_res,
        )
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[✓] Markdown scorecard successfully exported to: {export_path}")


def validate_suites(cases_dir: str = "cases", custom_dir: str = "custom_cases") -> bool:
    """Validate all registered declarative and custom test cases for schema correctness."""
    print("=" * 80)
    print(" VALIDATING PLUGGABLE TEST CASES")
    print("=" * 80)

    decl_cases = load_declarative_cases(cases_dir)
    print(f"Loaded {len(decl_cases)} declarative cases from '{cases_dir}/'")

    py_cases = load_custom_python_cases(custom_dir)
    print(f"Loaded {len(py_cases)} custom Python cases from '{custom_dir}/'")

    all_cases = get_all_registered_tests()
    if not all_cases:
        print("[i] No custom test cases registered yet.")
        return True

    all_valid = True
    for case in all_cases:
        valid = validate_test_case(case)
        status = "[VALID]" if valid else "[INVALID]"
        print(f"  {case.name:<50} {status}")
        if not valid:
            all_valid = False

    if all_valid:
        print("\n[✓] All custom test cases passed schema and interface validation.")
    else:
        print("\n[-] Validation failures detected.")
    return all_valid
