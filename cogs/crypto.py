import discord
from discord.ext import commands
import requests
import qrcode
from io import BytesIO

class Crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def addy(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **LTC ADDY** {self.bot.custom_emojis.get('ltc', '')}\n`{self.bot.config.get('LTC_ADDY')}`\n**MUST SEND SCREENSHOT AND BLOCKCHAIN AFTER PAYMENT**")

    @commands.command()
    async def addy2(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **BINANCE LTC ADDY** {self.bot.custom_emojis.get('ltc', '')}\n`{self.bot.config.get('LTC_ADDY2')}`\n**MUST SEND SCREENSHOT AND BLOCKCHAIN AFTER PAYMENT**")

    @commands.command()
    async def bid(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('crypto', '')} **BINANCE ID** {self.bot.custom_emojis.get('crypto', '')}\n`{self.bot.config.get('BINANCE_ID')}`\n**MUST SEND SCREENSHOT AFTER PAYMENT**")

    @commands.command(aliases=["pay", "sendltc"])
    async def send(self, ctx, addr: str, value: str):
        try: await ctx.message.delete()
        except: pass
        try:
            val = float(value.strip('$'))
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=usd&vs_currencies=ltc")
            topay = r.json()['usd']['ltc'] * val
            payload = {
                "fromAddress": [{"address": self.bot.config.get("LTC_ADDY"), "privateKey": self.bot.config.get("ltckey")}],
                "to": [{"address": addr, "value": round(topay, 8)}],
                "fee": "0.00005", "changeAddress": self.bot.config.get("LTC_ADDY")
            }
            headers = {"accept": "application/json", "content-type": "application/json", "x-api-key": self.bot.config.get("apikey")}
            resp = requests.post("https://api.tatum.io/v3/litecoin/transaction", json=payload, headers=headers).json()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Successfully Sent {val}$**\n{self.bot.custom_emojis.get('check', '')} **To** {addr}\n{self.bot.custom_emojis.get('check', '')} **TXID:** https://live.blockcypher.com/ltc/tx/{resp.get('txId', 'Unknown')}")
        except Exception as e:
            await ctx.send(f"**Failed to send LTC:** {e}")

    @commands.command(aliases=['ltcbal'])
    async def bal(self, ctx, ltcaddress: str):
        try: await ctx.message.delete()
        except: pass
        r = requests.get(f'https://api.blockcypher.com/v1/ltc/main/addrs/{ltcaddress}/balance')
        if r.status_code == 200:
            data = r.json()
            bal = data['balance'] / 10**8
            cg = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd').json()['litecoin']['usd']
            await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **ADDY**: `{ltcaddress}`\n{self.bot.custom_emojis.get('ltc', '')} **BALANCE**: `{bal * cg:.2f}$ USD`")
        else:
            await ctx.send("Failed to fetch balance.")

    @commands.command()
    async def mybal(self, ctx):
        await self.bal(ctx, self.bot.config.get("LTC_ADDY"))

    @commands.command()
    async def mybal2(self, ctx):
        await self.bal(ctx, self.bot.config.get("LTC_ADDY2"))

    @commands.command(aliases=['cltc'])
    async def ltc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        price = requests.get('https://api.coingecko.com/api/v3/coins/litecoin').json()['market_data']['current_price']['usd']
        await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **LTC Price:** `{price:.2f}`")

    @commands.command(aliases=['csol'])
    async def sol(self, ctx):
        try: await ctx.message.delete()
        except: pass
        price = requests.get('https://api.coingecko.com/api/v3/coins/solana').json()['market_data']['current_price']['usd']
        await ctx.send(f"{self.bot.custom_emojis.get('sol', '')} **SOL Price:** `{price:.2f}`")

    @commands.command(aliases=['cbtc'])
    async def btc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        price = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin').json()['market_data']['current_price']['usd']
        await ctx.send(f"{self.bot.custom_emojis.get('btc', '')} **BTC Price:** `{price:.2f}`")

    @commands.command(aliases=['cusdt'])
    async def usdt(self, ctx):
        try: await ctx.message.delete()
        except: pass
        price = requests.get('https://api.coingecko.com/api/v3/coins/tether').json()['market_data']['current_price']['usd']
        await ctx.send(f"{self.bot.custom_emojis.get('usdt', '')} **USDT Price:** `{price:.2f}`")

    @commands.command()
    async def ltcqr(self, ctx, ltc_ady: str, usd_amount: float):
        try: await ctx.message.delete()
        except: pass
        try:
            rate = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd").json()["litecoin"]["usd"]
            amt = usd_amount / rate
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(f"litecoin:{ltc_ady}?amount={amt:.8f}")
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            await ctx.send(f"QR for **${usd_amount:.2f} USD** (~{amt:.8f} LTC):", file=discord.File(buffer, filename="ltc.png"))
        except Exception as e:
            await ctx.send(str(e))

    # --- UPI COMMANDS ---
    @commands.command()
    async def upi(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('upi', '')} **UPI** {self.bot.custom_emojis.get('upi', '')}\n{self.bot.config.get('Upi')}\n**MUST SEND SCREENSHOT**")

    @commands.command()
    async def upi2(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('upi', '')} **UPI 2** {self.bot.custom_emojis.get('upi', '')}\n{self.bot.config.get('Upi2')}\n**MUST SEND SCREENSHOT**")

    @commands.command()
    async def qr(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.config.get('Qr')}\n**MUST SEND SCREENSHOT**")

    @commands.command()
    async def qr2(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.config.get('Qr2')}\n**MUST SEND SCREENSHOT**")

    @commands.command(name='upiqr')
    async def cqr(self, ctx, amount: str, *, note: str):
        try: await ctx.message.delete()
        except: pass
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(f"upi://pay?pa={self.bot.config.get('Upi')}&am={amount}&cu=INR&tn={note}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, 'PNG')
            buffer.seek(0)
            await ctx.send(file=discord.File(fp=buffer, filename='upi.png'))
        except Exception as e:
            await ctx.send(str(e))

async def setup(bot):
    await bot.add_cog(Crypto(bot))