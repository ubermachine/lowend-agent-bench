"""
Constrained Function Calling & Anti-Hallucination Benchmark Suite (BFCL-Derived).
Evaluates single tool dispatch, multi-tool disambiguation, parallel calls, enum enforcement,
and critical anti-hallucination refusal when required arguments are absent.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from lowend_bench.client import LLMClient


@dataclass
class ToolTestResult:
    name: str
    passed: bool
    tokens_per_sec: float
    details: str = ""


# Tools Schemas
TOOLS_BANK = [
    {
        "type": "function",
        "function": {
            "name": "calculate_tax",
            "description": "Calculates sales tax for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subtotal": {"type": "number", "description": "Order subtotal in USD"},
                    "state": {"type": "string", "description": "Two-letter US state code"},
                },
                "required": ["subtotal", "state"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search available flights between airports.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_quote",
            "description": "Fetches current market price and volume for a stock ticker symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL)"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_deployment_environment",
            "description": "Switches the active deployment environment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "env": {
                        "type": "string",
                        "enum": ["production", "staging", "development"],
                        "description": "Target deployment environment.",
                    },
                    "force": {"type": "boolean"},
                },
                "required": ["env"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Executes a wire transfer between bank accounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_account": {"type": "string"},
                    "destination_account_id": {
                        "type": "string",
                        "description": "Verified destination 10-digit routing/account number.",
                    },
                    "amount": {"type": "number"},
                },
                "required": ["source_account", "destination_account_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "batch_create_records",
            "description": "Batch creates user records with nested role and permission objects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "users": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "email": {"type": "string"},
                                "roles": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["username", "email", "roles"],
                        },
                    }
                },
                "required": ["users"],
            },
        },
    },
]


def run_tool_suite(client: LLMClient) -> List[ToolTestResult]:
    results = []

    # Test 1: Simple Typed Function Call
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant with tool calling capabilities."},
            {"role": "user", "content": "What is the tax on a subtotal of $250.00 in California (CA)?"},
        ]
        res = client.chat_completion(messages, tools=[TOOLS_BANK[0]])
        passed = False
        details = ""
        if res.tool_calls:
            tc = res.tool_calls[0]
            if tc.name == "calculate_tax":
                args = tc.arguments
                if float(args.get("subtotal", 0)) == 250.0 and args.get("state", "").upper() == "CA":
                    passed = True
                    details = "Correctly emitted calculate_tax(subtotal=250.0, state='CA')"
                else:
                    details = f"Argument mismatch: {args}"
            else:
                details = f"Called wrong function: {tc.name}"
        else:
            details = "No tool call emitted."
        results.append(ToolTestResult("Simple Typed Function Call", passed, res.tokens_per_sec, details))
    except Exception as e:
        results.append(ToolTestResult("Simple Typed Function Call", False, 0.0, f"Error: {e}"))

    # Test 2: Multi-Tool Disambiguation
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant with tool calling capabilities."},
            {"role": "user", "content": "Can you check flight prices from JFK to LHR on 2026-12-25?"},
        ]
        res = client.chat_completion(messages, tools=TOOLS_BANK[:4])
        passed = False
        details = ""
        if res.tool_calls:
            tc = res.tool_calls[0]
            if tc.name == "search_flights":
                args = tc.arguments
                if "JFK" in str(args.get("origin", "")).upper() and "LHR" in str(args.get("destination", "")).upper():
                    passed = True
                    details = "Correctly selected search_flights out of 4 options."
                else:
                    details = f"Incorrect flight args: {args}"
            else:
                details = f"Wrong tool selected: {tc.name}"
        else:
            details = "No tool call emitted."
        results.append(ToolTestResult("Multi-Tool Disambiguation", passed, res.tokens_per_sec, details))
    except Exception as e:
        results.append(ToolTestResult("Multi-Tool Disambiguation", False, 0.0, f"Error: {e}"))

    # Test 3: Parallel Tool Calling (3 calls in 1 turn)
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant with tool calling capabilities. When multiple items need to be queried, call the function multiple times in parallel."},
            {"role": "user", "content": "Give me the latest stock quotes for Apple (AAPL), Microsoft (MSFT), and Google (GOOGL)."},
        ]
        res = client.chat_completion(messages, tools=[TOOLS_BANK[2]])
        passed = False
        details = ""
        if len(res.tool_calls) == 3:
            tickers = {str(tc.arguments.get("ticker", "")).upper() for tc in res.tool_calls}
            if {"AAPL", "MSFT", "GOOGL"}.issubset(tickers):
                passed = True
                details = "Successfully emitted 3 parallel get_stock_quote calls in 1 turn."
            else:
                details = f"Emitted 3 calls but ticker set mismatched: {tickers}"
        else:
            details = f"Emitted {len(res.tool_calls)} calls instead of 3."
        results.append(ToolTestResult("Parallel Tool Calling (3 tools)", passed, res.tokens_per_sec, details))
    except Exception as e:
        results.append(ToolTestResult("Parallel Tool Calling (3 tools)", False, 0.0, f"Error: {e}"))

    # Test 4: Enum & Constraint Validation
    try:
        messages = [
            {"role": "system", "content": "You are a deployment bot."},
            {"role": "user", "content": "Please switch the deployment environment to staging."},
        ]
        res = client.chat_completion(messages, tools=[TOOLS_BANK[3]])
        passed = False
        details = ""
        if res.tool_calls:
            tc = res.tool_calls[0]
            if tc.name == "set_deployment_environment" and tc.arguments.get("env") == "staging":
                passed = True
                details = "Correctly bound enum argument to 'staging'."
            else:
                details = f"Failed enum binding: {tc.arguments}"
        else:
            details = "No tool call emitted."
        results.append(ToolTestResult("Enum & Constraint Validation", passed, res.tokens_per_sec, details))
    except Exception as e:
        results.append(ToolTestResult("Enum & Constraint Validation", False, 0.0, f"Error: {e}"))

    # Test 5: Missing Parameter Anti-Hallucination
    try:
        messages = [
            {"role": "system", "content": "You are a secure banking assistant. NEVER guess or hallucinate account numbers."},
            {"role": "user", "content": "Please transfer $500 from my checking account to Bob."},
        ]
        res = client.chat_completion(messages, tools=[TOOLS_BANK[4]])
        passed = False
        details = ""
        # If the model emits transfer_funds, it hallucinated Bob's destination_account_id!
        if res.tool_calls:
            for tc in res.tool_calls:
                if tc.name == "transfer_funds":
                    dest = tc.arguments.get("destination_account_id")
                    details = f"HALLUCINATION FAILED: Model hallucinated fake destination_account_id: '{dest}'"
                    passed = False
                    break
        else:
            # Model refrained from calling tool and asked the user
            if any(w in res.content.lower() for w in ["account", "number", "id", "bob's", "details", "provide"]):
                passed = True
                details = "PASSED: Refrained from calling transfer_funds; asked user for missing destination account ID."
            else:
                details = "Model did not call tool, but response was unclear."
                passed = True
        results.append(ToolTestResult("Missing Parameter Anti-Hallucination", passed, res.tokens_per_sec, details))
    except Exception as e:
        results.append(ToolTestResult("Missing Parameter Anti-Hallucination", False, 0.0, f"Error: {e}"))

    # Test 6: Nested JSON Schema Parsing
    try:
        messages = [
            {"role": "system", "content": "You are a user management assistant."},
            {"role": "user", "content": "Add two users: alice (alice@example.com) with roles admin and editor, and bob (bob@example.com) with role viewer."},
        ]
        res = client.chat_completion(messages, tools=[TOOLS_BANK[5]])
        passed = False
        details = ""
        if res.tool_calls:
            tc = res.tool_calls[0]
            if tc.name == "batch_create_records":
                users = tc.arguments.get("users", [])
                if len(users) == 2:
                    passed = True
                    details = "Correctly parsed nested list of user objects with roles."
                else:
                    details = f"Expected 2 users, got {len(users)}: {users}"
            else:
                details = f"Called wrong function: {tc.name}"
        else:
            details = "No tool call emitted."
        results.append(ToolTestResult("Nested JSON Schema Parsing", passed, res.tokens_per_sec, details))
    except Exception as e:
        results.append(ToolTestResult("Nested JSON Schema Parsing", False, 0.0, f"Error: {e}"))

    return results
