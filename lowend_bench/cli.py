"""
CLI Entrypoint for lowend-agent-bench.
"""

import sys
import argparse
from lowend_bench.runner import run_all


def parse_args():
    parser = argparse.ArgumentParser(
        description="Low-End Agent Benchmark: Standardized evaluation suite for resource-constrained LLM agents."
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="http://127.0.0.1:8080/v1",
        help="OpenAI-compatible server endpoint (default: http://127.0.0.1:8080/v1)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default="none",
        help="Optional API key (default: none)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="default",
        help="Model ID string in payload (default: default)",
    )
    parser.add_argument(
        "--suite",
        type=str,
        choices=["all", "diff", "tools", "context", "adversarial"],
        default="all",
        help="Benchmark suite to execute (default: all)",
    )
    parser.add_argument(
        "--max-reflection",
        type=int,
        default=2,
        help="Max error-reflection iterations for failed diff tests (default: 2)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-request timeout in seconds (default: 120.0)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="File path to save Markdown scorecard report",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        run_all(
            endpoint=args.endpoint,
            api_key=args.api_key,
            model=args.model,
            suite=args.suite,
            max_reflection=args.max_reflection,
            timeout=args.timeout,
            export_path=args.export,
        )
    except KeyboardInterrupt:
        print("\n[!] Benchmark aborted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[-] Fatal error during benchmark run: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
