#!/usr/bin/env bash
# ==============================================================================
# Quick Evaluation Script for Active Model
# ==============================================================================
set -euo pipefail

ENDPOINT="${1:-http://127.0.0.1:8080/v1}"
SUITE="${2:-tools}"

echo "[+] Running quick evaluation against $ENDPOINT (Suite: $SUITE)..."
python3 -m lowend_bench --endpoint "$ENDPOINT" --suite "$SUITE"
