import discord
from discord.ext import commands
import requests
import qrcode
from io import BytesIO

class Crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ADDRESSES & BALANCES ---

    @commands.command()
    async def addy(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **LTC ADDY** {self.bot.custom_emojis.get('ltc', '')}\n`{self.bot.config.get('LTC_ADDY')}`\n**MUST SEND SCREENSHOT AND TX HASH AFTER PAYMENT**")

    @commands.command()
    async def addy2(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **SECOND LTC ADDY** {self.bot.custom_emojis.get('ltc', '')}\n`{self.bot.config.get('LTC_ADDY2')}`\n**MUST SEND SCREENSHOT AND TX HASH AFTER PAYMENT**")

    @commands.command()
    async def bid(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('crypto', '')} **BINANCE ID** {self.bot.custom_emojis.get('crypto', '')}\n`{self.bot.config.get('BINANCE_ID')}`\n**MUST SEND SCREENSHOT AFTER PAYMENT**")

    @commands.command(aliases=['ltcbal'])
    async def bal(self, ctx, ltcaddress: str):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get(f'https://api.blockcypher.com/v1/ltc/main/addrs/{ltcaddress}/balance', timeout=5)
            if r.status_code == 200:
                data = r.json()
                bal_ltc = data['balance'] / 10**8
                cg = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=eur', timeout=5).json()['litecoin']['eur']
                await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **ADDY**: `{ltcaddress}`\n{self.bot.custom_emojis.get('ltc', '')} **BALANCE**: `{bal_ltc:.6f} LTC` (~`€{bal_ltc * cg:.2f} EUR`)")
            else:
                await ctx.send(f"{self.bot.custom_emojis.get('error', '')} Failed to fetch balance.")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    @commands.command()
    async def mybal(self, ctx):
        await self.bal(ctx, self.bot.config.get("LTC_ADDY"))

    @commands.command()
    async def mybal2(self, ctx):
        await self.bal(ctx, self.bot.config.get("LTC_ADDY2"))

    # --- DIRECT TRANSACTION SEND ---

    @commands.command(aliases=["pay", "sendltc"])
    async def send(self, ctx, addr: str, ltc_amount: float):
        """Sends raw LTC amount directly through Tatum API."""
        try: await ctx.message.delete()
        except: pass
        
        # Risk Mode Guard
        if not self.bot.check_risk(ctx):
            return

        try:
            payload = {
                "fromAddress": [{"address": self.bot.config.get("LTC_ADDY"), "privateKey": self.bot.config.get("ltckey")}],
                "to": [{"address": addr, "value": round(float(ltc_amount), 8)}],
                "fee": "0.00005", 
                "changeAddress": self.bot.config.get("LTC_ADDY")
            }
            headers = {"accept": "application/json", "content-type": "application/json", "x-api-key": self.bot.config.get("apikey")}
            resp = requests.post("https://api.tatum.io/v3/litecoin/transaction", json=payload, headers=headers).json()
            
            if "txId" in resp:
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Successfully Sent {ltc_amount} LTC**\n- **Target:** `{addr}`\n- **TXID:** https://live.blockcypher.com/ltc/tx/{resp['txId']}")
            else:
                await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Transaction Failed:** `{resp}`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Transaction Error:** {e}")

    # --- LIVE PRICES IN EURO ---

    @commands.command(aliases=['cltc'])
    async def ltc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=eur', timeout=5).json()
            price = r['litecoin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **LTC Price:** `€{price:.2f} EUR`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    @commands.command(aliases=['csol'])
    async def sol(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=eur', timeout=5).json()
            price = r['solana']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('sol', '')} **SOL Price:** `€{price:.2f} EUR`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    @commands.command(aliases=['cbtc'])
    async def btc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur', timeout=5).json()
            price = r['bitcoin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('btc', '')} **BTC Price:** `€{price:.2f} EUR`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    @commands.command(aliases=['cusdc'])
    async def usdc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=usd-coin&vs_currencies=eur', timeout=5).json()
            price = r['usd-coin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('crypto', '')} **USDC Price:** `€{price:.4f} EUR`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    # --- CUSTOM QR IN EURO ---

    @commands.command()
    async def ltcqr(self, ctx, ltc_ady: str, eur_amount: float):
        """Generates an LTC QR code for a specific Euro value."""
        try: await ctx.message.delete()
        except: pass
        try:
            rate = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=eur", timeout=5).json()["litecoin"]["eur"]
            ltc_amt = eur_amount / rate
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(f"litecoin:{ltc_ady}?amount={ltc_amt:.8f}")
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            await ctx.send(f"QR for **€{eur_amount:.2f} EUR** (~`{ltc_amt:.8f} LTC`):", file=discord.File(buffer, filename="ltc_eur.png"))
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **QR Error:** {e}")

    # --- STATIC QR TOOLING ---

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

async def setup(bot):
    await bot.add_cog(Crypto(bot))