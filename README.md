# Low-End Agent Benchmark (`lowend-agent-bench`)

A standardized, empirical benchmark suite designed specifically for **low-end and resource-constrained LLMs** (0.5B–8B dense, or MoE models with $\le$4B active parameters) running on **8 GB, 16 GB, or 32 GB unified/VRAM edge machines**.

---

## 1. Why Another Benchmark?

Standard LLM benchmarks (MMLU, GSM8K, HumanEval) fail to evaluate whether a small model can survive in an **autonomous agent loop**:

1. **Diff Syntax Compliance vs. Pure Code Generation**: Generating a Python function in isolation is trivial. Generating an exact `<<<<<<< SEARCH` / `=======` / `>>>>>>> REPLACE` diff block that cleanly patches an existing 500-line file without corrupting whitespace or hallucinating line numbers is where 90% of small models fail.
2. **Anti-Hallucination Refusal in Tool Calling**: Small models frequently hallucinate missing mandatory parameters (e.g. inventing fake bank account IDs or file paths) rather than asking for clarification.
3. **Multi-Turn Error Reflection**: When a unit test or compiler fails, can the small model ingest the traceback and self-correct on turn 2 without looping into degenerative token output?
4. **Context Degradation & Memory Pressure**: How rapidly does the model's instruction adherence deteriorate as context scales from 2k to 32k tokens on tight VRAM?
5. **Adversarial Resilience**: Can the model handle obfuscated script blocks, navigate dynamic iframes, perform multi-chunk reassembly, and safely kill detached process subtrees without leaving zombie processes?

`lowend-agent-bench` tests these practical agentic capabilities with zero external heavy dependencies.

---

## 2. Benchmark Suites

| Suite Flag | Name | What It Evaluates | Key Metric |
| :--- | :--- | :--- | :--- |
| `--suite diff` | **Diff Editing & Code Repair** | SEARCH/REPLACE diff formatting, indentation preservation, test execution pass rate, multi-turn error reflection | % Tests Passed (Zero-Shot vs Reflection) |
| `--suite tools` | **Constrained Function Calling** | Single tool dispatch, multi-tool disambiguation, parallel 3-way calls, enum enforcement, **anti-hallucination refusal** | % Schema & Execution Accuracy |
| `--suite frontier` | **Frontier Challenge V4** | 8 adversarial scenarios: Obfuscated JS unpacking, Turnstile iframe frameLocator, multi-chunk range cURL & SHA256, WebSocket/SSE sniffing, fuzzy diff drift, parameterized SQL security, multipart cURL upload, and zombie process group kills | % Adversarial Tasks Solved |
| `--suite trace` | **Real-World Trace Replay** | Replays stranded agent state on LibGen's 22,000-token raw JSON API dump; evaluates zero-shot MD5/link navigation vs Turn 2 self-healing reflection | % Recovery Rate & Latency |
| `--suite vault` | **Frontier Vault Challenge** | Multi-stage extraction: portal scraping, honeypot trap avoidance, cursor-based pagination, HTTP 429 Retry-After backoff, cyclic XOR stream decryption, and composite SHA256 integrity | % Stages Passed (out of 5) |
| `--suite context` | **Context Scaling & Needle Retrieval** | Instruction adherence and reasoning decay as context grows (2k $\to$ 8k $\to$ 16k $\to$ 32k) | Accuracy @ Context Depth & t/s prefill |
| `--suite custom` | **Community & Custom Tests** | Pluggable declarative JSON tests (`cases/`) and custom Python tests (`custom_cases/`) | Custom pass rate |
| `--suite all` | **Complete Sweep** | Executes all 7 benchmark suites end-to-end | Overall Scorecard Total |

---

## 3. Quick Start

### Installation
`lowend-agent-bench` requires Python 3.9+ and has **zero required third-party dependencies** (uses standard library `urllib`, `json`, `subprocess`, `hashlib`, `re`):

```bash
git clone https://github.com/ubermachine/lowend-agent-bench.git
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

# Run the 8 Frontier Challenge V4 adversarial tests:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite frontier

# Run Real-World Trace Replay:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite trace

# Run Frontier Vault Multi-Stage Harvest:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite vault

# Export Markdown scorecard for GitHub PRs / reports:
python3 -m lowend_bench --endpoint http://127.0.0.1:8080/v1 --suite all --export reports/my_model_scorecard.md
```

---

## 4. Contributing Tests & Submitting PRs (Human & Agent Friendly)

`lowend-agent-bench` is built from the ground up to allow **autonomous AI agents and developers** to easily add new test cases and submit benchmark results via Pull Requests.

See **[AGENTS.md](AGENTS.md)** and **[CONTRIBUTING.md](CONTRIBUTING.md)** for full details.

### Adding a Declarative Test Case (Zero Code)
Drop a JSON file in `cases/<your_test>.json`:
```json
{
  "name": "Parse Custom Config Port",
  "category": "networking",
  "description": "Tests if model parses custom network ports.",
  "system_prompt": "You are a network parser.",
  "user_prompt": "Extract the port from https://internal.dev:8443/status.",
  "tools": [{
    "type": "function",
    "function": {
      "name": "set_port",
      "parameters": {
        "type": "object",
        "properties": { "port": { "type": "integer" } },
        "required": ["port"]
      }
    }
  }],
  "expected_tool_name": "set_port",
  "expected_arguments": { "port": 8443 }
}
```

### Adding a Custom Python Test Case
Add a Python file in `custom_cases/<your_test>.py`:
```python
from lowend_bench.base import BaseTestCase, TestResult
from lowend_bench.registry import register_test
from lowend_bench.client import LLMClient

@register_test
class MyEdgeCase(BaseTestCase):
    name = "My Custom Edge Case"
    category = "community"

    def run(self, client: LLMClient) -> TestResult:
        res = client.chat_completion([{"role": "user", "content": "Ping"}])
        passed = "pong" in res.content.lower()
        return TestResult(name=self.name, category=self.category, passed=passed)
```

### Validating Your Test Locally
```bash
python3 -m lowend_bench validate
```

### One-Command PR Scorecard Submission
```bash
python3 -m lowend_bench submit \
  --model "qwen2.5-coder-7b" \
  --contributor "my-username" \
  --hardware "16GB Unified Memory"
```

---

## 5. Repository Layout

```
lowend-agent-bench/
├── README.md                      # Overview & usage guide
├── AGENTS.md                      # Operating manual for AI agent contributors
├── CONTRIBUTING.md                # Contribution workflow
├── LICENSE                        # MIT License
├── pyproject.toml
├── requirements.txt
├── .github/
│   ├── pull_request_template.md   # Standardized PR template
│   └── workflows/ci.yml           # Multi-Python CI pipeline (3.9 - 3.12)
├── cases/                         # Community declarative JSON test cases
│   └── example_declarative_test.json
├── custom_cases/                  # Community Python test cases
│   └── example_python_test.py
├── lowend_bench/
│   ├── base.py                    # BaseTestCase & TestResult interfaces
│   ├── registry.py                # Dynamic test loader & validator
│   ├── client.py                  # Zero-dependency OpenAI HTTP client
│   ├── cli.py                     # CLI entrypoint (run, validate, submit)
│   ├── runner.py                  # Suite orchestrator
│   ├── reporter.py                # ANSI table & Markdown scorecard exporter
│   └── suites/
│       ├── diff_editing.py        # Aider SEARCH/REPLACE diff and reflection
│       ├── tool_calling.py        # BFCL function calling & anti-hallucination
│       ├── frontier_v4.py         # 8 adversarial agent edge cases
│       ├── trace_replay.py        # LibGen 22k token viewport navigation
│       ├── vault_challenge.py     # Multi-stage autonomous harvest
│       └── context_stress.py      # Context window scaling (2k -> 32k)
├── examples/
│   ├── run_quick_eval.sh
│   └── run_full_sweep.sh
└── reports/
    └── sample_scorecard.md
```

---

## License
MIT License. See [LICENSE](LICENSE) for details.
