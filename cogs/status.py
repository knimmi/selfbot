import discord
from discord.ext import commands, tasks
import asyncio

class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rotator_msgs = []
        self.rotator_task.start()

    def cog_unload(self):
        self.rotator_task.cancel()

    @tasks.loop(seconds=10)
    async def rotator_task(self):
        if not self.rotator_msgs: return
        for status_text in self.rotator_msgs:
            if not self.rotator_msgs: break
            try:
                act = discord.CustomActivity(name=status_text.strip())
                await self.bot.change_presence(status=discord.Status.dnd, activity=act)
            except Exception as e:
                if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[rotator_task] Failed: {e}")
            await asyncio.sleep(10)

    @commands.command()
    async def status(self, ctx, *, text: str):
        try: await ctx.message.delete()
        except: pass
        try:
            act = discord.CustomActivity(name=text)
            await self.bot.change_presence(status=discord.Status.dnd, activity=act)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Status Set**: `{text}`")
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def rotate(self, ctx, *, raw_text: str):
        try: await ctx.message.delete()
        except: pass
        self.rotator_msgs = [msg.strip() for msg in raw_text.split("/") if msg.strip()]
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Status Rotator started with {len(self.rotator_msgs)} phases.**")

    @commands.command(aliases=["stoprotate"])
    async def stop_rotate(self, ctx):
        try: await ctx.message.delete()
        except: pass
        self.rotator_msgs = []
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Status Rotator stopped.**")

    @commands.command()
    async def stream(self, ctx, *, title: str):
        try: await ctx.message.delete()
        except: pass
        try:
            act = discord.Streaming(name=title, url="https://twitch.tv/twitch")
            await self.bot.change_presence(activity=act)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Stream Status Set:** `{title}`")
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def play(self, ctx, *, title: str):
        try: await ctx.message.delete()
        except: pass
        try:
            act = discord.Activity(type=discord.ActivityType.playing, name=title)
            await self.bot.change_presence(activity=act)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Playing Status Set:** `{title}`")
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command(aliases=["watch"])
    async def watching(self, ctx, *, title: str):
        try: await ctx.message.delete()
        except: pass
        try:
            act = discord.Activity(type=discord.ActivityType.watching, name=title)
            await self.bot.change_presence(activity=act)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Watching Status Set:** `{title}`")
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command(aliases=["listen"])
    async def listening(self, ctx, *, title: str):
        try: await ctx.message.delete()
        except: pass
        try:
            act = discord.Activity(type=discord.ActivityType.listening, name=title)
            await self.bot.change_presence(activity=act)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Listening Status Set:** `{title}`")
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def stopactivity(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            self.rotator_msgs = []
            await self.bot.change_presence(activity=None, status=discord.Status.dnd)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Activity Cleared.**")
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

async def setup(bot):
    await bot.add_cog(StatusCommands(bot))