"""
Authored by: Preston Vardaman
DayZero Cybersecurity Club Discord Bot

A feature-rich Discord bot with cybersecurity tools, moderation,
scheduled announcements, encoding/decoding utilities, and more.
"""

import os
import asyncio
import logging
import random

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN environment variable is not set. Set TOKEN in .env before running the bot.")

PREFIX = os.getenv("PREFIX", ".")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dayzero")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
)

STATUS_QUOTES = [
    f"{PREFIX}help | DayZero",
    "Hackers gonna hack",
    "Scanning for vulnerabilities...",
    "sudo rm -rf /sleep",
    "There is no patch for stupidity",
    "Encrypt everything",
    "CTF grinding hours",
    "01100100 01100001 01111001 00110000",
    "Brute forcing your Wi-Fi...",
    "Decrypting the matrix",
    "/etc/shadow has entered the chat",
    "Kernel panic! Just kidding.",
    "Pwning noobs since day zero",
    "Wireshark is my therapist",
    "I read your packets",
    "XSS is not a clothing size",
    "SELECT * FROM secrets",
    "rm -rf doubts",
    "Trust no one. Verify everything.",
    "Have you tried turning it off and on again?",
    f"{PREFIX}contribute | help us grow",
]

@tasks.loop(minutes=5)
async def rotate_status():
    quote = random.choice(STATUS_QUOTES)
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=quote)
    )

@rotate_status.before_loop
async def before_rotate_status():
    await bot.wait_until_ready()

COGS = [
    "cogs.sectools",
    "cogs.encoding",
    "cogs.ctftime",
    "cogs.secnews",
    "cogs.moderation",
    "cogs.scheduling",
    "cogs.utility",
    "cogs.welcome",
    "cogs.help",
]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            log.info("Loaded cog: %s", cog)
        except Exception as exc:
            log.error("Failed to load cog %s: %s", cog, exc)

@bot.event
async def on_ready():
    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    log.info("Connected to %d guild(s)", len(bot.guilds))
    log.info("Bot is ready!")
    if not rotate_status.is_running():
        rotate_status.start()

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await ctx.send(
            f"You don't have permission to use `{PREFIX}{ctx.command}`. "
            f"Required: **{missing}**."
        )
        return
    if isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await ctx.send(
            f"I'm missing permissions to do that: **{missing}**. "
            f"Please check my role permissions."
        )
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"Missing required argument: `{error.param.name}`.\n"
            f"Run `{PREFIX}help {ctx.command}` to see the full usage."
        )
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(
            f"Invalid argument provided.\n"
            f"Run `{PREFIX}help {ctx.command}` to see the correct usage."
        )
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Command on cooldown. Try again in **{error.retry_after:.1f}s**.")
        return
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("This command can only be used in a server, not in DMs.")
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            f"You don't have the required permissions to use `{PREFIX}{ctx.command}`."
        )
        return
    log.error("Unhandled command error in %s: %s", ctx.command, error, exc_info=error)
    await ctx.send("An unexpected error occurred. Please try again later.")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
