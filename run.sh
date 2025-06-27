#!/bin/sh

LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/$(date '+%Y-%m-%d_%H-%M-%S').log"
mkdir -p "$LOG_DIR"
ls -1t "$LOG_DIR" | tail -n +7 | xargs -I {} rm -f "$LOG_DIR/{}"

echo "Script start @ $(date)" >> "$LOG_FILE"

sh query_jamf.sh >> "$LOG_FILE" 2>&1
python3 query_assetsonar.py >> "$LOG_FILE" 2>&1
python3 parse_responses.py >> "$LOG_FILE" 2>&1
python3 retire_assets.py >> "$LOG_FILE" 2>&1
python3 audit_users.py >> "$LOG_FILE" 2>&1

echo -e "\nScript end @ $(date)" >> "$LOG_FILE"
