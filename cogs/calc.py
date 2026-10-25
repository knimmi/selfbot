import discord
from discord.ext import commands
import requests

class Calc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def math(self, ctx, *, equation: str):
        try: await ctx.message.delete()
        except: pass
        try:
            resp = requests.get('https://api.mathjs.org/v4/', params={'expr': equation}, timeout=5)
            if resp.status_code == 200:
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **EQUATION**: `{equation}`\n**Result**: `{resp.text}`")
            else:
                await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid Math Equation**")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    @commands.command()
    async def f2c(self, ctx, fiat: str, amount: float, crypto: str):
        try: await ctx.message.delete()
        except: pass
        fiat, crypto = fiat.lower(), crypto.lower()
        try:
            resp = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies={fiat}', timeout=5).json()
            rate = resp[crypto][fiat]
            result = amount / rate
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} `{amount} {fiat.upper()}` = `{result:.8f} {crypto.upper()}`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Failed.** Check the coin name (e.g., `litecoin`) and fiat (e.g., `eur`).")

    @commands.command()
    async def c2f(self, ctx, crypto: str, amount: float, fiat: str):
        try: await ctx.message.delete()
        except: pass
        fiat, crypto = fiat.lower(), crypto.lower()
        try:
            resp = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies={fiat}', timeout=5).json()
            rate = resp[crypto][fiat]
            result = amount * rate
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} `{amount} {crypto.upper()}` = `{result:.2f} {fiat.upper()}`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Failed.** Check inputs.")

    @commands.command()
    async def l2e(self, ctx, ltc_amt: float):
        try: await ctx.message.delete()
        except: pass
        try:
            rate = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=eur', timeout=5).json()['litecoin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} `{ltc_amt} LTC` = `€{ltc_amt * rate:.2f} EUR`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"Error: {e}")

    @commands.command()
    async def e2l(self, ctx, eur_amt: float):
        try: await ctx.message.delete()
        except: pass
        try:
            rate = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=eur', timeout=5).json()['litecoin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} `€{eur_amt} EUR` = `{eur_amt / rate:.8f} LTC`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Calc(bot))