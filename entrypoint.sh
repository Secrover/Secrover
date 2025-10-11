#!/bin/bash
set -e

run_scan() {
    echo "Running Secrover scan at $(date)"
    uv run main.py
}

if [ "$1" = "run_once" ]; then
    run_scan
    exit 0
fi

if [ -n "$CRON_SCHEDULE" ]; then
    # Generate crontab file for Supercronic
    CRON_SCHEDULE=$(echo "$CRON_SCHEDULE" | tr -d '"')
    echo "$CRON_SCHEDULE /entrypoint.sh run_once >> /output/secrover.log 2>&1" > /tmp/crontab
    echo "Starting Secrover with schedule: $CRON_SCHEDULE"
    exec /usr/bin/supercronic /tmp/crontab
else
    # No schedule → run once
    run_scan
fi
