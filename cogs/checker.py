import discord
from discord.ext import commands
import aiohttp
import requests

class Checker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def checkpromo(self, ctx, *, promo_links):
        try: await ctx.message.delete()
        except: pass
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

    @commands.command()
    async def checktoken(self, ctx, token_str: str):
        try: await ctx.message.delete()
        except: pass
        r = requests.get("https://discord.com/api/v10/users/@me", headers={'Authorization': token_str})
        if r.status_code == 200:
            user = r.json()
            await ctx.send(f'### Token Checked\n- **Username:** `{user["username"]}`\n- **ID:** `{user["id"]}`\n- **Email:** `{user.get("email")}`\n- **Verified?** `{user.get("verified")}`')
        else:
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Invalid or locked token")

async def setup(bot):
    await bot.add_cog(Checker(bot))