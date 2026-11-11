# Low-End Agent Benchmark (`lowend-agent-bench`)

A standardized, empirical benchmark suite designed specifically for **low-end and resource-constrained LLMs** (0.5B–8B dense, or MoE models with $\le$4B active parameters) running on **8 GB, 16 GB, or 32 GB unified/VRAM edge machines**.

---

## 1. Why Another Benchmark?

Standard LLM benchmarks (MMLU, GSM8K, HumanEval) fail to evaluate whether a small model can survive in an **autonomous agent loop**:

1. **Diff Syntax Compliance vs. Pure Code Generation**: Generating a Python function in isolation is trivial. Generating an exact `<<<<<<< SEARCH` / `=======` / `>>>>>>> REPLACE` diff block that cleanly patches an existing 500-line file without corrupting whitespace or hallucinating line numbers is where 90% of small models fail.
2. **Anti-Hallucination Refusal in Tool Calling**: Small models frequently hallucinate missing mandatory parameters (e.g. inventing fake bank account IDs or file paths) rather than asking for clarification.
3. **Multi-Turn Reflection**: When a unit test or compiler fails, can the small model ingest the traceback and self-correct on turn 2 without looping into degenerative token output?
4. **Context Degradation & Memory Pressure**: How rapidly does the model's instruction adherence deteriorate as context scales from 2k to 32k tokens on tight VRAM?

`lowend-agent-bench` tests these practical agentic capabilities with zero external heavy dependencies.

---

## 2. Benchmark Suites

| Suite | Name | What It Evaluates | Key Metric |
| :--- | :--- | :--- | :--- |
| **`diff`** | **Diff Editing & Patching** | SEARCH/REPLACE diff formatting, indentation preservation, test execution pass rate, multi-turn error reflection | % Tests Passed (Zero-Shot vs Reflection) |
| **`tools`** | **Constrained Function Calling** | Single tool dispatch, multi-tool disambiguation, parallel calls, enum enforcement, **anti-hallucination refusal** | % Schema & Execution Accuracy |
| **`context`** | **Context Scaling & Needle Retrieval** | Instruction adherence and reasoning decay as context grows (2k $\to$ 8k $\to$ 16k $\to$ 32k) | Accuracy @ Context Depth & t/s prefill |
| **`adversarial`** | **Adversarial Agent Resilience** | Obfuscated code parsing, truncated output recovery, safe process subtree termination | % Adversarial Tasks Solved |

---

## 3. Quick Start

### Installation
`lowend-agent-bench` requires Python 3.9+ and has **zero required third-party dependencies** (uses standard library `urllib`, `json`, `subprocess`):

```bash
git clone https://github.com/<your-username>/lowend-agent-bench.git
cd lowend-agent-bench
pip install -e .
```

### Running Against Any OpenAI-Compatible Server
Start your local model server (e.g. `llama-server`, `vLLM`, `Ollama`, or `Aphrodite`) at `http://127.0.0.1:8080/v1`:

```bash
# Run all benchmark suites:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite all

# Run only the Diff Editing suite with up to 2 reflection attempts:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite diff --max-reflection 2

# Run only the Tool Calling & Anti-Hallucination suite:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite tools

# Export Markdown scorecard for GitHub PRs / reports:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite all --export reports/my_model_scorecard.md
```

---

## 4. CLI Arguments Reference

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--endpoint` | `http://127.0.0.1:8080/v1` | OpenAI-compatible API base URL |
| `--api-key` | `none` | Optional API key |
| `--model` | `default` | Model identifier string sent in request payload |
| `--suite` | `all` | Benchmark suite to run (`diff`, `tools`, `context`, `adversarial`, `all`) |
| `--max-reflection` | `2` | Maximum retry attempts with error traceback feedback |
| `--timeout` | `120` | Request timeout per turn in seconds |
| `--export` | `None` | Path to export generated Markdown scorecard |

---

## 5. Sample Output & Scorecard

```
================================================================================
LOW-END AGENT BENCHMARK REPORT
Target Model: gpt-oss-20b-heretic-v2
Endpoint:     http://127.0.0.1:8080/v1
================================================================================

SUITE 1: DIFF EDITING (AIDER SEARCH/REPLACE)
--------------------------------------------------------------------------------
1. Two Sum (Duplicates & Multi-Index)   [PASSED - Turn 1]  (101.6 t/s)
2. Expiring LRU Cache (TTL Eviction)     [PASSED - Turn 1]  (114.8 t/s)
3. SemVer 2.0 Parser & Comparator       [PASSED - Turn 2 (Reflection)] (95.4 t/s)
Suite Pass Rate: 3 / 3 (100.0%)

SUITE 2: FUNCTION CALLING & ANTI-HALLUCINATION
--------------------------------------------------------------------------------
1. Simple Typed Function Call           [PASSED]  (57.7 t/s)
2. Multi-Tool Disambiguation            [PASSED]  (58.2 t/s)
3. Parallel Tool Dispatch (3 tools)     [PASSED]  (43.5 t/s)
4. Enum & Constraint Validation         [PASSED]  (62.0 t/s)
5. Missing Param Anti-Hallucination     [PASSED]  (Refrained from hallucinating)
6. Nested JSON Schema Parsing           [PASSED]  (71.1 t/s)
Suite Accuracy: 6 / 6 (100.0%)

OVERALL BENCHMARK SCORE: 100.0%
Scorecard exported to: reports/sample_scorecard.md
```

---

## 6. Repository Layout

```
lowend-agent-bench/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── lowend_bench/
│   ├── __init__.py
│   ├── cli.py                     # Main command line parser
│   ├── client.py                  # Zero-dependency OpenAI HTTP client
│   ├── runner.py                  # Suite orchestrator & test executor
│   ├── reporter.py                # ANSI table formatter & Markdown exporter
│   └── suites/
│       ├── __init__.py
│       ├── diff_editing.py        # SEARCH/REPLACE diff and unit test runner
│       ├── tool_calling.py        # BFCL function calling & anti-hallucination
│       ├── context_stress.py      # Context scaling & needle-in-haystack test
│       └── adversarial_agent.py   # Adversarial agent edge cases
├── examples/
│   ├── run_quick_eval.sh
│   └── run_full_sweep.sh
└── reports/
    └── sample_scorecard.md
```

---

## License
MIT License. See [LICENSE](LICENSE) for details.
