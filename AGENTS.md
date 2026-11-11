# Agent Operating Guidelines: lowend-agent-bench

Welcome, Agent. This repository is specifically designed to be **autonomous-agent friendly**.
You can run benchmarks, add new edge-case tests, validate schemas, and submit scorecards via Pull Requests without human intervention.

---

## 1. Ground Rules & Directives

1. **Focus on Resource-Constrained Edge Cases**: This benchmark is not for 70B+ datacenter clusters. Every test case should probe how well small models (0.5B to 8B dense, or MoE with $\le$4B active parameters) handle real agent workloads on tight VRAM (8GB - 32GB).
2. **Zero Heavy Dependencies**: Keep the core lightweight. All test cases must rely on standard Python libraries (`urllib`, `json`, `re`, `subprocess`, `hashlib`, `time`, `typing`).
3. **Reproducibility**: Assertions must be deterministic. Avoid nondeterministic timing checks or open-ended fuzzy criteria.
4. **Self-Validation**: Always run `python -m lowend_bench validate` before submitting a PR.

---

## 2. How to Add a New Test Case

You have two simple ways to add a test:

### Option A: Declarative JSON (Recommended for simple prompts & tool calls)
Drop a `.json` file inside `cases/<test_name>.json`:

```json
{
  "name": "Extract Port from URL",
  "category": "networking",
  "description": "Tests if model parses custom network ports.",
  "system_prompt": "You are a network parser.",
  "user_prompt": "Parse the port from https://internal.dev:8443/status.",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "set_port",
        "parameters": {
          "type": "object",
          "properties": { "port": { "type": "integer" } },
          "required": ["port"]
        }
      }
    }
  ],
  "expected_tool_name": "set_port",
  "expected_arguments": { "port": 8443 }
}
```

### Option B: Custom Python Test (For complex logic, multi-turn, or code execution)
Add a `.py` file inside `custom_cases/<test_name>.py`:

```python
from lowend_bench.base import BaseTestCase, TestResult
from lowend_bench.registry import register_test
from lowend_bench.client import LLMClient

@register_test
class MyAgentEdgeCase(BaseTestCase):
    name = "My Agent Edge Case"
    category = "resilience"
    description = "Tests recovery from corrupted headers."

    def run(self, client: LLMClient) -> TestResult:
        res = client.chat_completion([{"role": "user", "content": "Ping"}])
        passed = "pong" in res.content.lower()
        return TestResult(
            name=self.name,
            category=self.category,
            passed=passed,
            tokens_per_sec=res.tokens_per_sec,
            details="Handled ping correctly" if passed else "Failed ping"
        )
```

---

## 3. Validating Your Test Locally

Run the validation suite to ensure your test implements the required interface and schema:

```bash
python -m lowend_bench validate
```

If the output shows `[VALID]`, your test case is ready for a PR.

---

## 4. Submitting a Benchmark Scorecard (PR Flow)

To benchmark a model and produce a PR-ready scorecard:

```bash
# 1. Start your local server at http://127.0.0.1:8080/v1
# 2. Run the automated submission command:
python -m lowend_bench submit \
  --model "qwen2.5-coder-7b-q4_k_m" \
  --contributor "agent-alpha-01" \
  --hardware "Apple M2 16GB / AMD 8060S 32GB"

# 3. Output file will be saved in reports/
# 4. Stage and commit the report:
git checkout -b results/qwen2.5-coder-7b
git add reports/
git commit -m "benchmark: add qwen2.5-coder-7b scorecard on 16GB unified memory"
```

---

## 5. Available Suites Reference

| Flag | Suite Name | Description |
| :--- | :--- | :--- |
| `--suite diff` | Aider Diff Editing | SEARCH/REPLACE diff compliance, unit test pass rate, multi-turn reflection |
| `--suite tools` | Function Calling | Single tool, multi-tool, parallel 3-way, enum, anti-hallucination refusal |
| `--suite frontier` | Frontier Challenge V4 | 8 adversarial cases (Turnstile, obfuscated JS, range chunking, process kills) |
| `--suite trace` | Trace Replay | Real LibGen 22k raw JSON viewport failure recovery |
| `--suite vault` | Frontier Vault | Multi-stage honeypot avoidance, pagination, 429 backoff, cyclic XOR decryption |
| `--suite context` | Context Stress | 2k -> 32k scaling and needle retrieval under memory pressure |
| `--suite custom` | Custom Cases | All tests in `cases/` and `custom_cases/` |
| `--suite all` | Complete Sweep | Runs all suites end-to-end |
