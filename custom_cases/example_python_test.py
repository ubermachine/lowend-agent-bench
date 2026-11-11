"""
Example custom Python test case.
Demonstrates subclassing BaseTestCase and using @register_test.
"""

from lowend_bench.base import BaseTestCase, TestResult
from lowend_bench.registry import register_test
from lowend_bench.client import LLMClient


@register_test
class CustomEnvValidationTest(BaseTestCase):
    name = "Custom Environment Config Validation"
    category = "community"
    description = "Tests if model detects insecure default environment variables."

    def run(self, client: LLMClient) -> TestResult:
        messages = [
            {"role": "system", "content": "You are a DevOps and security auditor."},
            {
                "role": "user",
                "content": (
                    "Review this Docker environment file and identify the critical security flaw:\n"
                    "DEBUG=True\n"
                    "SECRET_KEY=django-insecure-default-change-in-production-12345\n"
                    "ALLOWED_HOSTS=*\n"
                    "DATABASE_URL=sqlite:///db.sqlite3\n"
                    "Provide a 1-sentence remediation."
                ),
            },
        ]
        try:
            res = client.chat_completion(messages, temperature=0.1)
            content = res.content.lower()
            # Pass if it flags SECRET_KEY or DEBUG or ALLOWED_HOSTS
            passed = "secret_key" in content or "debug" in content or "insecure" in content
            return TestResult(
                name=self.name,
                category=self.category,
                passed=passed,
                tokens_per_sec=res.tokens_per_sec,
                latency_sec=res.latency_sec,
                details="Correctly identified insecure configuration" if passed else "Failed to flag insecure secrets",
            )
        except Exception as e:
            return TestResult(
                name=self.name,
                category=self.category,
                passed=False,
                error_message=str(e),
            )
