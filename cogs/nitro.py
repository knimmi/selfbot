import discord
from discord.ext import commands
import re
import aiohttp
import json

class Sniper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Matches discord.gift/CODE, discord.com/gifts/CODE, and discordapp.com/gifts/CODE
        self.gift_regex = re.compile(r'(?:discord\.gift/|discord\.com/gifts/|discordapp\.com/gifts/)([a-zA-Z0-9]{16,24})')
        
        if "nitro_sniper" not in self.bot.config:
            self.bot.config["nitro_sniper"] = False

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    @commands.command(aliases=["nsniper"])
    async def sniper(self, ctx):
        """Toggles the Nitro Sniper on or off."""
        try: await ctx.message.delete()
        except: pass
        try:
            current = self.bot.config.get("nitro_sniper", False)
            new_val = not current
            self.bot.config["nitro_sniper"] = new_val
            self.save_config()
            
            status = "ENABLED" if new_val else "DISABLED"
            icon = self.bot.custom_emojis.get('check', '') if new_val else self.bot.custom_emojis.get('error', '')
            await ctx.send(f"{icon} **Nitro Sniper is now:** `{status}`")
        except Exception as e: self.log_err(ctx, e)

    async def redeem_code(self, code, channel_id):
        url = f"https://discord.com/api/v10/entitlements/gift-codes/{code}/redeem"
        headers = {
            "Authorization": self.bot.http.token,
            "Content-Type": "application/json"
        }
        # Discord requires the channel_id where the code was found to process the redemption
        payload = {"channel_id": str(channel_id)}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status in [200, 201, 204]:
                    if hasattr(self.bot, 'bot_logger'): 
                        self.bot.bot_logger.info(f"[Nitro Sniper] SUCCESSFULLY CLAIMED NITRO: {code}")
                elif resp.status == 429:
                    if hasattr(self.bot, 'bot_logger'): 
                        self.bot.bot_logger.warning(f"[Nitro Sniper] Rate limited on code: {code}")
                else:
                    if hasattr(self.bot, 'bot_logger'): 
                        self.bot.bot_logger.error(f"[Nitro Sniper] Invalid/Used code: {code} (HTTP {resp.status})")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.bot.config.get("nitro_sniper", False): return
        if message.author.id == self.bot.user.id: return
        
        codes = self.gift_regex.findall(message.content)
        if codes:
            for code in codes:
                # Fire the redemption task asynchronously so it doesn't block the bot loop
                self.bot.loop.create_task(self.redeem_code(code, message.channel.id))

async def setup(bot):
    await bot.add_cog(Sniper(bot))