"""
Authored by: Preston Vardaman
DayZero Cybersecurity Club Discord Bot

A feature-rich Discord bot with cybersecurity tools, moderation,
scheduled announcements, encoding/decoding utilities, and more.
"""

import os
import asyncio
import logging

import discord
from discord.ext import commands
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
    activity=discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help | DayZero"),
)

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

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use that command.")
        return
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have the required permissions to do that.")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`. Use `{PREFIX}help {ctx.command}` for usage info.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument. Use `{PREFIX}help {ctx.command}` for usage info.")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Command on cooldown. Try again in {error.retry_after:.1f}s.")
        return
    log.error("Unhandled command error in %s: %s", ctx.command, error, exc_info=error)
    await ctx.send("An unexpected error occurred. Please try again later.")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
