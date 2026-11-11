"""
Context Window Scaling & Needle Stress Benchmark Suite.
Measures instruction adherence, memory pressure, and prefill/generation degradation
as context grows from 2k to 8k, 16k, and 32k tokens.
"""

import random
from typing import Dict, Any, List
from dataclasses import dataclass
from lowend_bench.client import LLMClient


@dataclass
class ContextStressResult:
    target_tokens: int
    prompt_tokens: int
    passed: bool
    latency_sec: float
    prefill_tps: float
    gen_tps: float
    details: str = ""


# Deterministic text generation for synthetic context filler
FILLER_SENTENCES = [
    "The distributed memory subsystem utilizes non-blocking synchronized queues to schedule asynchronous DMA transfers.",
    "Database replica nodes synchronize via the Raft consensus protocol with periodic heartbeat exchanges every 250 milliseconds.",
    "Kernel page tables are initialized in early boot with identity mappings configured for all physical memory apertures.",
    "The compiler optimizer performs common subexpression elimination across basic blocks within the intermediate representation.",
    "TLS session resumption caches cryptographic ticket keys protected by ephemeral elliptic-curve Diffie-Hellman handshakes.",
    "Network packets traversing the ingress pipeline are filtered against access control lists prior to socket buffer allocation.",
]


def generate_filler_text(approx_tokens: int) -> str:
    """Generate pseudo-code / technical documentation filler."""
    words = []
    # ~1.3 words per token
    target_words = int(approx_tokens * 0.75)
    rng = random.Random(42)  # Fixed seed for reproducibility
    while len(words) < target_words:
        sentence = rng.choice(FILLER_SENTENCES)
        words.extend(sentence.split())
    return " ".join(words[:target_words])


def run_context_suite(
    client: LLMClient, test_depths: List[int] = None
) -> List[ContextStressResult]:
    if test_depths is None:
        # Default testing depths: 2k, 8k, 16k, 32k
        test_depths = [2048, 8192, 16384, 32768]

    results = []

    for depth in test_depths:
        secret_key = f"SEC_KEY_{depth}_{random.randint(1000, 9999)}"
        filler = generate_filler_text(depth - 300)

        # Place needle at ~75% depth (the hardest retrieval point for RoPE)
        split_idx = int(len(filler) * 0.75)
        needle = f"\n\n[CONFIDENTIAL INSTRUCTION: The verification passkey for depth {depth} is '{secret_key}'.]\n\n"
        full_context = filler[:split_idx] + needle + filler[split_idx:]

        messages = [
            {
                "role": "system",
                "content": "You are a technical context analyzer. Read the provided documentation carefully and answer the user query accurately.",
            },
            {
                "role": "user",
                "content": f"{full_context}\n\nWhat is the verification passkey for depth {depth}? Reply with ONLY the passkey and nothing else.",
            },
        ]

        try:
            res = client.chat_completion(
                messages, temperature=0.0, max_tokens=128
            )
            passed = secret_key in res.content
            # Estimate prefill t/s
            prefill_tps = (
                res.prompt_tokens / res.latency_sec
                if res.latency_sec > 0
                else 0.0
            )

            results.append(
                ContextStressResult(
                    target_tokens=depth,
                    prompt_tokens=res.prompt_tokens,
                    passed=passed,
                    latency_sec=res.latency_sec,
                    prefill_tps=prefill_tps,
                    gen_tps=res.tokens_per_sec,
                    details=f"Output: '{res.content.strip()}'",
                )
            )
        except Exception as e:
            results.append(
                ContextStressResult(
                    target_tokens=depth,
                    prompt_tokens=0,
                    passed=False,
                    latency_sec=0.0,
                    prefill_tps=0.0,
                    gen_tps=0.0,
                    details=f"Context overflow or error: {e}",
                )
            )

    return results
