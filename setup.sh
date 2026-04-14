#!/bin/bash
cd "$(dirname "$0")"
BOT_DIR=$(pwd)

echo "DayZero Bot Setup"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install discord.py aiohttp python-dotenv

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    read -p "Enter your bot token: " TOKEN
    echo "TOKEN=$TOKEN" > .env
    echo ".env created."
else
    echo ".env already exists, skipping."
fi

# Make scripts executable
chmod +x update.sh restart.sh

# Add cron jobs
CRON_UPDATE="* * * * * $BOT_DIR/update.sh >> $BOT_DIR/update.log 2>&1"
CRON_RESTART="0 6 * * * $BOT_DIR/restart.sh >> $BOT_DIR/restart.log 2>&1"

(crontab -l 2>/dev/null | grep -v "$BOT_DIR/update.sh" | grep -v "$BOT_DIR/restart.sh"; echo "$CRON_UPDATE"; echo "$CRON_RESTART") | crontab -

echo "Cron jobs added:"
echo "  - Auto-update: checks every minute"
echo "  - Auto-restart: daily at 6:00 AM"

# Start the bot
echo "Starting bot..."
nohup python3 bot.py > bot.log 2>&1 &
echo "Bot started (PID: $!)."

echo ""
echo "Setup complete"
echo "Logs: $BOT_DIR/bot.log"
echo "Update log: $BOT_DIR/update.log"
echo "Restart log: $BOT_DIR/restart.log"
