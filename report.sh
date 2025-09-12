#!/bin/sh

REPORT_DIR="./reports"
# LOG_FILE="$REPORT_DIR/$(date '+%Y-%m-%d_%H-%M-%S').log"
mkdir -p "$REPORT_DIR"
ls -1t "$REPORT_DIR" | tail -n +7 | xargs -I {} rm -f "$REPORT_DIR/{}"

python3 generate_report.py
