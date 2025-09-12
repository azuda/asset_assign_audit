#!/bin/sh

LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/$(date '+%Y-%m-%d_%H-%M-%S').log"
mkdir -p "$LOG_DIR"
ls -1t "$LOG_DIR" | tail -n +7 | xargs -I {} rm -f "$LOG_DIR/{}"

PROJECT="$PWD"
VENV="$PROJECT/.venv/bin/python3"

echo "Script start @ $(date)" >> "$LOG_FILE"

sh query_jamf.sh >> "$LOG_FILE" 2>&1
$VENV query_assetsonar.py >> "$LOG_FILE" 2>&1
$VENV parse_responses.py >> "$LOG_FILE" 2>&1
$VENV retire_assets.py >> "$LOG_FILE" 2>&1
$VENV audit_users.py >> "$LOG_FILE" 2>&1
$VENV auto_checkout.py >> "$LOG_FILE" 2>&1
sh report.sh >> "$LOG_FILE" 2>&1

echo -e "\nScript end @ $(date)" >> "$LOG_FILE"
