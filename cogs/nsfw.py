import discord
from discord.ext import commands
import aiohttp

class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_img(self, endpoint):
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://nekobot.xyz/api/image?type={endpoint}") as r:
                    if r.status == 200: return (await r.json()).get('message')
        except Exception as e: 
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[NSFW API Error - {endpoint}] {e}")
        return None

    @commands.command()
    async def hass(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("hass")
        if img: await ctx.send(img)

    @commands.command()
    async def ass(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("ass")
        if img: await ctx.send(img)

    @commands.command()
    async def boobs(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("boobs")
        if img: await ctx.send(img)

    @commands.command()
    async def lewdneko(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("lewdneko")
        if img: await ctx.send(img)

    @commands.command()
    async def blowjob(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("blowjob")
        if img: await ctx.send(img)

    @commands.command()
    async def hentai(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("hentai")
        if img: await ctx.send(img)

    @commands.command()
    async def gayporn(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("gayporn")
        if img: await ctx.send(img)

    @commands.command()
    async def bo_sinn(self, ctx):
        try: await ctx.message.delete()
        except: pass
        img = await self.fetch_img("bo sinn")
        if img: await ctx.send(img)
        
async def setup(bot):
    await bot.add_cog(NSFW(bot))