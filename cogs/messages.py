import discord
from discord.ext import commands
import asyncio
from deep_translator import GoogleTranslator

class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_greeter = {}

    @commands.command()
    async def spam(self, ctx, times: int, *, message: str):
        try: await ctx.message.delete()
        except: pass
        if not self.bot.check_risk(ctx): return
        for _ in range(times):
            await ctx.send(message)
            await asyncio.sleep(0.5)

    @commands.command(aliases=['purge'])
    async def clear(self, ctx, times: int):
        if not self.bot.check_risk(ctx): return
        deleted = 0
        async for msg in ctx.channel.history(limit=times + 1):
            if msg.author.id == self.bot.user.id:
                try:
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.3)
                except: pass

    @commands.command()
    async def dm(self, ctx, user: discord.User, *, message: str):
        try: await ctx.message.delete()
        except: pass
        try:
            await user.send(message)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Successfully DM'd** {user.name}")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Failed to DM:** {e}")

    @commands.command()
    async def dmall(self, ctx, *, msg: str):
        try: await ctx.message.delete()
        except: pass
        if not self.bot.check_risk(ctx): return
        for member in ctx.guild.members:
            if member != self.bot.user:
                try:
                    await member.send(msg)
                    await asyncio.sleep(3)
                except: pass

    @commands.command(aliases=["massdmfrnds"])
    async def massdmfriends(self, ctx, *, message: str):
        try: await ctx.message.delete()
        except: pass
        if not self.bot.check_risk(ctx): return
        for user in list(self.bot.user.friends):
            try:
                await user.send(message)
                await asyncio.sleep(2)
            except: pass

    @commands.command()
    async def translate(self, ctx, *, text: str):
        try: await ctx.message.delete()
        except: pass
        try:
            t = GoogleTranslator(source='auto', target='en').translate(text)
            await ctx.send(f"**Original:** {text}\n**Translated:** {t}")
        except:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} Could not translate.")

    @commands.command()
    async def sc(self, ctx, category_id: int, *, message: str):
        try: await ctx.message.delete()
        except: pass
        self.ticket_greeter[category_id] = message
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Monitoring Ticket Category:** `{category_id}`")

    @commands.command()
    async def stopsc(self, ctx, category_id: int):
        try: await ctx.message.delete()
        except: pass
        if category_id in self.ticket_greeter:
            del self.ticket_greeter[category_id]
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Stopped Greeter for Category:** `{category_id}`")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel):
            if channel.category_id in self.ticket_greeter:
                await asyncio.sleep(1)
                try:
                    await channel.send(self.ticket_greeter[channel.category_id])
                except: pass

async def setup(bot):
    await bot.add_cog(Messages(bot))