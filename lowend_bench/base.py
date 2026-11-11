"""
Base classes and interfaces for pluggable benchmark test cases.
Designed so human contributors and autonomous agents can add new tests with minimal boilerplate.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from lowend_bench.client import LLMClient


@dataclass
class TestResult:
    name: str
    category: str
    passed: bool
    tokens_per_sec: float = 0.0
    latency_sec: float = 0.0
    turn_solved: int = 1
    details: str = ""
    error_message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


class BaseTestCase(ABC):
    """
    Abstract base class for all benchmark test cases.
    To add a new benchmark test, subclass BaseTestCase and implement `run()`.
    """
    name: str = "Unnamed Test"
    category: str = "general"
    description: str = ""
    timeout_sec: float = 120.0

    @abstractmethod
    def run(self, client: LLMClient) -> TestResult:
        """
        Execute the test against the target LLM client and return a TestResult.
        """
        pass
