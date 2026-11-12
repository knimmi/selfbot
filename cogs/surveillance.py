import datetime
from collections import deque
import discord
from discord.ext import commands


class Surveillance(commands.Cog, name="Surveillance"):
    """Ghost Global User Message Lookup & Live User Activity Tracker."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tracked_user_ids: set[int] = set()
        self.tracking_feed: deque[dict] = deque(maxlen=200)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author or message.author.id not in self.tracked_user_ids:
            return
        self.tracking_feed.appendleft({
            "type": "TRACKED",
            "author": str(message.author),
            "author_id": message.author.id,
            "content": message.content or "[Attachment/Embed]",
            "channel_name": getattr(message.channel, "name", "DM"),
            "guild_name": message.guild.name if message.guild else "Direct Message",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        })

    @commands.command(name="stalk", aliases=["surveillance", "usersearch"], help="Search recent messages from a user across shared channels.")
    async def stalk(self, ctx: commands.Context, user: discord.User, limit_per_channel: int = 25):
        status_msg = await ctx.send(f"`[Ghost Surveillance]` Scanning recent history for **{user}**...")
        matches = []

        guilds_to_scan = [ctx.guild] if ctx.guild else list(self.bot.guilds)[:5]
        for guild in guilds_to_scan:
            if not guild:
                continue
            for channel in guild.text_channels:
                perms = channel.permissions_for(guild.me)
                if not (perms.read_messages and perms.read_message_history):
                    continue
                try:
                    async for m in channel.history(limit=limit_per_channel):
                        if m.author.id == user.id and m.content:
                            matches.append(
                                f"[{guild.name} #{channel.name}] ({m.created_at.strftime('%m-%d %H:%M')}): {m.content[:120]}"
                            )
                            if len(matches) >= 15:
                                break
                except Exception:
                    continue
                if len(matches) >= 15:
                    break
            if len(matches) >= 15:
                break

        if not matches:
            return await status_msg.edit(content=f"`[Ghost Surveillance]` No recent messages found for **{user}**.")

        report = "\n".join(matches)
        await status_msg.edit(content=f"```ini\n[Ghost Surveillance Report: {user}]\n{report[:1850]}\n```")

    @commands.command(name="trackuser", aliases=["watchuser"], help="Toggle live surveillance tracking on a specific user ID/mention.")
    async def trackuser(self, ctx: commands.Context, user: discord.User):
        if user.id in self.tracked_user_ids:
            self.tracked_user_ids.remove(user.id)
            return await ctx.send(f"`[Ghost Surveillance]` Stopped tracking **{user}**.", delete_after=6)

        self.tracked_user_ids.add(user.id)
        await ctx.send(f"`[Ghost Surveillance]` Now logging all live messages from **{user}** to the Web UI.", delete_after=6)

    @commands.command(name="mutuals", help="List all mutual servers shared with a user.")
    async def mutuals(self, ctx: commands.Context, user: discord.User):
        shared = [g.name for g in self.bot.guilds if g.get_member(user.id)]
        if not shared:
            return await ctx.send(f"`[Ghost Surveillance]` No mutual servers found with **{user}**.", delete_after=8)
        formatted = "\n".join(f"• {name}" for name in shared[:30])
        await ctx.send(f"```ini\n[Mutual Servers with {user} ({len(shared)})]\n{formatted}\n```")


async def setup(bot: commands.Bot):
    await bot.add_cog(Surveillance(bot))