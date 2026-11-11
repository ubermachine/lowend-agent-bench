"""
Adversarial Agent Resilience Suite.
Tests edge-case survival: obfuscated payloads, anti-bot block handling,
resumable range chunking, and zombie process subtree termination.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from lowend_bench.client import LLMClient


@dataclass
class AdversarialTestResult:
    name: str
    passed: bool
    tokens_per_sec: float
    details: str = ""


ADVERSARIAL_TASKS = [
    {
        "name": "Obfuscated JS String Unpacking",
        "prompt": """Analyze this obfuscated JavaScript snippet from a target site and extract the hidden authorization endpoint URL:
```javascript
const _0x1a = ["\\x68\\x74\\x74\\x70\\x73\\x3a\\x2f\\x2f", "\\x61\\x70\\x69\\x2e\\x73\\x65\\x63\\x75\\x72\\x65\\x2d\\x64\\x6f\\x6d\\x61\\x69\\x6e\\x2e\\x69\\x6f", "\\x2f\\x76\\x31\\x2f\\x61\\x75\\x74\\x68\\x2f\\x74\\x6f\\x6b\\x65\\x6e"];
const endpoint = _0x1a[0] + _0x1a[1] + _0x1a[2];
```
Return ONLY the clean decoded URL string.""",
        "expected_substrings": ["https://api.secure-domain.io/v1/auth/token"],
    },
    {
        "name": "Cloudflare Turnstile Iframe Detection",
        "prompt": """Your automated scraper requested an API endpoint `https://example.com/data.json` expecting JSON, but received this HTTP 403 HTML body:
```html
<!DOCTYPE html>
<html>
<head><title>Just a moment...</title></head>
<body>
  <div id="cf-turnstile" data-sitekey="0x4AAAAAAABcd"></div>
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
</body>
</html>
```
Identify the blocking mechanism and recommend the exact technical tool/approach needed (do not hallucinate JSON parsing).""",
        "expected_substrings": ["cloudflare", "turnstile"],
    },
    {
        "name": "Resumable Range Chunking Header",
        "prompt": """Write a single bash `curl` command to resume downloading a 500MB file `https://cdn.example.com/large.tar.gz` starting from byte offset 10485760 (10MB) to 20971519 (20MB), saving output to `part2.bin` without downloading earlier bytes.""",
        "expected_substrings": ["-H", "Range: bytes=10485760-20971519", "part2.bin"],
    },
    {
        "name": "Zombie Process Subtree Termination",
        "prompt": """A worker daemon process with PID 4102 spawned several detached child processes (Chromium and Node.js workers) in its process group.
Give the exact Linux shell command to terminate the entire process group cleanly with SIGTERM first, without leaving orphaned zombie worker processes.""",
        "expected_substrings": ["kill -TERM -4102", "kill -15 -4102", "pkill -P 4102", "kill -- -4102"],
    },
]


def run_adversarial_suite(client: LLMClient) -> List[AdversarialTestResult]:
    results = []

    for task in ADVERSARIAL_TASKS:
        name = task["name"]
        prompt = task["prompt"]
        expected = task["expected_substrings"]

        messages = [
            {"role": "system", "content": "You are a senior systems engineer and penetration tester."},
            {"role": "user", "content": prompt},
        ]

        try:
            res = client.chat_completion(messages, temperature=0.1)
            content = res.content.lower()

            # Check if expected patterns match
            if name == "Zombie Process Subtree Termination":
                # Any valid process group kill syntax
                passed = any(exp.lower() in content for exp in expected)
            else:
                passed = all(exp.lower() in content for exp in expected)

            results.append(
                AdversarialTestResult(
                    name=name,
                    passed=passed,
                    tokens_per_sec=res.tokens_per_sec,
                    details="PASSED" if passed else f"Missing required patterns from output: {res.content[:100]}...",
                )
            )
        except Exception as e:
            results.append(
                AdversarialTestResult(
                    name=name,
                    passed=False,
                    tokens_per_sec=0.0,
                    details=f"Error: {e}",
                )
            )

    return results
