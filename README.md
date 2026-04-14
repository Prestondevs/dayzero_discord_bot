# DayZero Discord Bot

A feature-rich Discord bot built for the DayZero Cybersecurity Club. Packed with security tools, CTF tracking, encoding utilities, moderation, and more.

## Features

### Security Tools
- **IP Lookup** — Geolocation and network info for any IP or domain
- **DNS / Reverse DNS** — Query DNS records, reverse lookups
- **CVE Search** — Look up vulnerabilities by CVE ID with CVSS scores
- **WHOIS** — Domain registration info
- **HTTP Headers** — Security header audit for any URL
- **Port Scanner** — TCP connect test on a host/port
- **Port Reference** — Common port number database
- **Subnet Calculator** — CIDR notation breakdown
- **Hash Generator** — MD5, SHA1, SHA256, SHA512
- **Password Checker** — Strength analysis with entropy scoring

### Encoding & Ciphers
- Base64, Hex, URL, Binary, Morse code encode/decode
- ROT13, Caesar cipher (with brute force option)
- String analysis with encoding detection

### CTFTime Integration
- Automatic hourly updates of upcoming CTF competitions
- Manual lookup with `.ctftime`
- Configure a channel with `.setctftimechannel #channel`

### Security News
- Automatic hourly posts from The Hacker News RSS feed
- Manual lookup with `.secnews`
- Configure a channel with `.setsecnewschannel #channel`

### Scheduling
- Schedule announcements to specific channels with a delay
- Recurring announcements on an interval
- Personal reminders
- All schedules persist across restarts via CSV

### Moderation (Admin Only)
- Kick, ban, unban, mute/timeout, unmute
- Purge messages, slowmode, channel lock/unlock
- Warnings, nickname changes
- Bot self-protection (can't be used against itself)

### Utility
- **Ping** — Show bot latency
- **Uptime** — Show how long the bot has been running
- **Bot Info** — Bot stats, version, server count
- **Server Info** — Server details, member count, boost level
- **User Info** — User account details and roles
- **Avatar** — View a user's avatar in full size
- **Role Info** — Role details and permissions
- **Poll** — Create a poll with up to 10 options
- **Vote** — Quick yes/no vote
- **Coin Flip / Dice Roll** — Random coin flip or NdN dice roll
- **Embed Builder** — Create custom embed messages (admin)
- **Contribute** — Link to the GitHub repo

### Welcome System
- Configurable welcome/leave messages
- Auto-role assignment on join
- Optional DM on join

## Setup

### Requirements
- Python 3.10+
- A Discord bot token from the [Developer Portal](https://discord.com/developers/applications)

### Install
```bash
git clone https://github.com/Prestondevs/dayzero_discord_bot.git
cd dayzero_discord_bot
pip install -r requirements.txt
```

### Configure
```bash
echo "TOKEN=your_bot_token_here" > .env
```

Optional: set a custom prefix (default is `.`):
```bash
echo "PREFIX=!" >> .env
```

### Run
```bash
python bot.py
```

## Deploying on a Server

```bash
git clone https://github.com/Prestondevs/dayzero_discord_bot.git
cd dayzero_discord_bot
pip3 install discord.py aiohttp python-dotenv
echo "TOKEN=your_bot_token_here" > .env
```

Then to keep it running after you close the terminal:

```bash
nohup python3 bot.py > bot.log 2>&1 &
```

- `nohup` — survives you logging out
- `> bot.log 2>&1` — logs output to a file
- `&` — runs in background

Useful commands after that:

```bash
cat bot.log           # check logs
tail -f bot.log       # watch logs live
ps aux | grep bot.py  # find the process
kill <PID>            # stop it
```

To update later:

```bash
kill $(pgrep -f bot.py)
git pull
nohup python3 bot.py > bot.log 2>&1 &
```

### Bot Permissions
When inviting the bot, it needs:
- Administrator (recommended), or individually:
  - Kick/Ban Members, Moderate Members
  - Manage Channels, Manage Roles, Manage Nicknames, Manage Messages
  - Send Messages, Embed Links, Read Message History, Add Reactions

Enable these intents in the Developer Portal:
- **Message Content Intent**
- **Server Members Intent**

## Permissions

All moderation, scheduling, and configuration commands require **Administrator**. Encoding tools, security lookups, and informational commands are available to everyone.

---

*Authored by Preston V.*
