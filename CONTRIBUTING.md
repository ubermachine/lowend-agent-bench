# Contributing to lowend-agent-bench

We welcome contributions from both **human developers** and **autonomous AI agents**!

---

## What We Look For

1. **New Realistic Edge Cases**: If you found a scenario where a small model (e.g. 1B–8B) failed in an agent loop (broken diff formatting, hallucinated arguments, parsing issues, stream disconnects), add it!
2. **Benchmark Scorecards**: Run the benchmark on your local setup (e.g. Apple Silicon M-series, AMD Ryzen/Strix APUs, Intel Core Ultra, Nvidia RTX 3060/4060 8GB/12GB/16GB) and submit your markdown report to `reports/`.
3. **Optimizations**: Improvements to test isolation, execution speed, or reporter formatting.

---

## Quick Contribution Rules

- **Zero Heavy Dependencies**: Rely only on standard Python 3.9+ libraries.
- **Deterministic Evaluation**: Tests must have objective, verifiable assertions (e.g. unit tests, checksums, regex matches, tool call parameters).
- **Validate Before Opening PR**:
  ```bash
  python -m lowend_bench validate
  ```
- **PR Scope**: Keep each PR focused on either (1) a single new test case or (2) a new model benchmark run.

---

## Pull Request Process

1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b test/my-new-edge-case
   ```
2. Add your test to `cases/<name>.json` or `custom_cases/<name>.py`.
3. Validate:
   ```bash
   python -m lowend_bench validate
   ```
4. Commit your changes and open a Pull Request using the provided PR template.
