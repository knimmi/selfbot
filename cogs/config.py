import discord
from discord.ext import commands
import json

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def update_config(self, key, value):
        self.bot.config[key] = value
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    @commands.command()
    async def prefix(self, ctx, new_val: str):
        self.update_config("prefix", new_val)
        self.bot.command_prefix = new_val
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Prefix updated to: `{new_val}`")

    @commands.command()
    async def setupi(self, ctx, new_val: str):
        self.update_config("Upi", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Upi updated to: `{new_val}`")

    @commands.command()
    async def setupi2(self, ctx, new_val: str):
        self.update_config("Upi2", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Upi2 updated to: `{new_val}`")

    @commands.command()
    async def setqr(self, ctx, new_val: str):
        self.update_config("Qr", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Qr updated to: `{new_val}`")

    @commands.command()
    async def setqr2(self, ctx, new_val: str):
        self.update_config("Qr2", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Qr2 updated to: `{new_val}`")

    @commands.command()
    async def setsrvlink(self, ctx, new_val: str):
        self.update_config("SERVER_Link", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Server Link updated to: `{new_val}`")

    @commands.command()
    async def setuserid(self, ctx, new_val: str):
        self.update_config("User_Id", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} User_Id updated to: `{new_val}`")

    @commands.command()
    async def setaddy(self, ctx, new_val: str):
        self.update_config("LTC_ADDY", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Ltc Addy updated to: `{new_val}`")

    @commands.command()
    async def setaddy2(self, ctx, new_val: str):
        self.update_config("LTC_ADDY2", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Ltc Addy 2 updated to: `{new_val}`")

    @commands.command()
    async def setbinid(self, ctx, new_val: str):
        self.update_config("BINANCE_ID", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Binance Id updated to: `{new_val}`")

    @commands.command()
    async def setltckey(self, ctx, new_val: str):
        self.update_config("ltckey", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Ltc Key updated to: `{new_val}`")

async def setup(bot):
    await bot.add_cog(Config(bot))