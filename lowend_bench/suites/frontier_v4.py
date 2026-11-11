"""
Frontier Challenge V4: Adversarial Agent & Systems Benchmark Suite.
Evaluates local models on 8 real-world frontier agent scenarios:
1. Obfuscated JS Unpacking (Unpacking Dean Edwards / XOR packed media stream URLs)
2. Cloudflare / Iframe Challenge Navigation (Frame locator & verification targeting)
3. Multi-Chunk Range Download & SHA256 Reassembly (Parallel streams & hash validation)
4. WebSocket / SSE Realtime Feed Sniffing (Connecting to wss:// / text/event-stream)
5. Fuzzy Patch / Line Drift Conflict Resolution (Applying diffs with shifted line offsets)
6. Parameterized SQL Migration Security (Eliminating raw string formatting vulnerabilities)
7. Multipart Form-Data Complex Upload via cURL (-F meta JSON + -F file binary)
8. Orphaned Zombie Process Tree Cleanup (Clean kill of parent + all sub-renderers)
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from lowend_bench.client import LLMClient
from lowend_bench.base import BaseTestCase, TestResult


V4_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click an element matching the selector in the active page or frame.",
            "parameters": {
                "type": "object",
                "properties": {"selector": {"type": "string"}},
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_fill",
            "description": "Type text into an input field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["selector", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_run_code",
            "description": "Execute Playwright code in the browser context.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
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

V4_SYSTEM_PROMPT = (
    "You are an elite autonomous agent. You MUST execute tasks using the provided tools. "
    "Do NOT output markdown code blocks or conversational text without calling a tool."
)


def run_frontier_v4_suite(client: LLMClient) -> List[TestResult]:
    """Execute all 8 Frontier Challenge V4 tests."""
    results = []

    # 1. Obfuscated JS Unpacking
    p1 = (
        "A streaming site serves direct download links packed inside obfuscated JS on the page:\n"
        "<script type=\"text/javascript\">\n"
        "eval(function(p,a,c,k,e,d){e=function(c){return c};if(!''.replace(/^/,String)){"
        "while(c--){d[c]=k[c]||c}k=[function(e){return d[e]}];e=function(){return'\\\\w+'};c=1};"
        "while(c--){if(k[c]){p=p.replace(new RegExp('\\\\b'+e(c)+'\\\\b','g'),k[c])}}return p}"
        "('var direct_media_cdn=\"https://edge.video-host.net/streams/hls/master.m3u8?token=AUTH_SEC_992\";',"
        "10,10,'||||||||direct_media_cdn|https'.split('|'),0,{}))\n"
        "</script>\n"
        "Execute a command or script using browser_run_code or bash to unpack this expression and output the unescaped direct_media_cdn URL."
    )
    try:
        r1 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p1}],
            tools=V4_TOOLS,
        )
        act1 = str([f"{tc.name}({tc.arguments})" for tc in r1.tool_calls]) if r1.tool_calls else r1.content[:200]
        pass1 = ("direct_media_cdn" in act1 or "edge.video-host.net" in act1 or "master.m3u8" in act1) and (
            "browser_run_code" in act1 or "node" in act1 or "python" in act1 or "bash" in act1
        )
        results.append(
            TestResult(
                name="V4-1: Obfuscated JS URL Unpacking",
                category="frontier_v4",
                passed=pass1,
                tokens_per_sec=r1.tokens_per_sec,
                latency_sec=r1.latency_sec,
                details="Unpacked obfuscated JS expression" if pass1 else "Failed to unpack JS expression",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-1: Obfuscated JS URL Unpacking", "frontier_v4", False, error_message=str(e)))

    # 2. Cloudflare / Iframe Challenge Navigation
    p2 = (
        "A website displays a verification challenge enclosed inside an iframe:\n"
        "<iframe src=\"https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/b/turnstile/if/ov2/...\" id=\"cf-chl-widget\">\n"
        "  #document\n"
        "  <input type=\"checkbox\" id=\"challenge-stage-checkbox\">\n"
        "</iframe>\n"
        "Standard page.click('#challenge-stage-checkbox') fails because it is inside an isolated frame.\n"
        "Execute Playwright code using browser_run_code to locate the iframe via frameLocator and click the checkbox."
    )
    try:
        r2 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p2}],
            tools=V4_TOOLS,
        )
        act2 = str([f"{tc.name}({tc.arguments})" for tc in r2.tool_calls]) if r2.tool_calls else r2.content[:200]
        pass2 = "browser_run_code" in act2 and (
            "frameLocator" in act2 or "frames()" in act2 or "contentFrame" in act2
        ) and "challenge-stage-checkbox" in act2
        results.append(
            TestResult(
                name="V4-2: Cloudflare Turnstile Iframe Piercing",
                category="frontier_v4",
                passed=pass2,
                tokens_per_sec=r2.tokens_per_sec,
                latency_sec=r2.latency_sec,
                details="Pierced iframe boundary via frameLocator" if pass2 else "Failed to target frameLocator",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-2: Cloudflare Turnstile Iframe Piercing", "frontier_v4", False, error_message=str(e)))

    # 3. Multi-Chunk Range Download & SHA256 Reassembly
    p3 = (
        "A 100MB file is hosted in 4 separate chunks:\n"
        "- https://cdn.storage.org/file.part0\n"
        "- https://cdn.storage.org/file.part1\n"
        "- https://cdn.storage.org/file.part2\n"
        "- https://cdn.storage.org/file.part3\n"
        "Expected final file SHA-256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'\n"
        "Execute a bash script that downloads all 4 parts, concatenates them into /tmp/full_file.bin in order, "
        "and verifies the sha256sum matches."
    )
    try:
        r3 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p3}],
            tools=V4_TOOLS,
        )
        act3 = str([f"{tc.name}({tc.arguments})" for tc in r3.tool_calls]) if r3.tool_calls else r3.content[:200]
        pass3 = "bash" in act3 and ("cat" in act3 or ">>" in act3) and "sha256sum" in act3 and "e3b0c442" in act3 and "full_file.bin" in act3
        results.append(
            TestResult(
                name="V4-3: Multi-Chunk Range Assembly & SHA256",
                category="frontier_v4",
                passed=pass3,
                tokens_per_sec=r3.tokens_per_sec,
                latency_sec=r3.latency_sec,
                details="Assembled 4 parts and verified sha256" if pass3 else "Incomplete assembly or hash check",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-3: Multi-Chunk Range Assembly & SHA256", "frontier_v4", False, error_message=str(e)))

    # 4. WebSocket / SSE Live Feed Sniffing
    p4 = (
        "A market exchange sends realtime price events via WebSocket at wss://stream.crypto-feed.io/v1/ticks.\n"
        "Standard HTTP GET requests fail.\n"
        "Execute a command (using Playwright page.on('websocket'), websocat, wscat, or node/python script via bash) "
        "to connect to the WebSocket, read 3 ticks, and save them to /tmp/ticks.jsonl."
    )
    try:
        r4 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p4}],
            tools=V4_TOOLS,
        )
        act4 = str([f"{tc.name}({tc.arguments})" for tc in r4.tool_calls]) if r4.tool_calls else r4.content[:200]
        pass4 = ("wss://" in act4 or "crypto-feed.io" in act4) and (
            "websocket" in act4.lower() or "wscat" in act4 or "websocat" in act4 or "ws" in act4
        ) and "/tmp/ticks.jsonl" in act4
        results.append(
            TestResult(
                name="V4-4: WebSocket / SSE Realtime Stream Sniffing",
                category="frontier_v4",
                passed=pass4,
                tokens_per_sec=r4.tokens_per_sec,
                latency_sec=r4.latency_sec,
                details="Connected to wss:// and captured ticks" if pass4 else "Missed WebSocket protocol handling",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-4: WebSocket / SSE Realtime Stream Sniffing", "frontier_v4", False, error_message=str(e)))

    # 5. Fuzzy Patch / Line Drift Conflict Resolution
    p5 = (
        "You must apply a patch to /src/server.cpp, but recent commits shifted line numbers down by +25 lines.\n"
        "A rigid 'git apply patch.diff' fails with 'patch does not apply'.\n"
        "Execute a bash command or script using fuzzy matching (e.g. 'git apply -C1 --reject', 'patch -p1 -F3', or python regex replace) "
        "to apply the patch cleanly without failing."
    )
    try:
        r5 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p5}],
            tools=V4_TOOLS,
        )
        act5 = str([f"{tc.name}({tc.arguments})" for tc in r5.tool_calls]) if r5.tool_calls else r5.content[:200]
        pass5 = "bash" in act5 and ("patch" in act5 or "git apply" in act5 or "python" in act5) and (
            "-C" in act5 or "--reject" in act5 or "-F" in act5 or "--fuzz" in act5 or "3" in act5 or "fuzzy" in act5.lower()
        )
        results.append(
            TestResult(
                name="V4-5: Fuzzy Git Patch Drift Resolution",
                category="frontier_v4",
                passed=pass5,
                tokens_per_sec=r5.tokens_per_sec,
                latency_sec=r5.latency_sec,
                details="Applied fuzzy offset tolerance" if pass5 else "Used rigid patch without fuzz tolerance",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-5: Fuzzy Git Patch Drift Resolution", "frontier_v4", False, error_message=str(e)))

    # 6. Parameterized SQL Migration Security
    p6 = (
        "An insecure backend migration function has:\n"
        "query = f\"UPDATE users SET email = '{new_email}' WHERE org_id = '{org_id}'\"\n"
        "db.execute(query)\n\n"
        "Rewrite this in Python using sqlite3/psycopg parameterized queries with placeholders (? or %s) "
        "to eliminate SQL injection vulnerabilities entirely. Execute the code to update /data/app.db."
    )
    try:
        r6 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p6}],
            tools=V4_TOOLS,
        )
        act6 = str([f"{tc.name}({tc.arguments})" for tc in r6.tool_calls]) if r6.tool_calls else r6.content[:200]
        pass6 = ("?" in act6 or "%s" in act6 or ":email" in act6) and (
            "new_email" in act6 and "org_id" in act6
        ) and ("f\"UPDATE" not in act6 and "f'UPDATE" not in act6)
        results.append(
            TestResult(
                name="V4-6: Parameterized SQL Migration Security",
                category="frontier_v4",
                passed=pass6,
                tokens_per_sec=r6.tokens_per_sec,
                latency_sec=r6.latency_sec,
                details="Parameterized SQL query eliminated injection" if pass6 else "Vulnerable string formatting detected",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-6: Parameterized SQL Migration Security", "frontier_v4", False, error_message=str(e)))

    # 7. Multipart Form-Data Complex Upload via cURL
    p7 = (
        "Upload an archive /tmp/package.tar.gz to https://api.cloud-deploy.com/v1/artifacts.\n"
        "The API strictly requires multipart/form-data with:\n"
        "- Field 'manifest': JSON string '{\"version\": \"1.4.0\", \"target\": \"production\"}' (Content-Type: application/json)\n"
        "- Field 'payload': the binary file /tmp/package.tar.gz\n"
        "- Authorization header: Bearer TOKEN_XYZ_991\n"
        "Execute the exact cURL command to perform this upload."
    )
    try:
        r7 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p7}],
            tools=V4_TOOLS,
        )
        act7 = str([f"{tc.name}({tc.arguments})" for tc in r7.tool_calls]) if r7.tool_calls else r7.content[:200]
        pass7 = "bash" in act7 and "curl" in act7 and "-F" in act7 and "package.tar.gz" in act7 and "TOKEN_XYZ_991" in act7 and (
            "application/json" in act7 or "manifest=" in act7
        )
        results.append(
            TestResult(
                name="V4-7: Resumable Multipart Form Upload via cURL",
                category="frontier_v4",
                passed=pass7,
                tokens_per_sec=r7.tokens_per_sec,
                latency_sec=r7.latency_sec,
                details="Valid multipart/form-data with JSON header" if pass7 else "Malformed form-data arguments",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-7: Resumable Multipart Form Upload via cURL", "frontier_v4", False, error_message=str(e)))

    # 8. Orphaned Zombie Process Tree Cleanup
    p8 = (
        "A rogue web scraper spawned child renderer processes that were orphaned and left hanging:\n"
        "Parent PID: 4910\n"
        "Children PIDs: 4911, 4912, 4913\n"
        "Execute a bash command that finds and terminates the entire process tree (parent and all descendants) "
        "cleanly using SIGTERM, followed by SIGKILL if still running."
    )
    try:
        r8 = client.chat_completion(
            [{"role": "system", "content": V4_SYSTEM_PROMPT}, {"role": "user", "content": p8}],
            tools=V4_TOOLS,
        )
        act8 = str([f"{tc.name}({tc.arguments})" for tc in r8.tool_calls]) if r8.tool_calls else r8.content[:200]
        pass8 = "bash" in act8 and (
            "pkill" in act8 or "pgrep" in act8 or "kill -- -" in act8 or "pstree" in act8 or "4910" in act8
        ) and ("SIGTERM" in act8 or "-TERM" in act8 or "-15" in act8 or "kill" in act8)
        results.append(
            TestResult(
                name="V4-8: Zombie Subtree Process Termination",
                category="frontier_v4",
                passed=pass8,
                tokens_per_sec=r8.tokens_per_sec,
                latency_sec=r8.latency_sec,
                details="Clean subtree/group kill command generated" if pass8 else "Incomplete or single-process kill",
            )
        )
    except Exception as e:
        results.append(TestResult("V4-8: Zombie Subtree Process Termination", "frontier_v4", False, error_message=str(e)))

    return results
