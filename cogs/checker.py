import discord
from discord.ext import commands
import aiohttp
import requests

class Checker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def checkpromo(self, ctx, *, promo_links):
        try: await ctx.message.delete()
        except: pass
        try:
            links = promo_links.split('\n')
            async with aiohttp.ClientSession() as session:
                for link in links:
                    code = link.split('/')[-1]
                    url = f'https://ptb.discord.com/api/v10/entitlements/gift-codes/{code}'
                    async with session.get(url) as resp:
                        if resp.status in [200, 204, 201]:
                            data = await resp.json()
                            status = "ALREADY CLAIMED" if data["uses"] == data["max_uses"] else "VALID"
                            await ctx.send(f'**Code:** {code}\n**Status:** {status}')
                        elif resp.status == 429:
                            await ctx.send('**RARE LIMITED** (Rate Limit)')
                        else:
                            await ctx.send(f'**INVALID CODE** : `{code}`')
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def checktoken(self, ctx, token_str: str):
        try: await ctx.message.delete()
        except: pass
        try:
            r = requests.get("https://discord.com/api/v10/users/@me", headers={'Authorization': token_str}, timeout=5)
            if r.status_code == 200:
                user = r.json()
                await ctx.send(f'### Token Checked\n- **Username:** `{user["username"]}`\n- **ID:** `{user["id"]}`\n- **Email:** `{user.get("email")}`\n- **Verified?** `{user.get("verified")}`')
            else:
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Invalid or locked token")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} Token Check Failed.")

async def setup(bot):
    await bot.add_cog(Checker(bot))