"""
Frontier Vault Challenge: Full Multi-Stage System Integration Suite.
Evaluates the model on 5 complex autonomous agent capabilities:
1. Honeypot avoidance & HTML secret extraction (<meta name="x-vault-token"> and <div id="vault-cipher">)
2. Cursor-based manifest pagination (looping through ?cursor=<next_cursor> until null)
3. HTTP 429 Rate Limiting & Retry-After backoff handling
4. Stream cyclic XOR decryption
5. Shard reassembly in numerical index order and composite SHA-256 integrity verification
"""

import re
import sys
import tempfile
import subprocess
from typing import Dict, Any, List
from lowend_bench.client import LLMClient
from lowend_bench.base import TestResult


VAULT_SYSTEM_PROMPT = """You are an expert autonomous systems and cybersecurity automation engineer.
When given a complex task involving reverse-engineering, pagination, rate limiting, and cryptographic payload assembly:
1. Reason through the architecture, edge cases, rate limiting, and decryption algorithm.
2. Produce a single, complete, production-grade, self-contained Python 3 script inside a ```python ``` code block.
Use only standard Python 3 libraries (urllib, json, re, hashlib, time, sys, os)."""

VAULT_TASK_PROMPT = """You must write a self-contained Python 3 script that automates the extraction, paginated harvesting, decryption, and integrity verification of sharded data from a protected API endpoint.

Target Service: http://127.0.0.1:18889
Destination File: /tmp/vault_payload.bin

Step-by-Step Requirements & Constraints:
1. Scraping & Secret Extraction:
   - Target page: http://127.0.0.1:18889/vault/portal
   - Avoid honeypots (hidden/trap links under /vault/trap/...).
   - Extract the authentication token from the HTML <meta name="x-vault-token" content="..."> tag.
   - Extract the decryption cipher key from the `data-key` attribute of the element with id `vault-cipher` (<div id="vault-cipher" data-key="..."></div>).

2. Cursor-Based Manifest Pagination:
   - Query http://127.0.0.1:18889/vault/api/manifest using header `Authorization: Bearer <x-vault-token>`.
   - Follow pagination by passing `?cursor=<next_cursor>` until `next_cursor` is null, collecting all shard descriptors across all pages.

3. Shard Downloading & 429 Rate Limiting:
   - Download each shard from its relative `url` using header `Authorization: Bearer <x-vault-token>`.
   - The server may return HTTP 429 Too Many Requests with a `Retry-After` header (seconds).
   - Catch HTTP 429, extract `Retry-After`, sleep for that duration, and retry up to 3 times.

4. Stream Decryption & Shard Integrity:
   - Each shard's raw bytes are encrypted using cyclic XOR with the cipher key bytes:
     `decrypted_byte[i] = encrypted_byte[i] ^ key_bytes[i % len(key_bytes)]`
   - Compute the MD5 checksum of each decrypted shard and verify it matches `expected_md5`.

5. Reassembly & Final Composite Verification:
   - Sort the shards by integer `id` (0, 1, 2, ...).
   - Concatenate all decrypted shards in numerical order and write to `/tmp/vault_payload.bin`.
   - Compute the SHA256 checksum of the composite file and verify it matches `expected_composite_sha256`.

Provide your reasoning, followed by the complete executable Python 3 script inside a ```python ``` code block."""


def run_vault_challenge_suite(client: LLMClient) -> List[TestResult]:
    results = []

    messages = [
        {"role": "system", "content": VAULT_SYSTEM_PROMPT},
        {"role": "user", "content": VAULT_TASK_PROMPT},
    ]

    try:
        res = client.chat_completion(messages, temperature=0.1, max_tokens=4096)
        content = res.content

        # Extract code block
        code_match = re.search(r"```(?:python)?\s*\n(.*?)\n```", content, re.DOTALL)
        code = code_match.group(1) if code_match else content

        # Check required capabilities in generated agent code:
        # 1. Token extraction
        has_token_extract = ("x-vault-token" in code or "vault-token" in code) and ("re." in code or "find" in code or "meta" in code)
        # 2. Cipher extraction
        has_cipher_extract = ("vault-cipher" in code or "data-key" in code)
        # 3. Pagination
        has_pagination = ("cursor" in code or "next_cursor" in code) and ("while" in code or "for" in code)
        # 4. 429 Rate Limiting
        has_429 = ("429" in code or "HTTPError" in code) and ("Retry-After" in code.lower() or "retry" in code.lower()) and ("sleep" in code)
        # 5. Cyclic XOR Decryption
        has_xor = ("^" in code) and ("%" in code or "cycle" in code or "len(" in code)
        # 6. SHA256 / MD5 validation
        has_hashes = ("hashlib" in code) and ("sha256" in code) and ("md5" in code)

        score_components = {
            "Secret Extraction": has_token_extract and has_cipher_extract,
            "Cursor Pagination": has_pagination,
            "429 Retry-After Backoff": has_429,
            "Cyclic XOR Decryption": has_xor,
            "Composite Hash Integrity": has_hashes,
        }

        passed_all = all(score_components.values())
        passed_count = sum(1 for v in score_components.values() if v)
        details = ", ".join(f"{k}: {'OK' if v else 'MISSING'}" for k, v in score_components.items())

        results.append(
            TestResult(
                name="Frontier Vault: Multi-Tier Autonomous Extraction",
                category="vault_challenge",
                passed=passed_all,
                tokens_per_sec=res.tokens_per_sec,
                latency_sec=res.latency_sec,
                details=f"Passed {passed_count}/5 stages ({details})",
                metrics=score_components,
            )
        )
    except Exception as e:
        results.append(
            TestResult(
                name="Frontier Vault: Multi-Tier Autonomous Extraction",
                category="vault_challenge",
                passed=False,
                error_message=str(e),
            )
        )

    return results
