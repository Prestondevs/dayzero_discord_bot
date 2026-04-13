"""
Scheduling cog for DayZero Bot.

Provides scheduled announcements with channel targeting, one-off reminders,
and recurring messages. Schedules persist across restarts via CSV.
"""

import asyncio
import csv
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord.ext import commands, tasks

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCHEDULES_FILE = DATA_DIR / "schedules.csv"
REMINDERS_FILE = DATA_DIR / "reminders.json"

SCHEDULE_FIELDS = [
    "id", "channel_id", "guild_id", "author", "author_id",
    "title", "message", "fire_at", "recurring", "created_at",
]


def _load_schedules() -> list[dict]:
    if SCHEDULES_FILE.exists():
        with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return []


def _save_schedules(schedules: list[dict]):
    DATA_DIR.mkdir(exist_ok=True)
    with open(SCHEDULES_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEDULE_FIELDS)
        writer.writeheader()
        for s in schedules:
            writer.writerow({k: s.get(k, "") for k in SCHEDULE_FIELDS})


def _load_json(path: Path) -> list:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_json(path: Path, data: list):
    DATA_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _parse_duration(text: str) -> timedelta | None:
    """Parse a human-friendly duration like '2h30m', '45m', '1d', '90s'."""
    total_seconds = 0
    pattern = re.compile(r"(\d+)\s*([dhms])", re.IGNORECASE)
    matches = pattern.findall(text)
    if not matches:
        return None
    for value, unit in matches:
        value = int(value)
        if unit.lower() == "d":
            total_seconds += value * 86400
        elif unit.lower() == "h":
            total_seconds += value * 3600
        elif unit.lower() == "m":
            total_seconds += value * 60
        elif unit.lower() == "s":
            total_seconds += value
    return timedelta(seconds=total_seconds) if total_seconds > 0 else None


class Scheduling(commands.Cog, name="Scheduling"):
    """Schedule announcements, reminders, and recurring messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.check_schedules.start()
        self.check_reminders.start()

    async def cog_unload(self):
        self.check_schedules.cancel()
        self.check_reminders.cancel()

    @tasks.loop(seconds=30)
    async def check_schedules(self):
        schedules = _load_schedules()
        now = datetime.now(timezone.utc)
        remaining = []
        for sched in schedules:
            fire_at = datetime.fromisoformat(sched["fire_at"])
            if now >= fire_at:
                channel = self.bot.get_channel(int(sched["channel_id"]))
                if channel:
                    embed = discord.Embed(
                        title=sched.get("title") or "Scheduled Announcement",
                        description=sched["message"],
                        color=0x3498DB,
                    )
                    embed.set_footer(text=f"Scheduled by {sched['author']}")
                    try:
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        pass

                if sched.get("recurring"):
                    delta = _parse_duration(sched["recurring"])
                    if delta:
                        sched["fire_at"] = (fire_at + delta).isoformat()
                        remaining.append(sched)
            else:
                remaining.append(sched)

        if len(remaining) != len(schedules):
            _save_schedules(remaining)

    @check_schedules.before_loop
    async def before_check_schedules(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=15)
    async def check_reminders(self):
        reminders = _load_json(REMINDERS_FILE)
        now = datetime.now(timezone.utc)
        remaining = []
        for rem in reminders:
            fire_at = datetime.fromisoformat(rem["fire_at"])
            if now >= fire_at:
                channel = self.bot.get_channel(rem["channel_id"])
                if channel:
                    try:
                        await channel.send(
                            f"<@{rem['user_id']}> **Reminder:** {rem['message']}"
                        )
                    except discord.Forbidden:
                        pass
            else:
                remaining.append(rem)

        if len(remaining) != len(reminders):
            _save_json(REMINDERS_FILE, remaining)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @commands.command(name="schedule", aliases=["announce"])
    @commands.has_permissions(administrator=True)
    async def schedule_announcement(self, ctx: commands.Context, delay: str, channel: discord.TextChannel, *, message: str):
        """Schedule an announcement to be sent in a specific channel after a delay.

        Usage: .schedule <delay> <#channel> <message>
        Delay format: 30m, 2h, 1d, 1h30m, etc.

        Example: .schedule 2h #announcements Server maintenance in 2 hours!
        Example: .schedule 1d #general Tomorrow's meeting is cancelled.
        """
        delta = _parse_duration(delay)
        if not delta:
            await ctx.send(
                "Invalid duration format. Use a combination of:\n"
                "- `s` for seconds, `m` for minutes, `h` for hours, `d` for days\n"
                "- Examples: `30m`, `2h`, `1d`, `1h30m`\n"
                f"Run `{ctx.prefix}help schedule` for full usage."
            )
            return

        fire_at = datetime.now(timezone.utc) + delta
        sched_id = str(uuid.uuid4())[:8]

        schedules = _load_schedules()
        schedules.append({
            "id": sched_id,
            "channel_id": str(channel.id),
            "guild_id": str(ctx.guild.id),
            "author": str(ctx.author),
            "author_id": str(ctx.author.id),
            "message": message,
            "title": "Announcement",
            "fire_at": fire_at.isoformat(),
            "recurring": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        _save_schedules(schedules)

        embed = discord.Embed(title="Announcement Scheduled", color=0x2ECC71)
        embed.add_field(name="ID", value=f"`{sched_id}`")
        embed.add_field(name="Channel", value=channel.mention)
        embed.add_field(name="Fires At", value=f"<t:{int(fire_at.timestamp())}:F>")
        embed.add_field(name="Message", value=message[:200], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="scheduletitled", aliases=["announcetitled"])
    @commands.has_permissions(administrator=True)
    async def schedule_titled(self, ctx: commands.Context, delay: str, channel: discord.TextChannel, title: str, *, message: str):
        """Schedule an announcement with a custom title in a specific channel.

        Usage: .scheduletitled <delay> <#channel> "<title>" <message>
        Example: .scheduletitled 1h #general "Maintenance" Servers going down at midnight.
        Example: .scheduletitled 30m #announcements "CTF Reminder" Don't forget to register!
        """
        delta = _parse_duration(delay)
        if not delta:
            await ctx.send(
                "Invalid duration format. Use a combination of:\n"
                "- `s` for seconds, `m` for minutes, `h` for hours, `d` for days\n"
                f"Run `{ctx.prefix}help scheduletitled` for full usage."
            )
            return

        fire_at = datetime.now(timezone.utc) + delta
        sched_id = str(uuid.uuid4())[:8]

        schedules = _load_schedules()
        schedules.append({
            "id": sched_id,
            "channel_id": str(channel.id),
            "guild_id": str(ctx.guild.id),
            "author": str(ctx.author),
            "author_id": str(ctx.author.id),
            "message": message,
            "title": title,
            "fire_at": fire_at.isoformat(),
            "recurring": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        _save_schedules(schedules)

        embed = discord.Embed(title="Announcement Scheduled", color=0x2ECC71)
        embed.add_field(name="ID", value=f"`{sched_id}`")
        embed.add_field(name="Title", value=title)
        embed.add_field(name="Channel", value=channel.mention)
        embed.add_field(name="Fires At", value=f"<t:{int(fire_at.timestamp())}:F>")
        embed.add_field(name="Message", value=message[:200], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="recurring", aliases=["repeat"])
    @commands.has_permissions(administrator=True)
    async def recurring_announcement(self, ctx: commands.Context, interval: str, channel: discord.TextChannel, *, message: str):
        """Schedule a recurring announcement in a specific channel.

        Usage: .recurring <interval> <#channel> <message>
        Interval format: 1h, 6h, 1d, 12h, etc.
        First delivery happens after one interval. Minimum: 10 minutes.

        Example: .recurring 24h #ctf-updates Don't forget to check the CTF scoreboard!
        Example: .recurring 12h #general Good morning / Good evening!
        """
        delta = _parse_duration(interval)
        if not delta:
            await ctx.send(
                "Invalid interval format. Use a combination of:\n"
                "- `s` for seconds, `m` for minutes, `h` for hours, `d` for days\n"
                f"Run `{ctx.prefix}help recurring` for full usage."
            )
            return
        if delta < timedelta(minutes=10):
            await ctx.send("Minimum recurring interval is 10 minutes.")
            return

        fire_at = datetime.now(timezone.utc) + delta
        sched_id = str(uuid.uuid4())[:8]

        schedules = _load_schedules()
        schedules.append({
            "id": sched_id,
            "channel_id": str(channel.id),
            "guild_id": str(ctx.guild.id),
            "author": str(ctx.author),
            "author_id": str(ctx.author.id),
            "message": message,
            "title": "Recurring Announcement",
            "fire_at": fire_at.isoformat(),
            "recurring": interval,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        _save_schedules(schedules)

        embed = discord.Embed(title="Recurring Announcement Scheduled", color=0x9B59B6)
        embed.add_field(name="ID", value=f"`{sched_id}`")
        embed.add_field(name="Channel", value=channel.mention)
        embed.add_field(name="Interval", value=interval)
        embed.add_field(name="Next Fire", value=f"<t:{int(fire_at.timestamp())}:F>")
        embed.add_field(name="Message", value=message[:200], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="schedules", aliases=["listschedules", "scheduled"])
    @commands.has_permissions(administrator=True)
    async def list_schedules(self, ctx: commands.Context):
        """List all scheduled announcements for this server.

        Usage: .schedules
        """
        schedules = _load_schedules()
        guild_schedules = [s for s in schedules if s.get("guild_id") == str(ctx.guild.id)]

        if not guild_schedules:
            await ctx.send("No scheduled announcements.")
            return

        embed = discord.Embed(title="Scheduled Announcements", color=0x3498DB)
        for s in guild_schedules[:20]:
            fire_at = datetime.fromisoformat(s["fire_at"])
            recurring = f" (every {s['recurring']})" if s.get("recurring") else ""
            embed.add_field(
                name=f"`{s['id']}` — {s.get('title') or 'Announcement'}{recurring}",
                value=f"<t:{int(fire_at.timestamp())}:R> in <#{s['channel_id']}>\n{s['message'][:100]}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="cancelschedule", aliases=["unschedule", "rmschedule"])
    @commands.has_permissions(administrator=True)
    async def cancel_schedule(self, ctx: commands.Context, schedule_id: str):
        """Cancel a scheduled announcement by its ID.

        Usage: .cancelschedule <id>
        """
        schedules = _load_schedules()
        new_schedules = [s for s in schedules if s["id"] != schedule_id]
        if len(new_schedules) == len(schedules):
            await ctx.send(f"No schedule found with ID `{schedule_id}`.")
            return
        _save_schedules(new_schedules)
        await ctx.send(f"Cancelled schedule `{schedule_id}`.")

    @commands.command(name="remind", aliases=["remindme", "reminder"])
    async def set_reminder(self, ctx: commands.Context, delay: str, *, message: str):
        """Set a personal reminder. The bot will ping you when the time is up.

        Usage: .remind <delay> <message>
        Example: .remind 30m Check on the CTF challenge
        Example: .remind 2h Submit the writeup
        """
        delta = _parse_duration(delay)
        if not delta:
            await ctx.send(
                "Invalid duration format. Use a combination of:\n"
                "- `s` for seconds, `m` for minutes, `h` for hours, `d` for days\n"
                f"Run `{ctx.prefix}help remind` for full usage."
            )
            return

        fire_at = datetime.now(timezone.utc) + delta
        rem_id = str(uuid.uuid4())[:8]

        reminders = _load_json(REMINDERS_FILE)
        reminders.append({
            "id": rem_id,
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "message": message,
            "fire_at": fire_at.isoformat(),
        })
        _save_json(REMINDERS_FILE, reminders)

        await ctx.send(f"Reminder set! I'll ping you <t:{int(fire_at.timestamp())}:R>. (ID: `{rem_id}`)")

    @commands.command(name="reminders", aliases=["myreminders"])
    async def list_reminders(self, ctx: commands.Context):
        """List your pending reminders.

        Usage: .reminders
        """
        reminders = _load_json(REMINDERS_FILE)
        mine = [r for r in reminders if r["user_id"] == ctx.author.id]

        if not mine:
            await ctx.send("You have no pending reminders.")
            return

        embed = discord.Embed(title="Your Reminders", color=0xF39C12)
        for r in mine[:15]:
            fire_at = datetime.fromisoformat(r["fire_at"])
            embed.add_field(
                name=f"`{r['id']}` — <t:{int(fire_at.timestamp())}:R>",
                value=r["message"][:100],
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="cancelreminder", aliases=["rmreminder"])
    async def cancel_reminder(self, ctx: commands.Context, reminder_id: str):
        """Cancel a personal reminder by its ID.

        Usage: .cancelreminder <id>
        """
        reminders = _load_json(REMINDERS_FILE)
        new_reminders = [r for r in reminders if not (r["id"] == reminder_id and r["user_id"] == ctx.author.id)]
        if len(new_reminders) == len(reminders):
            await ctx.send(f"No reminder found with ID `{reminder_id}` (or it's not yours).")
            return
        _save_json(REMINDERS_FILE, new_reminders)
        await ctx.send(f"Cancelled reminder `{reminder_id}`.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Scheduling(bot))
