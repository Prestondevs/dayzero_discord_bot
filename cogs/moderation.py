"""
Moderation cog for DayZero Bot.

Provides kick, ban, unban, mute, unmute, purge, slowmode,
channel lock/unlock, and an audit-log style mod-log.
"""

import datetime

import discord
from discord.ext import commands
class Moderation(commands.Cog, name="Moderation"):
    """Server moderation commands (requires appropriate permissions)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server.

        Usage: -kick @user [reason]
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick someone with an equal or higher role.")
            return
        await member.kick(reason=f"{ctx.author}: {reason}")
        embed = discord.Embed(title="Member Kicked", color=0xE74C3C)
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=str(ctx.author))
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server.

        Usage: -ban @user [reason]
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with an equal or higher role.")
            return
        await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=0)
        embed = discord.Embed(title="Member Banned", color=0xE74C3C)
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=str(ctx.author))
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int):
        """Unban a user by their ID.

        Usage: -unban <user_id>
        """
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"Unbanned **{user}** ({user.id}).")
        except discord.NotFound:
            await ctx.send("That user is not banned or does not exist.")

    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int = 10, *, reason: str = "No reason provided"):
        """Timeout a member for a specified number of minutes.

        Usage: -mute @user [minutes] [reason]
        Default: 10 minutes. Max: 40320 (28 days).
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot mute someone with an equal or higher role.")
            return
        if duration < 1 or duration > 40320:
            await ctx.send("Duration must be between 1 and 40320 minutes (28 days).")
            return
        until = discord.utils.utcnow() + datetime.timedelta(minutes=duration)
        await member.timeout(until, reason=f"{ctx.author}: {reason}")
        embed = discord.Embed(title="Member Muted", color=0xF39C12)
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.add_field(name="Duration", value=f"{duration} minutes")
        embed.add_field(name="Moderator", value=str(ctx.author))
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """Remove a timeout from a member.

        Usage: -unmute @user
        """
        await member.timeout(None)
        await ctx.send(f"Removed timeout from **{member}**.")

    @commands.command(name="purge", aliases=["clear", "prune"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int, member: discord.Member = None):
        """Delete messages from the channel.

        Usage: -purge <amount> [@user]
        If a user is specified, only their messages are deleted.
        Max: 200 messages.
        """
        if amount < 1 or amount > 200:
            await ctx.send("Amount must be between 1 and 200.")
            return

        def check(msg):
            if member:
                return msg.author == member
            return True

        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount, check=check)
        msg = await ctx.send(f"Deleted {len(deleted)} message(s).")
        await msg.delete(delay=3)

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int = 0):
        """Set slowmode delay for the current channel.

        Usage: -slowmode [seconds]
        Set to 0 to disable. Max: 21600 (6 hours).
        """
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode must be between 0 and 21600 seconds.")
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("Slowmode disabled.")
        else:
            await ctx.send(f"Slowmode set to **{seconds}** seconds.")

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def lock_channel(self, ctx: commands.Context):
        """Lock the current channel (prevent @everyone from sending messages).

        Usage: -lock
        """
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("This channel has been locked.")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unlock_channel(self, ctx: commands.Context):
        """Unlock the current channel.

        Usage: -unlock
        """
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("This channel has been unlocked.")

    @commands.command(name="warn")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Issue a warning to a member (logged in chat).

        Usage: -warn @user [reason]
        """
        embed = discord.Embed(title="Member Warned", color=0xF1C40F)
        embed.add_field(name="User", value=f"{member.mention} ({member.id})")
        embed.add_field(name="Moderator", value=str(ctx.author))
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)
        # Try to DM the user
        try:
            await member.send(
                f"You have been warned in **{ctx.guild.name}** for: {reason}"
            )
        except discord.Forbidden:
            pass

    @commands.command(name="nick", aliases=["nickname"])
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def change_nick(self, ctx: commands.Context, member: discord.Member, *, nickname: str = None):
        """Change a member's nickname (omit nickname to reset).

        Usage: -nick @user [new_nickname]
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot change the nickname of someone with an equal or higher role.")
            return
        await member.edit(nick=nickname)
        if nickname:
            await ctx.send(f"Changed **{member}**'s nickname to **{nickname}**.")
        else:
            await ctx.send(f"Reset **{member}**'s nickname.")
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
