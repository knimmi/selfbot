import discord
from discord.ext import commands
import asyncio
from collections import deque
from deep_translator import GoogleTranslator

class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category_messages = {}
        self.active_tasks = {}
        self.deleted_messages = {}

    @commands.command()
    async def spam(self, ctx, times: int, *, message):
        try: await ctx.message.delete()
        except: pass
        for _ in range(times):
            await ctx.send(message)
            await asyncio.sleep(0.1)

    @commands.command(aliases=['purge'])
    async def clear(self, ctx, times: int):
        deleted = 0
        async for msg in ctx.channel.history(limit=times + 1):
            if msg.author.id == self.bot.user.id:
                try:
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.3)
                except: pass

    @commands.command()
    async def dm(self, ctx, user: discord.User, *, message):
        try: await ctx.message.delete()
        except: pass
        try:
            await user.send(message)
            await ctx.send(f"[+] Successfully DM'd {user.name}")
        except Exception as e:
            await ctx.send(f"[-] Failed to DM: {e}")

    @commands.command()
    async def translate(self, ctx, *, text: str):
        try: await ctx.message.delete()
        except: pass
        try:
            t = GoogleTranslator(source='auto', target='en').translate(text)
            await ctx.send(f"**Original:** {text}\n**Translated:** {t}")
        except:
            await ctx.send("**Error**: Could not translate.")

    @commands.command()
    async def dmall(self, ctx, *, msg):
        try: await ctx.message.delete()
        except: pass
        for member in ctx.guild.members:
            if member != self.bot.user:
                try:
                    await member.send(msg)
                    await asyncio.sleep(5)
                except: pass

    @commands.command()
    async def massdmfrnds(self, ctx, *, message):
        try: await ctx.message.delete()
        except: pass
        for user in list(self.bot.user.friends):
            try:
                await user.send(message)
                await asyncio.sleep(1.5)
            except: pass

    @commands.command()
    async def sc(self, ctx, category_id: int, *, message: str):
        try: await ctx.message.delete()
        except: pass
        if ctx.guild:
            self.category_messages[category_id] = message
            self.active_tasks[category_id] = True
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Monitoring Ticket Category {category_id}**")

    @commands.command()
    async def stopsc(self, ctx, category_id: int):
        try: await ctx.message.delete()
        except: pass
        if category_id in self.active_tasks:
            self.active_tasks[category_id] = False
            await ctx.send(f"**Stopped Category {category_id}**")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel):
            if channel.category_id in self.active_tasks and self.active_tasks[channel.category_id]:
                await asyncio.sleep(1)
                await channel.send(self.category_messages[channel.category_id])

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild:
            if message.channel.id not in self.deleted_messages:
                self.deleted_messages[message.channel.id] = deque(maxlen=5)
            self.deleted_messages[message.channel.id].append({
                'content': message.content, 'author': message.author.name
            })

async def setup(bot):
    await bot.add_cog(Messages(bot))