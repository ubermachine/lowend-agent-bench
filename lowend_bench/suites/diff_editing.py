"""
Diff Editing & Code Repair Benchmark Suite (Aider-Style SEARCH/REPLACE).
Evaluates exact diff formatting, hunk application, unit test execution, and multi-turn error reflection.
"""

import re
import sys
import tempfile
import subprocess
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from lowend_bench.client import LLMClient


@dataclass
class DiffTestResult:
    name: str
    passed: bool
    turn_solved: int  # 1 = zero-shot, 2+ = reflection, 0 = failed
    tokens_per_sec: float
    error_message: str = ""
    diff_text: str = ""


DIFF_SYSTEM_PROMPT = """You are an expert software engineer.
You are given a file and a task to fix or implement code in it.
You MUST output your edits using exact SEARCH/REPLACE blocks formatted like this:

<<<<<<< SEARCH
... exact lines to replace from original file ...
=======
... replacement lines ...
>>>>>>> REPLACE

Rules:
1. Every SEARCH block must EXACTLY match the lines in the original file, including exact spaces and indentation.
2. Only replace what is necessary.
3. Do NOT output the entire file.
4. Output only SEARCH/REPLACE blocks.
"""


def apply_search_replace(original_text: str, diff_text: str) -> Tuple[bool, str, str]:
    """
    Parse and apply SEARCH/REPLACE blocks to original_text.
    Returns (success, new_text, error_msg).
    """
    pattern = re.compile(
        r"<<<<<<<\s*SEARCH\r?\n(.*?)\r?\n=======\r?\n(.*?)\r?\n>>>>>>>\s*REPLACE",
        re.DOTALL,
    )
    matches = list(pattern.finditer(diff_text))
    if not matches:
        return False, original_text, "No valid <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE blocks found in output."

    current_text = original_text
    for i, match in enumerate(matches, 1):
        search_block = match.group(1)
        replace_block = match.group(2)

        if search_block not in current_text:
            # Try stripped line comparison for fuzzy tolerance
            norm_search = "\n".join(line.rstrip() for line in search_block.splitlines())
            norm_curr = "\n".join(line.rstrip() for line in current_text.splitlines())
            if norm_search in norm_curr:
                # Approximate match succeeded, but strict indentation failed
                idx = norm_curr.find(norm_search)
                # Compute replacement
                return False, current_text, f"Block {i}: SEARCH block whitespace/indentation mismatch."
            return False, current_text, f"Block {i}: SEARCH block not found in file."

        current_text = current_text.replace(search_block, replace_block, 1)

    return True, current_text, ""


def execute_test(code_text: str, test_code: str) -> Tuple[bool, str]:
    """Execute code + test in an isolated Python process."""
    full_script = f"{code_text}\n\n{test_code}"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as tmp:
        tmp.write(full_script)
        tmp.flush()
        try:
            res = subprocess.run(
                [sys.executable, tmp.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            )
            if res.returncode == 0:
                return True, res.stdout
            else:
                return False, f"Process exited with code {res.returncode}:\n{res.stderr}\n{res.stdout}"
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (infinite loop or hang)."
        except Exception as e:
            return False, f"Execution exception: {e}"


# --- Problem Definitions ---

PROBLEMS = [
    {
        "name": "Two Sum (Duplicates & Multi-Index)",
        "file_name": "two_sum.py",
        "initial_code": '''def two_sum(nums, target):
    """
    Given an array of integers nums and an integer target,
    return indices of the two numbers such that they add up to target.
    Must return 0-indexed list [index1, index2] where index1 < index2.
    Must handle duplicate values properly and achieve O(n) runtime.
    """
    # BUGGY INITIAL IMPLEMENTATION
    for i in range(len(nums)):
        for j in range(len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
''',
        "prompt": "Fix `two_sum` in `two_sum.py` so that it returns two distinct indices `[index1, index2]` with `index1 < index2`, handles duplicates correctly (e.g. `[3, 3] target 6 -> [0, 1]`), and executes in O(n) average time using a hash map.",
        "test_code": '''import unittest

class TestTwoSum(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(two_sum([2, 7, 11, 15], 9), [0, 1])

    def test_duplicates(self):
        self.assertEqual(two_sum([3, 3], 6), [0, 1])

    def test_non_adjacent(self):
        self.assertEqual(two_sum([3, 2, 4], 6), [1, 2])

    def test_negative(self):
        self.assertEqual(two_sum([-1, -2, -3, -4, -5], -8), [2, 4])

if __name__ == '__main__':
    unittest.main()
''',
    },
    {
        "name": "Expiring LRU Cache (TTL Eviction)",
        "file_name": "cache.py",
        "initial_code": '''import time
from collections import OrderedDict

class ExpiringLRUCache:
    def __init__(self, capacity: int, default_ttl: float = 60.0):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.cache = OrderedDict()

    def get(self, key):
        # BUG: Missing expiry check and LRU refresh
        if key in self.cache:
            return self.cache[key]
        return None

    def put(self, key, value, ttl: float = None):
        # BUG: Does not store timestamp, does not evict on capacity
        self.cache[key] = value
''',
        "prompt": "Complete `ExpiringLRUCache` in `cache.py`. It must support `get(key)` returning value or `None` if absent or expired (evicting on access if expired). `put(key, value, ttl=None)` must update value and expiry time (using `default_ttl` if `ttl` is None), refresh LRU order, and if capacity is exceeded, evict the least recently used non-expired entry.",
        "test_code": '''import unittest
import time

class TestExpiringLRUCache(unittest.TestCase):
    def test_lru_and_expiry(self):
        c = ExpiringLRUCache(capacity=2, default_ttl=0.1)
        c.put("a", 1)
        c.put("b", 2)
        self.assertEqual(c.get("a"), 1)
        # Adding c evicts b (since a was accessed and is more recent)
        c.put("c", 3)
        self.assertEqual(c.get("a"), 1)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("c"), 3)

        # Test expiration
        time.sleep(0.15)
        self.assertIsNone(c.get("a"))
        self.assertIsNone(c.get("c"))

if __name__ == '__main__':
    unittest.main()
''',
    },
    {
        "name": "SemVer 2.0 Parser & Comparator",
        "file_name": "semver.py",
        "initial_code": '''class SemVer:
    def __init__(self, version_str: str):
        self.raw = version_str
        # TODO: Parse major, minor, patch, prerelease, and build metadata
        self.major = 0
        self.minor = 0
        self.patch = 0
        self.prerelease = []
        self.build = None

    def __lt__(self, other):
        return self.raw < other.raw

    def __eq__(self, other):
        return self.raw == other.raw
''',
        "prompt": "Implement a full SemVer 2.0 parser and comparator in `semver.py`. Parse `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`. `__lt__` and `__eq__` must compare major, minor, patch numerically, then compare prerelease identifiers (numeric identifiers compare numerically, strings lexically; a version with a prerelease is lower precedence than without: `1.0.0-alpha < 1.0.0`). Build metadata MUST be ignored in comparisons.",
        "test_code": '''import unittest

class TestSemVer(unittest.TestCase):
    def test_precedence(self):
        v1 = SemVer("1.0.0-alpha")
        v2 = SemVer("1.0.0-alpha.1")
        v3 = SemVer("1.0.0-beta")
        v4 = SemVer("1.0.0")
        v5 = SemVer("1.0.0+20130313144700")

        self.assertTrue(v1 < v2)
        self.assertTrue(v2 < v3)
        self.assertTrue(v3 < v4)
        self.assertEqual(v4, v5)  # Build metadata ignored
        self.assertTrue(SemVer("1.0.0") < SemVer("2.0.0"))
        self.assertTrue(SemVer("1.1.0") > SemVer("1.0.9"))

if __name__ == '__main__':
    unittest.main()
''',
    },
]


def run_diff_suite(
    client: LLMClient, max_reflection: int = 2
) -> List[DiffTestResult]:
    """Run the diff editing and code repair suite."""
    results = []

    for prob in PROBLEMS:
        name = prob["name"]
        file_name = prob["file_name"]
        curr_code = prob["initial_code"]
        test_code = prob["test_code"]
        prompt = prob["prompt"]

        messages = [
            {"role": "system", "content": DIFF_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Here is `{file_name}`:\n```python\n{curr_code}\n```\nTask: {prompt}",
            },
        ]

        passed = False
        turn_solved = 0
        last_error = ""
        last_tps = 0.0

        for turn in range(1, max_reflection + 2):
            try:
                res = client.chat_completion(messages, temperature=0.1)
                last_tps = res.tokens_per_sec
                diff_output = res.content

                success, patched_code, patch_err = apply_search_replace(
                    curr_code, diff_output
                )
                if not success:
                    last_error = f"Patch failed: {patch_err}"
                else:
                    test_ok, test_output = execute_test(patched_code, test_code)
                    if test_ok:
                        passed = True
                        turn_solved = turn
                        break
                    else:
                        last_error = f"Test failure:\n{test_output}"

                # Reflection step
                if turn <= max_reflection:
                    messages.append({"role": "assistant", "content": diff_output})
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Your previous edit failed with error:\n{last_error}\nPlease re-examine the original file and output a corrected <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE block.",
                        }
                    )
            except Exception as e:
                last_error = f"API Error: {e}"
                break

        results.append(
            DiffTestResult(
                name=name,
                passed=passed,
                turn_solved=turn_solved,
                tokens_per_sec=last_tps,
                error_message=last_error if not passed else "",
            )
        )

    return results
