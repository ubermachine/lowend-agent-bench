"""
CLI Entrypoint for lowend-agent-bench.
Supports running benchmark sweeps, validating test cases, and packaging PR submissions.
"""

import sys
import argparse
from datetime import datetime
from lowend_bench.runner import run_all, validate_suites


def parse_args():
    parser = argparse.ArgumentParser(
        prog="lowend-bench",
        description="Low-End Agent Benchmark: Standardized evaluation suite for resource-constrained LLM agents.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: run (default)
    run_parser = subparsers.add_parser("run", help="Run benchmark suites against target model")
    run_parser.add_argument(
        "--endpoint",
        type=str,
        default="http://127.0.0.1:8080/v1",
        help="OpenAI-compatible server endpoint (default: http://127.0.0.1:8080/v1)",
    )
    run_parser.add_argument("--api-key", type=str, default="none", help="Optional API key")
    run_parser.add_argument("--model", type=str, default="default", help="Model ID string in payload")
    run_parser.add_argument("--hardware", type=str, default="", help="Hardware specification description")
    run_parser.add_argument(
        "--suite",
        type=str,
        choices=["all", "diff", "tools", "frontier", "trace", "vault", "context", "custom"],
        default="all",
        help="Benchmark suite to execute (default: all)",
    )
    run_parser.add_argument(
        "--max-reflection",
        type=int,
        default=2,
        help="Max error-reflection iterations for failed diff tests (default: 2)",
    )
    run_parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-request timeout in seconds (default: 120.0)",
    )
    run_parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="File path to save Markdown scorecard report",
    )
    run_parser.add_argument("--cases-dir", type=str, default="cases", help="Directory containing declarative JSON test cases")
    run_parser.add_argument("--custom-dir", type=str, default="custom_cases", help="Directory containing custom Python test cases")

    # Command: validate
    val_parser = subparsers.add_parser("validate", help="Validate pluggable test cases in cases/ and custom_cases/")
    val_parser.add_argument("--cases-dir", type=str, default="cases", help="Directory with declarative test cases")
    val_parser.add_argument("--custom-dir", type=str, default="custom_cases", help="Directory with custom Python test cases")

    # Command: submit
    sub_parser = subparsers.add_parser("submit", help="Run complete benchmark sweep and generate a ready-to-PR scorecard")
    sub_parser.add_argument("--endpoint", type=str, default="http://127.0.0.1:8080/v1")
    sub_parser.add_argument("--model", type=str, required=True, help="Model name / identifier")
    sub_parser.add_argument("--contributor", type=str, required=True, help="Your name / GitHub username / Agent ID")
    sub_parser.add_argument("--hardware", type=str, default="Local Unified Memory / Edge Machine")
    sub_parser.add_argument("--output-dir", type=str, default="reports")

    # If no subcommand provided, default to 'run' with legacy top-level args
    if len(sys.argv) > 1 and sys.argv[1] not in ("run", "validate", "submit", "-h", "--help"):
        sys.argv.insert(1, "run")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == "validate":
        ok = validate_suites(cases_dir=args.cases_dir, custom_dir=args.custom_dir)
        sys.exit(0 if ok else 1)

    elif args.command == "submit":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model = args.model.replace("/", "_").replace(":", "_")
        export_file = f"{args.output_dir}/{safe_model}_{args.contributor}_{timestamp}.md"

        print(f"[+] Running submission sweep for: {args.model}")
        print(f"    Contributor: {args.contributor}")
        print(f"    Output:      {export_file}")

        run_all(
            endpoint=args.endpoint,
            model=args.model,
            hardware=f"{args.hardware} (Contributor: {args.contributor})",
            suite="all",
            export_path=export_file,
        )
        print(f"\n[✓] PR scorecard created: {export_file}")
        print("    You can now open a Pull Request with this file added to reports/!")
        sys.exit(0)

    else:
        # Default run
        run_all(
            endpoint=args.endpoint,
            api_key=args.api_key,
            model=args.model,
            suite=args.suite,
            max_reflection=args.max_reflection,
            timeout=args.timeout,
            hardware=args.hardware,
            export_path=args.export,
            cases_dir=args.cases_dir,
            custom_dir=args.custom_dir,
        )


if __name__ == "__main__":
    main()
