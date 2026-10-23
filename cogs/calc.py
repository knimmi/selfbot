import discord
from discord.ext import commands
import requests

class Calc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def math(self, ctx, *, equation):
        try: await ctx.message.delete()
        except: pass
        arrow = self.bot.custom_emojis.get('check', '')
        try:
            resp = requests.get('https://api.mathjs.org/v4/', params={'expr': equation}, timeout=5)
            if resp.status_code == 200:
                await ctx.send(f'{arrow} **EQUATION**: `{equation}`\n{arrow} **Result**: `{resp.text}`')
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command()
    async def i2c(self, ctx, amount: str):
        try: await ctx.message.delete()
        except: pass
        amt = float(amount.replace('₹', ''))
        rate = float(self.bot.config.get("I2C_Rate", 85))
        arrow = self.bot.custom_emojis.get('check', '')
        await ctx.send(f"{arrow} **EQUATION**: `{amt}/{rate}`\n{arrow} **Result** : `${amt/rate:.2f}`")

    @commands.command()
    async def c2i(self, ctx, amount: str):
        try: await ctx.message.delete()
        except: pass
        amt = float(amount.replace('$', ''))
        rate = float(self.bot.config.get("C2I_Rate", 85))
        arrow = self.bot.custom_emojis.get('check', '')
        await ctx.send(f"{arrow} **EQUATION**: `{amt}*{rate}`\n{arrow} **Result** : `₹{amt*rate:.2f}`")

    @commands.command()
    async def l2u(self, ctx, ltc_amt: float):
        try: await ctx.message.delete()
        except: pass
        arrow = self.bot.custom_emojis.get('check', '')
        try:
            resp = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
            rate = resp.json()['litecoin']['usd']
            await ctx.send(f"{arrow} **EQUATION**: `{ltc_amt}*{rate}`\n{arrow} `{ltc_amt} LTC = {ltc_amt*rate} USD`")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command()
    async def u2l(self, ctx, usd_amt: float):
        try: await ctx.message.delete()
        except: pass
        arrow = self.bot.custom_emojis.get('check', '')
        try:
            resp = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
            rate = resp.json()['litecoin']['usd']
            await ctx.send(f"{arrow} **EQUATION**: `{usd_amt}/{rate}`\n{arrow} `{usd_amt} USD = {usd_amt/rate} LTC`")
        except Exception as e:
            await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Calc(bot))