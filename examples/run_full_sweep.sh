#!/usr/bin/env bash
# ==============================================================================
# Full Comprehensive Sweep with Markdown Export
# ==============================================================================
set -euo pipefail

ENDPOINT="${1:-http://127.0.0.1:8080/v1}"
MODEL_NAME="${2:-local-model}"
OUTPUT_FILE="reports/${MODEL_NAME}_scorecard_$(date +%Y%m%d_%H%M%S).md"

mkdir -p reports

echo "[+] Running complete benchmark sweep against $ENDPOINT..."
echo "    Model Label: $MODEL_NAME"
echo "    Output File: $OUTPUT_FILE"

python3 -m lowend_bench \
    --endpoint "$ENDPOINT" \
    --model "$MODEL_NAME" \
    --suite all \
    --max-reflection 2 \
    --export "$OUTPUT_FILE"

echo "[✓] Sweep complete. Scorecard saved to: $OUTPUT_FILE"
