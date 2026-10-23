import discord
from discord.ext import commands

class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["setpresence"])
    async def presence(self, ctx, state: str):
        try: await ctx.message.delete()
        except: pass
        s_map = {
            "online": discord.Status.online, "idle": discord.Status.idle,
            "dnd": discord.Status.dnd, "offline": discord.Status.invisible,
            "invisible": discord.Status.invisible
        }
        if state.lower() in s_map:
            await self.bot.change_presence(status=s_map[state.lower()], activity=ctx.me.activity)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Presence**: `{state.capitalize()}`")

    @commands.command(aliases=["setstatus", "customstatus"])
    async def status(self, ctx, *, text: str):
        try: await ctx.message.delete()
        except: pass
        act = discord.CustomActivity(name=text)
        await self.bot.change_presence(status=discord.Status.dnd, activity=act)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Status Set**: `{text}`")

    @commands.command()
    async def stream(self, ctx, *, title: str):
        try: await ctx.message.delete()
        except: pass
        await self.bot.change_presence(activity=discord.Streaming(name=title, url="https://twitch.tv/twitch"))

    @commands.command()
    async def play(self, ctx, *, title: str):
        try: await ctx.message.delete()
        except: pass
        await self.bot.change_presence(activity=discord.Game(name=title))

    @commands.command(aliases=["watch"])
    async def watching(self, ctx, *, message):
        try: await ctx.message.delete()
        except: pass
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=message))

    @commands.command(aliases=["listen"])
    async def listening(self, ctx, *, message):
        try: await ctx.message.delete()
        except: pass
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=message))

    @commands.command()
    async def stopactivity(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await self.bot.change_presence(activity=None, status=discord.Status.dnd)

async def setup(bot):
    await bot.add_cog(StatusCommands(bot))