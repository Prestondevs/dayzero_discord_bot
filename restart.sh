#!/bin/bash
cd "$(dirname "$0")"

kill $(pgrep -f bot.py) 2>/dev/null
echo "$(date) — Bot stopped."

nohup python3 bot.py > bot.log 2>&1 &
echo "$(date) — Bot started (PID: $!)."
