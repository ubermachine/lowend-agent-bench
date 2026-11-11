"""
Zero-dependency HTTP client for OpenAI-compatible LLM endpoints.
Handles chat completions, function/tool calling, timing, and token metrics.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    latency_sec: float = 0.0
    tokens_per_sec: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw_response: Dict[str, Any] = field(default_factory=dict)


class LLMClient:
    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080/v1",
        api_key: str = "none",
        model: str = "default",
        timeout: float = 120.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def health_check(self) -> bool:
        """Check if server is reachable."""
        # Try both /health and /v1/models
        urls = [
            self.endpoint.replace("/v1", "") + "/health",
            f"{self.endpoint}/models",
        ]
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "lowend-bench"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status in (200, 204):
                        return True
            except Exception:
                continue
        return False

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a chat completion request to the OpenAI-compatible endpoint."""
        url = f"{self.endpoint}/chat/completions"

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "lowend-bench/0.1.0",
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status = response.status
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP Error {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Connection failed to {url}: {e}") from e

        t1 = time.perf_counter()
        latency = t1 - t0

        res_json = json.loads(body)
        choice = res_json.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content") or ""

        tool_calls = []
        raw_tool_calls = message.get("tool_calls") or []
        for tc in raw_tool_calls:
            fn = tc.get("function", {})
            fn_name = fn.get("name", "")
            raw_args = fn.get("arguments", "{}")
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except Exception:
                    args = {"_raw": raw_args}
            else:
                args = raw_args

            tool_calls.append(
                ToolCall(
                    id=tc.get("id", ""),
                    name=fn_name,
                    arguments=args,
                )
            )

        usage = res_json.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Estimate tokens/sec
        if completion_tokens > 0 and latency > 0:
            tokens_per_sec = completion_tokens / latency
        else:
            tokens_per_sec = (len(content.split()) * 1.33) / latency if latency > 0 else 0.0

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            latency_sec=latency,
            tokens_per_sec=tokens_per_sec,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            raw_response=res_json,
        )
