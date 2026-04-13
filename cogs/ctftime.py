"""
CTFTime integration cog for DayZero Bot.

Fetches upcoming CTF competitions from CTFTime and posts
updates to a configured channel. Data persists via CSV.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands, tasks

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CTFTIME_CHANNELS_FILE = DATA_DIR / "ctftime_channels.csv"
CTFTIME_POSTED_FILE = DATA_DIR / "ctftime_posted.csv"


def _load_channels() -> dict:
    channels = {}
    if CTFTIME_CHANNELS_FILE.exists():
        with open(CTFTIME_CHANNELS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                channels[int(row["guild_id"])] = int(row["channel_id"])
    return channels


def _save_channels(channels: dict):
    DATA_DIR.mkdir(exist_ok=True)
    with open(CTFTIME_CHANNELS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["guild_id", "channel_id"])
        writer.writeheader()
        for guild_id, channel_id in channels.items():
            writer.writerow({"guild_id": guild_id, "channel_id": channel_id})


def _load_posted() -> set:
    posted = set()
    if CTFTIME_POSTED_FILE.exists():
        with open(CTFTIME_POSTED_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    posted.add(row[0])
    return posted


def _save_posted(posted: set):
    DATA_DIR.mkdir(exist_ok=True)
    recent = list(posted)[-500:]
    with open(CTFTIME_POSTED_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["event_id"])
        for eid in recent:
            writer.writerow([eid])


class CTFTime(commands.Cog, name="CTFTime"):
    """CTFTime competition tracking and updates."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "DayZeroBot/1.0"}
        )
        self.check_ctftime.start()

    async def cog_unload(self):
        self.check_ctftime.cancel()
        if self.session:
            await self.session.close()

    async def _fetch_upcoming(self, limit: int = 5) -> list:
        now = int(datetime.now(timezone.utc).timestamp())
        finish = now + 7 * 86400
        url = f"https://ctftime.org/api/v1/events/?limit={limit}&start={now}&finish={finish}"
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return []

    @tasks.loop(hours=1)
    async def check_ctftime(self):
        channels = _load_channels()
        if not channels:
            return

        events = await self._fetch_upcoming(limit=10)
        if not events:
            return

        posted = _load_posted()
        new_events = [e for e in events if str(e.get("id")) not in posted]
        if not new_events:
            return

        for guild_id, channel_id in channels.items():
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue
            for event in new_events:
                embed = self._event_embed(event)
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        for event in new_events:
            posted.add(str(event["id"]))
        _save_posted(posted)

    @check_ctftime.before_loop
    async def before_check_ctftime(self):
        await self.bot.wait_until_ready()

    @staticmethod
    def _event_embed(event: dict) -> discord.Embed:
        title = event.get("title", "Unknown CTF")
        url = event.get("url") or event.get("ctftime_url", "")
        description = event.get("description", "")
        if len(description) > 300:
            description = description[:300] + "..."

        start = event.get("start", "")
        finish = event.get("finish", "")
        format_type = event.get("format", "")
        weight = event.get("weight", 0)
        participants = event.get("participants", 0)
        ctftime_url = event.get("ctftime_url", "")

        embed = discord.Embed(
            title=title,
            url=ctftime_url or url,
            description=description or "No description available.",
            color=0xE74C3C,
        )

        if start:
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                embed.add_field(name="Start", value=f"<t:{int(start_dt.timestamp())}:F>")
            except ValueError:
                embed.add_field(name="Start", value=start)
        if finish:
            try:
                finish_dt = datetime.fromisoformat(finish.replace("Z", "+00:00"))
                embed.add_field(name="End", value=f"<t:{int(finish_dt.timestamp())}:F>")
            except ValueError:
                embed.add_field(name="End", value=finish)

        if format_type:
            embed.add_field(name="Format", value=format_type)
        if weight:
            embed.add_field(name="Weight", value=f"{weight:.2f}")
        if participants:
            embed.add_field(name="Teams", value=str(participants))
        if url:
            embed.add_field(name="Website", value=f"[Link]({url})", inline=False)

        logo = event.get("logo", "")
        if logo:
            embed.set_thumbnail(url=logo)

        embed.set_footer(text="CTFTime")
        return embed

    @commands.command(name="setctftimechannel")
    @commands.has_permissions(administrator=True)
    async def set_ctftime_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for CTFTime competition updates.

        Usage: .setctftimechannel #channel
        """
        channels = _load_channels()
        channels[ctx.guild.id] = channel.id
        _save_channels(channels)
        await ctx.send(f"CTFTime updates will be posted in {channel.mention}.")

    @commands.command(name="removectftimechannel")
    @commands.has_permissions(administrator=True)
    async def remove_ctftime_channel(self, ctx: commands.Context):
        """Stop posting CTFTime updates in this server.

        Usage: .removectftimechannel
        """
        channels = _load_channels()
        if ctx.guild.id in channels:
            del channels[ctx.guild.id]
            _save_channels(channels)
            await ctx.send("CTFTime updates disabled for this server.")
        else:
            await ctx.send("CTFTime updates are not configured for this server.")

    @commands.command(name="ctftime", aliases=["ctf", "ctfs"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def upcoming_ctfs(self, ctx: commands.Context):
        """Show upcoming CTF competitions from CTFTime.

        Usage: .ctftime
        """
        events = await self._fetch_upcoming(limit=5)
        if not events:
            await ctx.send("No upcoming CTF events found (or CTFTime API is unavailable).")
            return

        embed = discord.Embed(title="Upcoming CTF Competitions", color=0xE74C3C)
        for event in events:
            title = event.get("title", "Unknown")
            ctftime_url = event.get("ctftime_url", "")
            start = event.get("start", "")
            format_type = event.get("format", "N/A")

            time_str = ""
            if start:
                try:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    time_str = f"<t:{int(start_dt.timestamp())}:R>"
                except ValueError:
                    time_str = start

            link = f"[{title}]({ctftime_url})" if ctftime_url else title
            embed.add_field(
                name=title,
                value=f"{link}\n{time_str} | {format_type}",
                inline=False,
            )

        embed.set_footer(text="Data from CTFTime.org")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CTFTime(bot))
