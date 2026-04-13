"""
Custom help command cog for DayZero Bot.

Provides a categorized, embed-based help menu that lists all cogs
and their commands, with detailed per-command help.
"""

import discord
from discord.ext import commands

CATEGORY_INFO = {
    "Security Tools": {"icon": "🔒", "desc": "Network recon, CVE lookup, hashing, and more"},
    "Encoding": {"icon": "🔤", "desc": "Base64, hex, binary, morse, and cipher tools"},
    "CTFTime": {"icon": "🏁", "desc": "CTF competition tracking from CTFTime.org"},
    "Security News": {"icon": "📰", "desc": "Cybersecurity news from The Hacker News"},
    "Moderation": {"icon": "🛡️", "desc": "Kick, ban, mute, purge, and server management"},
    "Scheduling": {"icon": "📅", "desc": "Announcements, reminders, and recurring messages"},
    "Utility": {"icon": "🔧", "desc": "Server info, polls, dice rolls, and more"},
    "Welcome": {"icon": "👋", "desc": "Member join/leave messages and auto-role"},
}

CATEGORY_ORDER = [
    "Security Tools",
    "Encoding",
    "CTFTime",
    "Security News",
    "Moderation",
    "Scheduling",
    "Utility",
    "Welcome",
]


class HelpCog(commands.Cog, name="Help"):
    """Custom help command with categorized embeds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands"])
    async def help_command(self, ctx: commands.Context, *, command_name: str = None):
        """Show the help menu or details for a specific command.

        Usage: .help [command_name]
        """
        prefix = ctx.prefix

        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await ctx.send(f"Unknown command: `{command_name}`. Use `{prefix}help` to see all commands.")
                return

            embed = discord.Embed(
                title=f"{prefix}{cmd.qualified_name}",
                description=cmd.help or "No description.",
                color=0x00FF88,
            )
            if cmd.aliases:
                embed.add_field(
                    name="Aliases",
                    value=" ".join(f"`{prefix}{a}`" for a in cmd.aliases),
                    inline=False,
                )
            if isinstance(cmd, commands.Group):
                subs = " ".join(f"`{sub.name}`" for sub in cmd.commands)
                embed.add_field(name="Subcommands", value=subs or "None", inline=False)

            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="DayZero Bot",
            description=f"Use `{prefix}help <command>` for details on any command.",
            color=0x00FF88,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        cogs_listed = set()
        for cog_name in CATEGORY_ORDER:
            cog = self.bot.get_cog(cog_name)
            if not cog:
                continue
            cogs_listed.add(cog_name)
            cmds = sorted(cog.get_commands(), key=lambda c: c.name)
            if not cmds:
                continue

            info = CATEGORY_INFO.get(cog_name, {})
            icon = info.get("icon", "")
            desc = info.get("desc", "")

            cmd_list = " ".join(f"`{cmd.name}`" for cmd in cmds)
            header = f"{icon} {cog_name}" if icon else cog_name
            value = f"*{desc}*\n{cmd_list}" if desc else cmd_list

            embed.add_field(name=header, value=value, inline=False)

        for cog_name, cog in self.bot.cogs.items():
            if cog_name in cogs_listed or cog_name == "Help":
                continue
            cmds = cog.get_commands()
            if not cmds:
                continue
            cmd_list = " ".join(f"`{cmd.name}`" for cmd in sorted(cmds, key=lambda c: c.name))
            embed.add_field(name=cog_name, value=cmd_list, inline=False)

        embed.set_footer(text="DayZero Cybersecurity Club")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
