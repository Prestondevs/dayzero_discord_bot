"""
Welcome cog for DayZero Bot.

Handles member join/leave messages, auto-role assignment,
and configurable welcome channels.
"""

import json
from pathlib import Path

import discord
from discord.ext import commands

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WELCOME_CONFIG_FILE = DATA_DIR / "welcome_config.json"
def _load_config() -> dict:
    if WELCOME_CONFIG_FILE.exists():
        with open(WELCOME_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
def _save_config(data: dict):
    DATA_DIR.mkdir(exist_ok=True)
    with open(WELCOME_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
def _guild_config(guild_id: int) -> dict:
    config = _load_config()
    return config.get(str(guild_id), {})
def _set_guild_config(guild_id: int, key: str, value):
    config = _load_config()
    gid = str(guild_id)
    if gid not in config:
        config[gid] = {}
    config[gid][key] = value
    _save_config(config)
class Welcome(commands.Cog, name="Welcome"):
    """Member join/leave messages and auto-role configuration."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        gc = _guild_config(member.guild.id)

        # Auto-role
        auto_role_id = gc.get("auto_role")
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except discord.Forbidden:
                    pass

        # Welcome message
        channel_id = gc.get("welcome_channel")
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                welcome_msg = gc.get(
                    "welcome_message",
                    "Welcome to **{server}**, {mention}! Check out the info channels to get started.",
                )
                formatted = welcome_msg.format(
                    mention=member.mention,
                    user=str(member),
                    server=member.guild.name,
                    member_count=member.guild.member_count,
                )
                embed = discord.Embed(description=formatted, color=0x2ECC71)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{member.guild.member_count}")
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        # DM the new member
        if gc.get("dm_on_join", True):
            try:
                await member.create_dm()
                await member.dm_channel.send(
                    f"Hi {member.name}, welcome to **{member.guild.name}**! "
                    f"Consider checking out the info channels to get started."
                )
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        gc = _guild_config(member.guild.id)
        channel_id = gc.get("leave_channel") or gc.get("welcome_channel")
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    description=f"**{member}** has left the server.",
                    color=0xE74C3C,
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    @commands.group(name="welcome", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def welcome_group(self, ctx: commands.Context):
        """Configure welcome/leave messages. Use subcommands.

        Usage: -welcome <subcommand>
        Subcommands: channel, leavechannel, message, autorole, dm, status
        """
        await ctx.send_help(ctx.command)

    @welcome_group.command(name="channel")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for welcome messages.

        Usage: -welcome channel #channel
        """
        _set_guild_config(ctx.guild.id, "welcome_channel", channel.id)
        await ctx.send(f"Welcome channel set to {channel.mention}.")

    @welcome_group.command(name="leavechannel")
    @commands.has_permissions(administrator=True)
    async def set_leave_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set a separate channel for leave messages (defaults to welcome channel).

        Usage: -welcome leavechannel #channel
        """
        _set_guild_config(ctx.guild.id, "leave_channel", channel.id)
        await ctx.send(f"Leave channel set to {channel.mention}.")

    @welcome_group.command(name="message")
    @commands.has_permissions(administrator=True)
    async def set_welcome_message(self, ctx: commands.Context, *, message: str):
        """Set a custom welcome message.

        Placeholders: {mention}, {user}, {server}, {member_count}
        Usage: -welcome message Welcome {mention} to {server}! You are member #{member_count}.
        """
        _set_guild_config(ctx.guild.id, "welcome_message", message)
        await ctx.send(f"Welcome message updated.\nPreview: {message}")

    @welcome_group.command(name="autorole")
    @commands.has_permissions(administrator=True)
    async def set_auto_role(self, ctx: commands.Context, role: discord.Role = None):
        """Set a role to auto-assign to new members (omit role to disable).

        Usage: -welcome autorole @role
        """
        _set_guild_config(ctx.guild.id, "auto_role", role.id if role else None)
        if role:
            await ctx.send(f"Auto-role set to **{role.name}**.")
        else:
            await ctx.send("Auto-role disabled.")

    @welcome_group.command(name="dm")
    @commands.has_permissions(administrator=True)
    async def toggle_dm(self, ctx: commands.Context, enabled: bool):
        """Enable or disable DM on join.

        Usage: -welcome dm true/false
        """
        _set_guild_config(ctx.guild.id, "dm_on_join", enabled)
        await ctx.send(f"DM on join: **{'enabled' if enabled else 'disabled'}**.")

    @welcome_group.command(name="status")
    @commands.has_permissions(administrator=True)
    async def welcome_status(self, ctx: commands.Context):
        """Show current welcome configuration.

        Usage: -welcome status
        """
        gc = _guild_config(ctx.guild.id)
        embed = discord.Embed(title="Welcome Configuration", color=0x2ECC71)

        wc = gc.get("welcome_channel")
        embed.add_field(name="Welcome Channel", value=f"<#{wc}>" if wc else "Not set")

        lc = gc.get("leave_channel")
        embed.add_field(name="Leave Channel", value=f"<#{lc}>" if lc else "Same as welcome")

        ar = gc.get("auto_role")
        if ar:
            role = ctx.guild.get_role(ar)
            embed.add_field(name="Auto-Role", value=role.mention if role else f"ID {ar} (deleted?)")
        else:
            embed.add_field(name="Auto-Role", value="Disabled")

        embed.add_field(name="DM on Join", value="Yes" if gc.get("dm_on_join", True) else "No")
        embed.add_field(
            name="Welcome Message",
            value=gc.get("welcome_message", "(default)"),
            inline=False,
        )
        await ctx.send(embed=embed)
async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
