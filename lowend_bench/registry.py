"""
Extensible Test Registry and Dynamic Case Loader.
Allows both humans and AI agents to register or drop in new test cases seamlessly.
"""

import os
import sys
import json
import glob
import importlib.util
from typing import Dict, List, Type, Optional, Callable
from lowend_bench.base import BaseTestCase, TestResult
from lowend_bench.client import LLMClient


_REGISTRY: Dict[str, BaseTestCase] = {}


def register_test(cls: Type[BaseTestCase]) -> Type[BaseTestCase]:
    """Decorator to register a BaseTestCase subclass in the global registry."""
    instance = cls()
    _REGISTRY[instance.name] = instance
    return cls


class DeclarativeJSONTestCase(BaseTestCase):
    """
    Test case loaded from a declarative JSON definition file in cases/.
    Enables zero-code additions of new prompts, tools, and assertions.
    """
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "Unnamed Declarative Test")
        self.category = data.get("category", "custom")
        self.description = data.get("description", "")
        self.system_prompt = data.get("system_prompt", "You are a helpful assistant.")
        self.user_prompt = data.get("user_prompt", "")
        self.tools = data.get("tools", None)
        self.expected_tool_name = data.get("expected_tool_name", None)
        self.expected_arguments = data.get("expected_arguments", {})
        self.expected_content_contains = data.get("expected_content_contains", [])
        self.refuse_tool_calls = data.get("refuse_tool_calls", False)
        self.temperature = data.get("temperature", 0.1)
        self.max_tokens = data.get("max_tokens", 2048)

    def run(self, client: LLMClient) -> TestResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]
        try:
            res = client.chat_completion(
                messages,
                tools=self.tools,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            passed = True
            details_list = []

            # 1. Check tool refusal
            if self.refuse_tool_calls and res.tool_calls:
                passed = False
                details_list.append("Emitted tool call when refusal was expected")

            # 2. Check expected tool call
            if self.expected_tool_name:
                emitted_names = [tc.name for tc in res.tool_calls]
                if self.expected_tool_name not in emitted_names:
                    passed = False
                    details_list.append(f"Expected tool '{self.expected_tool_name}', got {emitted_names}")
                else:
                    # Validate arguments
                    for tc in res.tool_calls:
                        if tc.name == self.expected_tool_name:
                            for k, v in self.expected_arguments.items():
                                if tc.arguments.get(k) != v:
                                    passed = False
                                    details_list.append(f"Arg mismatch for '{k}': expected '{v}', got '{tc.arguments.get(k)}'")

            # 3. Check expected content substrings
            for substring in self.expected_content_contains:
                if substring.lower() not in res.content.lower():
                    passed = False
                    details_list.append(f"Missing required substring: '{substring}'")

            details = "; ".join(details_list) if details_list else "All assertions passed"
            return TestResult(
                name=self.name,
                category=self.category,
                passed=passed,
                tokens_per_sec=res.tokens_per_sec,
                latency_sec=res.latency_sec,
                details=details,
            )
        except Exception as e:
            return TestResult(
                name=self.name,
                category=self.category,
                passed=False,
                error_message=str(e),
            )


def load_declarative_cases(cases_dir: str) -> List[BaseTestCase]:
    """Scan directory for *.json declarative test cases."""
    loaded = []
    if not os.path.isdir(cases_dir):
        return loaded

    for json_file in glob.glob(os.path.join(cases_dir, "*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                case = DeclarativeJSONTestCase(data)
                _REGISTRY[case.name] = case
                loaded.append(case)
        except Exception as e:
            print(f"[!] Warning: Failed loading declarative test from {json_file}: {e}")
    return loaded


def load_custom_python_cases(custom_dir: str) -> List[BaseTestCase]:
    """Dynamically import *.py files from custom_cases/ that register BaseTestCase."""
    loaded = []
    if not os.path.isdir(custom_dir):
        return loaded

    for py_file in glob.glob(os.path.join(custom_dir, "*.py")):
        if os.path.basename(py_file).startswith("__"):
            continue
        mod_name = f"custom_case_{os.path.splitext(os.path.basename(py_file))[0]}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, py_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
        except Exception as e:
            print(f"[!] Warning: Failed importing custom test module {py_file}: {e}")

    return list(_REGISTRY.values())


def get_all_registered_tests() -> List[BaseTestCase]:
    """Return all currently registered test cases."""
    return list(_REGISTRY.values())


def validate_test_case(case: BaseTestCase) -> bool:
    """Validate that a test case properly implements the interface."""
    if not case.name or not isinstance(case.name, str):
        return False
    if not case.category or not isinstance(case.category, str):
        return False
    if not hasattr(case, "run") or not callable(case.run):
        return False
    return True
