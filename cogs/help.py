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


def _get_permission_label(cmd: commands.Command) -> str | None:
    """Extract the required user permission from a command's checks."""
    for check in cmd.checks:
        closure = getattr(check, "__closure__", None)
        if not closure:
            continue
        for cell in closure:
            try:
                val = cell.cell_contents
            except ValueError:
                continue
            # Look for a discord.Permissions object (newer discord.py)
            if isinstance(val, discord.Permissions):
                perms = [p.replace("_", " ").title() for p, v in val if v]
                if perms:
                    return ", ".join(perms)
            # Look for a raw dict (older discord.py)
            if isinstance(val, dict):
                perms = [k.replace("_", " ").title() for k, v in val.items() if v]
                if perms:
                    return ", ".join(perms)
    return None


class HelpCog(commands.Cog, name="Help"):
    """Custom help command with categorized embeds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands"])
    async def help_command(self, ctx: commands.Context, *, command_name: str = None):
        """Show the help menu or details for a specific command.

        Usage: .help [command_name]
        Example: .help kick
        """
        prefix = ctx.prefix

        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await ctx.send(f"Unknown command: `{command_name}`. Use `{prefix}help` to see all commands.")
                return

            # Build detailed help embed
            embed = discord.Embed(
                title=f"{prefix}{cmd.qualified_name}",
                color=0x00FF88,
            )

            # Split docstring into description and fields
            doc = cmd.help or "No description available."
            lines = doc.strip().split("\n")

            description_lines = []
            usage_lines = []
            example_lines = []

            section = "desc"
            for line in lines:
                stripped = line.strip()
                if stripped.lower().startswith("usage:"):
                    section = "usage"
                    usage_lines.append(stripped.replace("Usage:", "").replace("usage:", "").strip())
                elif stripped.lower().startswith("example:"):
                    section = "example"
                    example_lines.append(stripped.replace("Example:", "").replace("example:", "").strip())
                elif section == "usage":
                    if stripped.lower().startswith("example:"):
                        section = "example"
                        example_lines.append(stripped.replace("Example:", "").replace("example:", "").strip())
                    elif stripped:
                        usage_lines.append(stripped)
                    else:
                        section = "desc"
                elif section == "example":
                    if stripped:
                        example_lines.append(stripped)
                    else:
                        section = "desc"
                else:
                    description_lines.append(stripped)

            # Clean up description
            desc_text = "\n".join(description_lines).strip()
            if desc_text:
                embed.description = desc_text

            if usage_lines:
                embed.add_field(
                    name="Usage",
                    value="\n".join(f"`{u}`" for u in usage_lines),
                    inline=False,
                )

            if example_lines:
                embed.add_field(
                    name="Examples",
                    value="\n".join(f"`{e}`" for e in example_lines),
                    inline=False,
                )

            if cmd.aliases:
                embed.add_field(
                    name="Aliases",
                    value=" ".join(f"`{prefix}{a}`" for a in cmd.aliases),
                    inline=False,
                )

            # Permission info
            perm = _get_permission_label(cmd)
            if perm:
                embed.add_field(name="Requires", value=f"`{perm}`", inline=False)

            # Category
            if cmd.cog:
                embed.add_field(name="Category", value=cmd.cog.qualified_name, inline=True)

            if isinstance(cmd, commands.Group):
                subs = " ".join(f"`{sub.name}`" for sub in cmd.commands)
                embed.add_field(name="Subcommands", value=subs or "None", inline=False)

            embed.set_footer(text=f"Use {prefix}help to see all commands")
            await ctx.send(embed=embed)
            return

        # Full help menu
        embed = discord.Embed(
            title="DayZero Bot",
            description=(
                f"Use `{prefix}help <command>` for detailed info on any command.\n"
                f"Commands marked with `*` require **Administrator**."
            ),
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

            cmd_entries = []
            for cmd in cmds:
                perm = _get_permission_label(cmd)
                marker = "*" if perm and "administrator" in perm.lower() else ""
                cmd_entries.append(f"`{cmd.name}`{marker}")

            cmd_list = " ".join(cmd_entries)
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
