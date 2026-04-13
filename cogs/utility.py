"""
Utility cog for DayZero Bot.

Provides server info, user info, avatar, poll creation, ping,
uptime, role info, emoji list, and a coin flip / dice roll.
"""

import platform
import random
import time

import discord
from discord.ext import commands


class Utility(commands.Cog, name="Utility"):
    """General-purpose utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Show the bot's latency.

        Usage: .ping
        """
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! `{latency}ms`")

    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        """Show how long the bot has been running.

        Usage: .uptime
        """
        elapsed = int(time.time() - self.start_time)
        days, remainder = divmod(elapsed, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        await ctx.send(f"Uptime: **{' '.join(parts)}**")

    @commands.command(name="botinfo", aliases=["about"])
    async def bot_info(self, ctx: commands.Context):
        """Show information about the bot.

        Usage: .botinfo
        """
        embed = discord.Embed(
            title="DayZero Bot",
            description="A cybersecurity-focused Discord bot for the DayZero Cybersecurity Club.",
            color=0x00FF88,
        )
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Users", value=str(sum(g.member_count or 0 for g in self.bot.guilds)))
        embed.add_field(name="Commands", value=str(len(self.bot.commands)))
        embed.add_field(name="Python", value=platform.python_version())
        embed.add_field(name="discord.py", value=discord.__version__)
        elapsed = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed, 3600)
        minutes, _ = divmod(remainder, 60)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["server", "guild"])
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context):
        """Display information about the current server.

        Usage: .serverinfo
        """
        g = ctx.guild
        embed = discord.Embed(title=g.name, color=0x3498DB)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner", value=str(g.owner))
        embed.add_field(name="ID", value=str(g.id))
        embed.add_field(name="Created", value=f"<t:{int(g.created_at.timestamp())}:R>")
        embed.add_field(name="Members", value=str(g.member_count))
        embed.add_field(name="Roles", value=str(len(g.roles)))
        embed.add_field(name="Channels", value=f"{len(g.text_channels)} text / {len(g.voice_channels)} voice")
        embed.add_field(name="Boost Level", value=str(g.premium_tier))
        embed.add_field(name="Boosts", value=str(g.premium_subscription_count))
        embed.add_field(name="Emojis", value=f"{len(g.emojis)}/{g.emoji_limit}")
        if g.banner:
            embed.set_image(url=g.banner.url)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["user"])
    @commands.guild_only()
    async def user_info(self, ctx: commands.Context, member: discord.Member = None):
        """Display information about a user (defaults to yourself).

        Usage: .userinfo [@user]
        """
        member = member or ctx.author
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]

        embed = discord.Embed(title=str(member), color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=str(member.id))
        embed.add_field(name="Nickname", value=member.nick or "None")
        embed.add_field(name="Bot", value="Yes" if member.bot else "No")
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>")
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown")
        embed.add_field(name="Top Role", value=member.top_role.mention)
        embed.add_field(
            name=f"Roles ({len(roles)})",
            value=" ".join(roles[:20]) if roles else "None",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """Show a user's avatar in full size.

        Usage: .avatar [@user]
        """
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=member.color)
        embed.set_image(url=member.display_avatar.with_size(1024).url)
        await ctx.send(embed=embed)

    @commands.command(name="roleinfo", aliases=["role"])
    @commands.guild_only()
    async def role_info(self, ctx: commands.Context, *, role: discord.Role):
        """Show information about a role.

        Usage: .roleinfo <role_name>
        """
        embed = discord.Embed(title=f"Role: {role.name}", color=role.color)
        embed.add_field(name="ID", value=str(role.id))
        embed.add_field(name="Color", value=str(role.color))
        embed.add_field(name="Position", value=str(role.position))
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No")
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No")
        embed.add_field(name="Members", value=str(len(role.members)))
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>")
        perms = ", ".join(p[0].replace("_", " ").title() for p in role.permissions if p[1]) or "None"
        if len(perms) > 1024:
            perms = perms[:1020] + "..."
        embed.add_field(name="Permissions", value=perms, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="poll")
    async def create_poll(self, ctx: commands.Context, question: str, *options: str):
        """Create a poll with up to 10 options.

        Usage: .poll "Question?" "Option 1" "Option 2" ...
        If no options given, creates a Yes/No poll.
        """
        number_emojis = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3", "5\u20e3",
                         "6\u20e3", "7\u20e3", "8\u20e3", "9\u20e3", "\U0001f51f"]

        if len(options) > 10:
            await ctx.send("Polls support a maximum of 10 options.")
            return

        embed = discord.Embed(title=f"Poll: {question}", color=0x3498DB)
        embed.set_footer(text=f"Poll by {ctx.author}")

        if not options:
            embed.description = "React to vote!"
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("\u2705")
            await msg.add_reaction("\u274c")
        else:
            desc = "\n".join(f"{number_emojis[i]} {opt}" for i, opt in enumerate(options))
            embed.description = desc
            msg = await ctx.send(embed=embed)
            for i in range(len(options)):
                await msg.add_reaction(number_emojis[i])

    @commands.command(name="vote")
    async def quick_vote(self, ctx: commands.Context, *, question: str):
        """Create a quick yes/no vote.

        Usage: .vote Should we do a CTF this weekend?
        """
        embed = discord.Embed(title=question, color=0x2ECC71)
        embed.set_footer(text=f"Vote by {ctx.author}")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("\U0001f44d")
        await msg.add_reaction("\U0001f44e")
        await msg.add_reaction("\U0001f937")

    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coin_flip(self, ctx: commands.Context):
        """Flip a coin.

        Usage: .coinflip
        """
        result = random.choice(["Heads", "Tails"])
        await ctx.send(f"**{result}!**")

    @commands.command(name="roll", aliases=["dice"])
    async def dice_roll(self, ctx: commands.Context, dice: str = "1d6"):
        """Roll dice in NdN format.

        Usage: .roll [NdN]
        Example: .roll 2d20
        """
        try:
            count, sides = dice.lower().split("d")
            count = int(count) if count else 1
            sides = int(sides)
        except ValueError:
            await ctx.send("Invalid format. Use `NdN` like `2d6` or `1d20`.")
            return

        if count < 1 or count > 100 or sides < 2 or sides > 1000:
            await ctx.send("Keep it reasonable: 1-100 dice, 2-1000 sides.")
            return

        rolls = [random.randint(1, sides) for _ in range(count)]
        embed = discord.Embed(title=f"Rolling {dice}", color=0xF39C12)
        embed.add_field(name="Rolls", value=", ".join(str(r) for r in rolls))
        embed.add_field(name="Total", value=str(sum(rolls)))
        await ctx.send(embed=embed)

    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def build_embed(self, ctx: commands.Context, title: str, *, description: str):
        """Create a custom embed message.

        Usage: .embed "Title" Description text here
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x00FF88,
        )
        embed.set_footer(text=f"Created by {ctx.author}")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
