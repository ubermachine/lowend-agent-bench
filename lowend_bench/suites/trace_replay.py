"""
Trace Replay Benchmark: Real-World LibGen Failure Recovery.
Replays stranded agent state trapped on LibGen's 22,000-token raw JSON API dump:
https://libgen.li/json.php?object=f&ids=104528574,112605062...

Evaluates:
Turn 1: Zero-Shot Recovery (Direct MD5 extraction or immediate navigation)
Turn 2: Multi-Turn Self-Healing Reflection (Recovery when browser reports no DOM elements on raw JSON)
"""

from typing import Dict, Any, List
from lowend_bench.client import LLMClient
from lowend_bench.base import TestResult


LIBGEN_SAMPLE_PAYLOAD = (
    '{"104528574":{"id":"104528574","title":"Quantum Computation and Quantum Information","author":"Nielsen, Chuang",'
    '"year":"2010","edition":"10th Anniversary ed","publisher":"Cambridge University Press","pages":"702",'
    '"language":"English","topic":"Physics/Quantum","filesize":"41943040","extension":"pdf",'
    '"md5":"b3a4f619e0481ecdb4a5b035178d2b99","coverurl":"","descript":"","timeadded":"2021-04-12 18:20:00"},'
    '"112605062":{"id":"112605062","title":"Introduction to Linear Algebra","author":"Gilbert Strang",'
    '"year":"2016","edition":"5th","publisher":"Wellesley-Cambridge Press","pages":"600",'
    '"language":"English","topic":"Mathematics","filesize":"31457280","extension":"pdf",'
    '"md5":"7c89f0a12e3456789abcdef012345678","coverurl":"","descript":"","timeadded":"2022-01-05 10:14:00"}}'
)

PI_BROWSER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Navigate the browser to a given URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click an element matching the selector or target ref.",
            "parameters": {
                "type": "object",
                "properties": {"target": {"type": "string"}},
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a shell command or script on Linux.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]


def run_trace_replay_suite(client: LLMClient) -> List[TestResult]:
    results = []

    # Scenario: Agent stranded on LibGen raw JSON endpoint
    system_prompt = (
        "You are an autonomous browser agent. The user wants to download the PDF for "
        "'Quantum Computation and Quantum Information' by Nielsen & Chuang. "
        "The browser is currently displaying a raw JSON response. Use the tools to proceed toward the download."
    )

    turn1_user = (
        f"Browser URL: https://libgen.li/json.php?object=f&ids=104528574,112605062\n"
        f"Viewport Content:\n{LIBGEN_SAMPLE_PAYLOAD}\n\n"
        f"User Instruction: 'we need pdf'"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": turn1_user},
    ]

    t1_passed = False
    turn_solved = 0
    tps = 0.0
    latency = 0.0
    details = ""

    try:
        r1 = client.chat_completion(messages, tools=PI_BROWSER_TOOLS)
        tps = r1.tokens_per_sec
        latency = r1.latency_sec

        act1 = str([f"{tc.name}({tc.arguments})" for tc in r1.tool_calls]) if r1.tool_calls else r1.content

        # Check Turn 1 Zero-Shot: Did it identify the MD5 / ID or navigate to the download page?
        if (
            "b3a4f619e0481ecdb4a5b035178d2b99" in act1
            or "104528574" in act1
            or "ads.php" in act1
            or "get.php" in act1
        ):
            t1_passed = True
            turn_solved = 1
            details = "PASSED [Zero-Shot: Identified target MD5 / download link]"
        else:
            # Turn 2: Self-Healing Reflection
            # Browser simulates failure clicking non-existent DOM element
            messages.append({"role": "assistant", "content": act1})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Error: Browser clicked element, but page contains no HTML interactive elements "
                        "(content-type is application/json). Please analyze the JSON payload in your context, "
                        "extract the MD5 hash for Nielsen & Chuang ('b3a4f619e0481ecdb4a5b035178d2b99'), "
                        "and navigate to https://libgen.li/ads.php?md5=b3a4f619e0481ecdb4a5b035178d2b99 or download it via bash/curl."
                    ),
                }
            )

            r2 = client.chat_completion(messages, tools=PI_BROWSER_TOOLS)
            tps = (tps + r2.tokens_per_sec) / 2
            latency += r2.latency_sec
            act2 = str([f"{tc.name}({tc.arguments})" for tc in r2.tool_calls]) if r2.tool_calls else r2.content

            if (
                "b3a4f619e0481ecdb4a5b035178d2b99" in act2
                or "ads.php" in act2
                or "get.php" in act2
                or "curl" in act2
            ):
                t1_passed = True
                turn_solved = 2
                details = "PASSED [Reflection Turn 2: Successfully self-healed and recovered navigation]"
            else:
                details = "FAILED [Trapped in JSON viewport after reflection]"

        results.append(
            TestResult(
                name="Trace Replay: 22k JSON Viewport Navigation",
                category="trace_replay",
                passed=t1_passed,
                turn_solved=turn_solved,
                tokens_per_sec=tps,
                latency_sec=latency,
                details=details,
            )
        )
    except Exception as e:
        results.append(
            TestResult(
                name="Trace Replay: 22k JSON Viewport Navigation",
                category="trace_replay",
                passed=False,
                error_message=str(e),
            )
        )

    return results
