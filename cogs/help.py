"""
Custom help command cog for DayZero Bot.

Provides a categorized, embed-based help menu that lists all cogs
and their commands, with detailed per-command help.
"""

import discord
from discord.ext import commands


class HelpCog(commands.Cog, name="Help"):
    """Custom help command with categorized embeds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands"])
    async def help_command(self, ctx: commands.Context, *, command_name: str = None):
        """Show the help menu or details for a specific command.

        Usage: -help [command_name]
        """
        prefix = ctx.prefix

        # Detailed help for a specific command
        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await ctx.send(f"Unknown command: `{command_name}`. Use `{prefix}help` to see all commands.")
                return

            embed = discord.Embed(
                title=f"Command: {prefix}{cmd.qualified_name}",
                description=cmd.help or "No description.",
                color=0x00FF88,
            )
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(f"`{prefix}{a}`" for a in cmd.aliases), inline=False)

            # Show subcommands if it's a group
            if isinstance(cmd, commands.Group):
                subs = ", ".join(f"`{prefix}{cmd.qualified_name} {sub.name}`" for sub in cmd.commands)
                embed.add_field(name="Subcommands", value=subs or "None", inline=False)

            await ctx.send(embed=embed)
            return

        # Full help menu
        embed = discord.Embed(
            title="DayZero Bot — Command Reference",
            description=(
                f"Use `{prefix}help <command>` for detailed info on a command.\n"
                f"Prefix: `{prefix}`"
            ),
            color=0x00FF88,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Category ordering
        category_order = [
            "Cybersecurity",
            "Encoding",
            "Moderation",
            "Scheduling",
            "Utility",
            "Welcome",
            "Help",
        ]

        cogs_listed = set()
        for cog_name in category_order:
            cog = self.bot.get_cog(cog_name)
            if not cog:
                continue
            cogs_listed.add(cog_name)
            cmds = cog.get_commands()
            if not cmds:
                continue

            cmd_list = []
            for cmd in sorted(cmds, key=lambda c: c.name):
                brief = cmd.short_doc or "No description"
                cmd_list.append(f"`{prefix}{cmd.name}` — {brief}")

            embed.add_field(
                name=f"--- {cog_name} ---",
                value="\n".join(cmd_list),
                inline=False,
            )

        # Any cogs not in the predefined order
        for cog_name, cog in self.bot.cogs.items():
            if cog_name in cogs_listed:
                continue
            cmds = cog.get_commands()
            if not cmds:
                continue
            cmd_list = [f"`{prefix}{cmd.name}` — {cmd.short_doc or 'No description'}" for cmd in cmds]
            embed.add_field(name=f"--- {cog_name} ---", value="\n".join(cmd_list), inline=False)

        embed.set_footer(text="DayZero Cybersecurity Club")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
