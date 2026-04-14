#!/bin/bash
cd "$(dirname "$0")"

git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "$(date) — Update detected, pulling and restarting..."
    git pull origin main
    kill $(pgrep -f bot.py) 2>/dev/null
    nohup python3 bot.py > bot.log 2>&1 &
    echo "$(date) — Bot restarted."
fi
