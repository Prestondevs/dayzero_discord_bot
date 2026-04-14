"""
Custom help command cog for DayZero Bot.

Provides a categorized, embed-based help menu that lists all cogs
and their commands, with detailed per-command help.
"""

import discord
from discord.ext import commands

CATEGORY_INFO = {
    "Security Tools": {
        "icon": "🔒",
        "desc": "Network recon, CVE lookup, hashing, and more",
        "commands": {
            "iplookup": "Look up IP/domain geolocation and network info",
            "dns": "Query DNS records (A, AAAA, MX, TXT, NS, etc.)",
            "rdns": "Reverse DNS lookup on an IP address",
            "headers": "Audit HTTP security headers for a URL",
            "cve": "Search for a CVE by ID with CVSS scores",
            "whois": "WHOIS domain registration lookup",
            "hash": "Generate MD5/SHA1/SHA256/SHA512 hashes",
            "password": "Analyze password strength and entropy",
            "subnet": "Calculate subnet info from CIDR notation",
            "port": "Look up common port numbers",
            "portcheck": "Test if a TCP port is open on a host",
        },
    },
    "Encoding": {
        "icon": "🔤",
        "desc": "Base64, hex, binary, morse, and cipher tools",
        "commands": {
            "b64encode": "Encode text to Base64",
            "b64decode": "Decode Base64 to text",
            "hexencode": "Encode text to hex",
            "hexdecode": "Decode hex to text",
            "urlencode": "URL-encode a string",
            "urldecode": "URL-decode a string",
            "rot13": "Apply ROT13",
            "caesar": "Caesar cipher with custom shift",
            "caesarbrute": "Brute-force all 25 Caesar rotations",
            "tobinary": "Text to binary",
            "frombinary": "Binary to text",
            "tomorse": "Text to Morse code",
            "frommorse": "Morse code to text",
            "analyze": "Analyze a string (entropy, encoding detection)",
        },
    },
    "CTFTime": {
        "icon": "🏁",
        "desc": "CTF competition tracking from CTFTime.org",
        "commands": {
            "ctftime": "Show upcoming CTF competitions",
            "setctftimechannel": "Set channel for automatic CTF updates",
            "removectftimechannel": "Disable automatic CTF updates",
        },
    },
    "Security News": {
        "icon": "📰",
        "desc": "Cybersecurity news from The Hacker News",
        "commands": {
            "secnews": "Show latest cybersecurity news",
            "setsecnewschannel": "Set channel for automatic news updates",
            "removesecnewschannel": "Disable automatic news updates",
        },
    },
    "Moderation": {
        "icon": "🛡️",
        "desc": "Server management (admin only)",
        "commands": {
            "kick": "Kick a member",
            "ban": "Ban a member",
            "unban": "Unban a user by ID",
            "mute": "Timeout a member",
            "unmute": "Remove a timeout",
            "purge": "Bulk delete messages",
            "slowmode": "Set channel slowmode",
            "lock": "Lock a channel",
            "unlock": "Unlock a channel",
            "warn": "Warn a member",
            "nick": "Change a member's nickname",
        },
    },
    "Scheduling": {
        "icon": "📅",
        "desc": "Announcements, reminders, and recurring messages",
        "commands": {
            "schedule": "Schedule an announcement to a channel",
            "scheduletitled": "Schedule a titled announcement",
            "recurring": "Set up a recurring announcement",
            "schedules": "List all scheduled announcements",
            "cancelschedule": "Cancel a scheduled announcement",
            "remind": "Set a personal reminder",
            "reminders": "List your pending reminders",
            "cancelreminder": "Cancel a reminder",
        },
    },
    "Utility": {
        "icon": "🔧",
        "desc": "Server info, polls, dice rolls, and more",
        "commands": {
            "ping": "Show bot latency",
            "uptime": "Show bot uptime",
            "botinfo": "Show bot info and stats",
            "serverinfo": "Show server info",
            "userinfo": "Show user info",
            "avatar": "Show a user's avatar",
            "roleinfo": "Show role info and permissions",
            "poll": "Create a poll with options",
            "vote": "Create a quick yes/no vote",
            "coinflip": "Flip a coin",
            "roll": "Roll dice (NdN format)",
            "contribute": "Get the GitHub repo link",
            "embed": "Create a custom embed message",
        },
    },
    "Welcome": {
        "icon": "👋",
        "desc": "Member join/leave messages and auto-role",
        "commands": {
            "welcome": "Configure welcome system (use subcommands)",
        },
    },
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
        if hasattr(check, "__qualname__") and "has_permissions" in check.__qualname__:
            closure = check.__closure__
            if closure:
                for cell in closure:
                    try:
                        val = cell.cell_contents
                        if isinstance(val, dict):
                            perms = [k.replace("_", " ").title() for k, v in val.items() if v]
                            if perms:
                                return ", ".join(perms)
                    except ValueError:
                        continue
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
        Example: .help schedule
        """
        prefix = ctx.prefix

        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await ctx.send(f"Unknown command: `{command_name}`. Use `{prefix}help` to see all commands.")
                return

            embed = discord.Embed(
                title=f"{prefix}{cmd.qualified_name}",
                color=0x00FF88,
            )

            # Parse docstring into sections
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
                    content = stripped.split(":", 1)[1].strip()
                    if content:
                        usage_lines.append(content)
                elif stripped.lower().startswith("example:"):
                    section = "example"
                    content = stripped.split(":", 1)[1].strip()
                    if content:
                        example_lines.append(content)
                elif section == "usage":
                    if stripped.lower().startswith("example:"):
                        section = "example"
                        content = stripped.split(":", 1)[1].strip()
                        if content:
                            example_lines.append(content)
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
                    if stripped:
                        description_lines.append(stripped)

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
                    inline=True,
                )

            perm = _get_permission_label(cmd)
            if perm:
                embed.add_field(name="Requires", value=f"`{perm}`", inline=True)

            if cmd.cog:
                embed.add_field(name="Category", value=cmd.cog.qualified_name, inline=True)

            if isinstance(cmd, commands.Group):
                sub_lines = []
                for sub in sorted(cmd.commands, key=lambda s: s.name):
                    sub_lines.append(f"`{prefix}{cmd.qualified_name} {sub.name}` — {sub.short_doc or 'No description'}")
                embed.add_field(
                    name="Subcommands",
                    value="\n".join(sub_lines) or "None",
                    inline=False,
                )

            embed.set_footer(text=f"Use {prefix}help to see all commands")
            await ctx.send(embed=embed)
            return

        # Full help menu — send multiple embeds for cleaner formatting
        header_embed = discord.Embed(
            title="DayZero Bot — Command Reference",
            description=(
                f"Use `{prefix}help <command>` for detailed info on any command.\n"
                f"`*` = requires **Administrator**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0x00FF88,
        )
        header_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=header_embed)

        for cog_name in CATEGORY_ORDER:
            cog = self.bot.get_cog(cog_name)
            if not cog:
                continue
            cmds = sorted(cog.get_commands(), key=lambda c: c.name)
            if not cmds:
                continue

            info = CATEGORY_INFO.get(cog_name, {})
            icon = info.get("icon", "")
            desc = info.get("desc", "")
            cmd_descriptions = info.get("commands", {})

            embed = discord.Embed(
                title=f"{icon} {cog_name}",
                description=f"*{desc}*" if desc else None,
                color=0x00FF88,
            )

            for cmd in cmds:
                perm = _get_permission_label(cmd)
                admin_tag = " `[Admin]`" if perm and "administrator" in perm.lower() else ""
                brief = cmd_descriptions.get(cmd.name, cmd.short_doc or "No description")
                embed.add_field(
                    name=f"{prefix}{cmd.name}{admin_tag}",
                    value=brief,
                    inline=True,
                )

            await ctx.send(embed=embed)

        footer_embed = discord.Embed(
            description=(
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"**Tip:** `{prefix}help <command>` for usage, examples, and aliases.\n"
                f"**Contribute:** `{prefix}contribute` for the GitHub repo."
            ),
            color=0x00FF88,
        )
        footer_embed.set_footer(text="DayZero Cybersecurity Club")
        await ctx.send(embed=footer_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
