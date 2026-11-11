# Benchmark Scorecard: `gpt-oss-20b-heretic-v2`

* **Endpoint:** `http://127.0.0.1:8080/v1`
* **Date:** 2026-11-08 23:30:15
* **Platform:** AMD Ryzen AI MAX+ 392 (Strix Halo) / Radeon 8060S (32GB LPDDR5X-8000)

---

## 1. Diff Editing & Patching Suite (Aider SEARCH/REPLACE)
| Test Case | Result | Solved On | Generation Speed | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Two Sum (Duplicates & Multi-Index) | **PASSED** | Turn 1 (Zero-Shot) | 101.6 t/s | Clean O(n) hash map implementation |
| Expiring LRU Cache (TTL Eviction) | **PASSED** | Turn 1 (Zero-Shot) | 114.8 t/s | Clean OrderedDict + timestamp expiry |
| SemVer 2.0 Parser & Comparator | **PASSED** | Turn 2 (Reflection) | 95.4 t/s | Corrected build metadata precedence |

*Suite Pass Rate:* **3 / 3 (100.0%)**

## 2. Function Calling & Anti-Hallucination Suite
| Test Case | Result | Speed | Evaluation Details |
| :--- | :--- | :--- | :--- |
| Simple Typed Function Call | **PASSED** | 57.7 t/s | Emitted `calculate_tax(subtotal=250.0, state='CA')` |
| Multi-Tool Disambiguation | **PASSED** | 58.2 t/s | Accurately selected `search_flights` |
| Parallel Tool Calling (3 tools) | **PASSED** | 43.5 t/s | Emitted 3 parallel `get_stock_quote` calls |
| Enum & Constraint Validation | **PASSED** | 62.0 t/s | Strictly bound env enum to `staging` |
| Missing Parameter Anti-Hallucination | **PASSED** | N/A | **Refrained from calling tool**; asked for Bob's account ID |
| Nested JSON Schema Parsing | **PASSED** | 71.1 t/s | Parsed nested user array and roles |

*Suite Accuracy:* **6 / 6 (100.0%)**

## 3. Context Scaling & Needle Retrieval
| Context Depth | Result | Latency | Prefill Speed | Generation Speed | Output Snippet |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2048 tokens | **PASSED** | 0.95s | 2,157.9 t/s | 112.4 t/s | `SEC_KEY_2048_4821` |
| 8192 tokens | **PASSED** | 3.82s | 2,144.5 t/s | 108.7 t/s | `SEC_KEY_8192_9104` |
| 16384 tokens | **PASSED** | 7.61s | 2,152.9 t/s | 104.2 t/s | `SEC_KEY_16384_3012` |
| 32768 tokens | **PASSED** | 15.22s | 2,153.0 t/s | 99.8 t/s | `SEC_KEY_32768_7721` |

*Retrieval Rate:* **4 / 4 (100.0%)**

## 4. Adversarial Agent Resilience
| Adversarial Task | Result | Speed | Evaluation Details |
| :--- | :--- | :--- | :--- |
| Obfuscated JS String Unpacking | **PASSED** | 113.1 t/s | Extracted `https://api.secure-domain.io/v1/auth/token` |
| Cloudflare Turnstile Iframe Detection | **PASSED** | 72.2 t/s | Identified Cloudflare Turnstile challenge |
| Resumable Range Chunking Header | **PASSED** | 75.1 t/s | Generated `-H "Range: bytes=10485760-20971519"` |
| Zombie Process Subtree Termination | **PASSED** | 104.0 t/s | Generated `kill -TERM -4102` process group kill |

*Resilience Rate:* **4 / 4 (100.0%)**

---

### Overall Score: **17 / 17 (100.0%)**
