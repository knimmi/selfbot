import discord
from discord.ext import commands
import requests
import qrcode
from io import BytesIO

class Crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def addy(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **LTC ADDY** {self.bot.custom_emojis.get('ltc', '')}\n`{self.bot.config.get('LTC_ADDY')}`\n**MUST SEND SCREENSHOT AND TX HASH AFTER PAYMENT**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def addy2(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **SECOND LTC ADDY** {self.bot.custom_emojis.get('ltc', '')}\n`{self.bot.config.get('LTC_ADDY2')}`\n**MUST SEND SCREENSHOT AND TX HASH AFTER PAYMENT**")
        except Exception as e: self.log_err(ctx, e)

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
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** API Timeout/Fail")

    @commands.command()
    async def mybal(self, ctx):
        await self.bal(ctx, self.bot.config.get("LTC_ADDY"))

    @commands.command()
    async def mybal2(self, ctx):
        await self.bal(ctx, self.bot.config.get("LTC_ADDY2"))

    @commands.command(aliases=["pay", "sendltc"])
    async def send(self, ctx, addr: str, ltc_amount: float):
        """Sends raw LTC amount directly through Tatum API."""
        try: await ctx.message.delete()
        except: pass
        if not self.bot.check_risk(ctx): return

        try:
            payload = {
                "fromAddress": [{"address": self.bot.config.get("LTC_ADDY"), "privateKey": self.bot.config.get("ltckey")}],
                "to": [{"address": addr, "value": round(float(ltc_amount), 8)}],
                "fee": "0.00005", 
                "changeAddress": self.bot.config.get("LTC_ADDY")
            }
            headers = {"accept": "application/json", "content-type": "application/json", "x-api-key": self.bot.config.get("apikey")}
            resp = requests.post("https://api.tatum.io/v3/litecoin/transaction", json=payload, headers=headers, timeout=10).json()
            
            if "txId" in resp:
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Successfully Sent {ltc_amount} LTC**\n- **Target:** `{addr}`\n- **TXID:** https://live.blockcypher.com/ltc/tx/{resp['txId']}")
            else:
                await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Transaction Failed:** `{resp}`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Transaction Error.** Check logs.")

    @commands.command(aliases=["tx", "track"])
    async def checktx(self, ctx, tx_hash: str):
        """Checks the live blockchain status of an LTC transaction."""
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get(f'https://api.blockcypher.com/v1/ltc/main/txs/{tx_hash}', timeout=5)
            if r.status_code == 200:
                data = r.json()
                confs = data.get("confirmations", 0)
                total_sent = data.get("total", 0) / 10**8
                fees = data.get("fees", 0) / 10**8
                
                check_icon = self.bot.custom_emojis.get('check', '')
                load_icon = self.bot.custom_emojis.get('loading', '')
                status = f"{check_icon} Confirmed" if confs > 0 else f"{load_icon} Unconfirmed"
                
                msg = f"### {self.bot.custom_emojis.get('ltc', '')} Transaction Info\n"
                msg += f"- **Hash:** `{tx_hash}`\n"
                msg += f"- **Status:** {status} ({confs} Confirmations)\n"
                msg += f"- **Amount Sent:** `{total_sent:.8f} LTC`\n"
                msg += f"- **Network Fee:** `{fees:.8f} LTC`\n"
                msg += f"- **Link:** https://live.blockcypher.com/ltc/tx/{tx_hash}"
                await ctx.send(msg)
            else:
                await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **TX Not Found:** Check the hash or try again later.")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **API Error.**")

    @commands.command(aliases=['cltc'])
    async def ltc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=eur', timeout=5).json()
            price = r['litecoin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('ltc', '')} **LTC Price:** `€{price:.2f} EUR`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **API Error.**")

    @commands.command(aliases=['csol'])
    async def sol(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=eur', timeout=5).json()
            price = r['solana']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('sol', '')} **SOL Price:** `€{price:.2f} EUR`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **API Error.**")

    @commands.command(aliases=['cbtc'])
    async def btc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur', timeout=5).json()
            price = r['bitcoin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('btc', '')} **BTC Price:** `€{price:.2f} EUR`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **API Error.**")

    @commands.command(aliases=['cusdc'])
    async def usdc(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=usd-coin&vs_currencies=eur', timeout=5).json()
            price = r['usd-coin']['eur']
            await ctx.send(f"{self.bot.custom_emojis.get('crypto', '')} **USDC Price:** `€{price:.4f} EUR`")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **API Error.**")

    @commands.command()
    async def ltcqr(self, ctx, ltc_ady: str, eur_amount: float):
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
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **QR Error.**")

    @commands.command()
    async def qr(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.config.get('Qr')}\n**MUST SEND SCREENSHOT**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def qr2(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.config.get('Qr2')}\n**MUST SEND SCREENSHOT**")
        except Exception as e: self.log_err(ctx, e)

async def setup(bot):
    await bot.add_cog(Crypto(bot))