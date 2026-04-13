"""
Security News cog for DayZero Bot.

Fetches cybersecurity news from The Hacker News RSS feed and
posts updates to a configured channel. Data persists via CSV.
"""

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands, tasks

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SECNEWS_CHANNELS_FILE = DATA_DIR / "secnews_channels.csv"
SECNEWS_POSTED_FILE = DATA_DIR / "secnews_posted.csv"

NEWS_FEED = "https://feeds.feedburner.com/TheHackersNews"


def _load_channels() -> dict:
    channels = {}
    if SECNEWS_CHANNELS_FILE.exists():
        with open(SECNEWS_CHANNELS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                channels[int(row["guild_id"])] = int(row["channel_id"])
    return channels


def _save_channels(channels: dict):
    DATA_DIR.mkdir(exist_ok=True)
    with open(SECNEWS_CHANNELS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["guild_id", "channel_id"])
        writer.writeheader()
        for guild_id, channel_id in channels.items():
            writer.writerow({"guild_id": guild_id, "channel_id": channel_id})


def _load_posted() -> set:
    posted = set()
    if SECNEWS_POSTED_FILE.exists():
        with open(SECNEWS_POSTED_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    posted.add(row[0])
    return posted


def _save_posted(posted: set):
    DATA_DIR.mkdir(exist_ok=True)
    recent = list(posted)[-500:]
    with open(SECNEWS_POSTED_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["article_id"])
        for aid in recent:
            writer.writerow([aid])


class SecurityNews(commands.Cog, name="Security News"):
    """Cybersecurity news feed from The Hacker News."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        self.check_news.start()

    async def cog_unload(self):
        self.check_news.cancel()
        if self.session:
            await self.session.close()

    async def _fetch_articles(self, limit: int = 5) -> list:
        articles = []
        try:
            async with self.session.get(NEWS_FEED, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                text = await resp.text()
                root = ET.fromstring(text)

                for item in root.iter("item"):
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    description = item.findtext("description", "")
                    pub_date = item.findtext("pubDate", "")

                    description = re.sub(r"<[^>]+>", "", description).strip()
                    if len(description) > 200:
                        description = description[:200] + "..."

                    articles.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "pub_date": pub_date,
                    })
        except Exception:
            pass

        return articles[:limit]

    @tasks.loop(hours=1)
    async def check_news(self):
        channels = _load_channels()
        if not channels:
            return

        articles = await self._fetch_articles(limit=10)
        if not articles:
            return

        posted = _load_posted()
        new_articles = [a for a in articles if a["link"] not in posted]
        if not new_articles:
            return

        for guild_id, channel_id in channels.items():
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue
            for article in new_articles[:5]:
                embed = discord.Embed(
                    title=article["title"],
                    url=article["link"],
                    description=article["description"],
                    color=0x1ABC9C,
                )
                embed.set_footer(text=f"The Hacker News | {article['pub_date']}")
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        for article in new_articles:
            posted.add(article["link"])
        _save_posted(posted)

    @check_news.before_loop
    async def before_check_news(self):
        await self.bot.wait_until_ready()

    @commands.command(name="setsecnewschannel")
    @commands.has_permissions(manage_guild=True)
    async def set_secnews_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for cybersecurity news updates.

        Usage: .setsecnewschannel #channel
        """
        channels = _load_channels()
        channels[ctx.guild.id] = channel.id
        _save_channels(channels)
        await ctx.send(f"Security news will be posted in {channel.mention}.")

    @commands.command(name="removesecnewschannel")
    @commands.has_permissions(manage_guild=True)
    async def remove_secnews_channel(self, ctx: commands.Context):
        """Stop posting security news in this server.

        Usage: .removesecnewschannel
        """
        channels = _load_channels()
        if ctx.guild.id in channels:
            del channels[ctx.guild.id]
            _save_channels(channels)
            await ctx.send("Security news updates disabled for this server.")
        else:
            await ctx.send("Security news is not configured for this server.")

    @commands.command(name="secnews", aliases=["cybernews", "news"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def latest_news(self, ctx: commands.Context):
        """Show the latest cybersecurity news.

        Usage: .secnews
        """
        articles = await self._fetch_articles(limit=5)
        if not articles:
            await ctx.send("No news articles found (or the feed is unavailable).")
            return

        embed = discord.Embed(title="Latest Cybersecurity News", color=0x1ABC9C)
        for article in articles:
            embed.add_field(
                name=article["title"],
                value=f"[Read more]({article['link']})\n{article['description'][:100]}",
                inline=False,
            )
        embed.set_footer(text="Source: The Hacker News")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityNews(bot))
