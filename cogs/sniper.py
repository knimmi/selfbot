import datetime
from collections import deque
import discord
from discord.ext import commands


class Sniper(commands.Cog, name="Sniper"):
    """Ghost Deleted, Edited, and Reaction Message Snipers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.deleted_messages: dict[int, deque[dict]] = {}
        self.edited_messages: dict[int, deque[dict]] = {}
        self.removed_reactions: dict[int, deque[dict]] = {}
        # Shared feed read by cogs/dashboard.py
        self.snipe_feed: deque[dict] = deque(maxlen=250)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.author or message.author.id == self.bot.user.id:
            return
        bucket = self.deleted_messages.setdefault(message.channel.id, deque(maxlen=25))
        entry = {
            "type": "DELETE",
            "author": str(message.author),
            "author_id": message.author.id,
            "content": message.content or "[No text content]",
            "attachments": [a.url for a in message.attachments],
            "channel_id": message.channel.id,
            "channel_name": getattr(message.channel, "name", "DM"),
            "guild_name": message.guild.name if message.guild else "Direct Message",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        bucket.appendleft(entry)
        self.snipe_feed.appendleft(entry)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.author or before.author.id == self.bot.user.id:
            return
        if before.content == after.content:
            return
        bucket = self.edited_messages.setdefault(before.channel.id, deque(maxlen=25))
        entry = {
            "type": "EDIT",
            "author": str(before.author),
            "author_id": before.author.id,
            "before": before.content or "[Empty]",
            "after": after.content or "[Empty]",
            "channel_id": before.channel.id,
            "channel_name": getattr(before.channel, "name", "DM"),
            "guild_name": before.guild.name if before.guild else "Direct Message",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        bucket.appendleft(entry)
        self.snipe_feed.appendleft(entry)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        if not user or user.id == self.bot.user.id:
            return
        bucket = self.removed_reactions.setdefault(reaction.message.channel.id, deque(maxlen=25))
        entry = {
            "type": "REACTION",
            "author": str(user),
            "author_id": user.id,
            "emoji": str(reaction.emoji),
            "content": f"Removed {reaction.emoji} from message {reaction.message.id}",
            "channel_name": getattr(reaction.message.channel, "name", "DM"),
            "guild_name": reaction.message.guild.name if reaction.message.guild else "Direct Message",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        bucket.appendleft(entry)
        self.snipe_feed.appendleft(entry)

    @commands.command(name="snipe", help="Snipe recently deleted messages in the current channel.")
    async def snipe(self, ctx: commands.Context, index: int = 1):
        bucket = self.deleted_messages.get(ctx.channel.id)
        if not bucket or index < 1 or index > len(bucket):
            return await ctx.send("```ini\n[Ghost Snipe] No deleted messages found at that index.\n```", delete_after=8)

        data = bucket[index - 1]
        attachments_str = "\nAttachments: " + ", ".join(data["attachments"]) if data["attachments"] else ""
        msg = (
            f"```ini\n"
            f"[Ghost Deleted Message Sniper - #{index}/{len(bucket)}]\n"
            f"Author  : {data['author']} ({data['author_id']})\n"
            f"Time    : {data['timestamp']}\n"
            f"Content : {data['content']}{attachments_str}\n"
            f"```"
        )
        await ctx.send(msg)

    @commands.command(name="editsnipe", aliases=["esnipe"], help="Snipe recently edited messages in the current channel.")
    async def editsnipe(self, ctx: commands.Context, index: int = 1):
        bucket = self.edited_messages.get(ctx.channel.id)
        if not bucket or index < 1 or index > len(bucket):
            return await ctx.send("```ini\n[Ghost EditSnipe] No edited messages found at that index.\n```", delete_after=8)

        data = bucket[index - 1]
        msg = (
            f"```ini\n"
            f"[Ghost Edited Message Sniper - #{index}/{len(bucket)}]\n"
            f"Author : {data['author']} ({data['author_id']})\n"
            f"Time   : {data['timestamp']}\n"
            f"Before : {data['before']}\n"
            f"After  : {data['after']}\n"
            f"```"
        )
        await ctx.send(msg)

    @commands.command(name="reactsnipe", aliases=["rsnipe"], help="Snipe recently removed reactions in the current channel.")
    async def reactsnipe(self, ctx: commands.Context, index: int = 1):
        bucket = self.removed_reactions.get(ctx.channel.id)
        if not bucket or index < 1 or index > len(bucket):
            return await ctx.send("```ini\n[Ghost ReactSnipe] No removed reactions found at that index.\n```", delete_after=8)

        data = bucket[index - 1]
        msg = (
            f"```ini\n"
            f"[Ghost Reaction Sniper - #{index}/{len(bucket)}]\n"
            f"User   : {data['author']} ({data['author_id']})\n"
            f"Emoji  : {data['emoji']}\n"
            f"Time   : {data['timestamp']}\n"
            f"Detail : {data['content']}\n"
            f"```"
        )
        await ctx.send(msg)

    @commands.command(name="clearsnipe", help="Clear sniped message history for the current channel.")
    async def clearsnipe(self, ctx: commands.Context):
        self.deleted_messages.pop(ctx.channel.id, None)
        self.edited_messages.pop(ctx.channel.id, None)
        self.removed_reactions.pop(ctx.channel.id, None)
        await ctx.send("`[Ghost Snipe]` Cleared channel snipe cache.", delete_after=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sniper(bot))