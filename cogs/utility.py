"""
Utility cog for DayZero Bot.

Provides server info, user info, avatar, poll creation, ping,
uptime, role info, emoji list, and a coin flip / dice roll.
"""

import platform
import random
import re
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
    async def info(self, ctx: commands.Context):
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

    @commands.command(name="contribute", aliases=["github", "repo", "source"])
    async def contribute(self, ctx: commands.Context):
        """Get the link to the bot's GitHub repository.

        Usage: .contribute
        """
        embed = discord.Embed(
            title="Contribute to DayZero Bot",
            description=(
                "Want to contribute, report a bug, or check out the source code?\n\n"
                "**GitHub:** [Prestondevs/dayzero_discord_bot]"
                "(https://github.com/Prestondevs/dayzero_discord_bot)"
            ),
            color=0x00FF88,
        )
        embed.set_footer(text="Pull requests welcome!")
        await ctx.send(embed=embed)

    @commands.command(name="embed")
    @commands.has_permissions(administrator=True)
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


    @commands.command(name="createctfteam", aliases=["ctfteam", "newctf"])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def create_ctf_team(self, ctx: commands.Context, comp_name: str, *members: discord.Member):
        """Create a CTF competition channel, role, and assign team members.

        Usage: .createctfteam <comp_name> @member1 @member2 ...
        Example: .createctfteam CPTC-2026 @alice @bob @charlie

        This will:
        - Create a role named after the competition
        - Assign all mentioned members to that role
        - Create a private channel in the Competitions category
        - Post onboarding info with dues and ethics contract links
        """
        if not members:
            await ctx.send(
                f"You need to mention at least one member.\n"
                f"Usage: `{ctx.prefix}createctfteam <comp_name> @member1 @member2 ...`"
            )
            return

        # Find the Competitions category (case-insensitive, flexible matching)
        comp_category = None
        for cat in ctx.guild.categories:
            if re.search(r"comp(etition)?s?", cat.name, re.IGNORECASE):
                comp_category = cat
                break

        # Create the role
        role = await ctx.guild.create_role(
            name=comp_name,
            mentionable=True,
            reason=f"CTF team created by {ctx.author}",
        )

        # Assign all members to the role
        for member in members:
            await member.add_roles(role, reason=f"Added to CTF team: {comp_name}")

        # Channel name (Discord requires lowercase, no spaces)
        channel_name = comp_name.lower().replace(" ", "-")

        # Set up permissions: deny @everyone, allow the team role + bot
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
                send_messages=False,
            ),
            role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
            ),
        }

        channel = await ctx.guild.create_text_channel(
            name=channel_name,
            category=comp_category,
            overwrites=overwrites,
            reason=f"CTF competition channel created by {ctx.author}",
        )

        # Build the member mention list
        member_list = "\n".join(f"- {m.mention}" for m in members)

        welcome_embed = discord.Embed(
            title=f"Welcome to {comp_name}!",
            description=(
                f"You have been selected to compete in **{comp_name}**. "
                f"This channel is your team's private workspace for coordination, "
                f"writeups, and strategy.\n\n"
                f"**Team Members:**\n{member_list}"
            ),
            color=0x00FF88,
        )
        welcome_embed.add_field(
            name="Before You Compete",
            value=(
                "If you haven't already, please complete **both** of the following:\n\n"
                "**1. Pay Club Dues**\n"
                "[Click here to pay dues](https://forms.gle/1VnMkDJei2sEKitg6)\n\n"
                "**2. Sign the Ethical Contract**\n"
                "[Click here to sign](https://forms.gle/3vabMiUB7GGnbXWW6)\n\n"
                "Both must be completed before you can officially represent DayZero in competition."
            ),
            inline=False,
        )
        welcome_embed.set_footer(text="Good luck, have fun, and hack responsibly.")

        await channel.send(f"{role.mention}", embed=welcome_embed)

        # Confirm in the original channel
        confirm_embed = discord.Embed(
            title="CTF Team Created",
            color=0x2ECC71,
        )
        confirm_embed.add_field(name="Competition", value=comp_name)
        confirm_embed.add_field(name="Channel", value=channel.mention)
        confirm_embed.add_field(name="Role", value=role.mention)
        confirm_embed.add_field(name="Members", value=f"{len(members)} assigned", inline=True)
        if comp_category:
            confirm_embed.add_field(name="Category", value=comp_category.name)
        else:
            confirm_embed.add_field(name="Category", value="None (created at top level)")
        await ctx.send(embed=confirm_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
