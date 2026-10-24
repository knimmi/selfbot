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

    def update_emojis(self, key, value):
        self.bot.custom_emojis[key] = value
        with open("emojis.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.custom_emojis, f, indent=4)

    @commands.command()
    async def risk(self, ctx):
        """Toggles Risk Mode on or off."""
        try: await ctx.message.delete()
        except: pass
        current = self.bot.config.get("risk_mode", False)
        new_val = not current
        self.update_config("risk_mode", new_val)
        status = "ENABLED" if new_val else "DISABLED"
        icon = self.bot.custom_emojis.get('check', '') if new_val else self.bot.custom_emojis.get('error', '')
        await ctx.send(f"{icon} **Risk Mode is now:** `{status}`")

    @commands.command()
    async def emoji(self, ctx, name: str, emoji_value: str):
        """Customise or add an emoji mapping in emojis.json."""
        try: await ctx.message.delete()
        except: pass
        self.update_emojis(name.lower(), emoji_value)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Emoji `{name.lower()}` set to:** {emoji_value}")

    @commands.command()
    async def prefix(self, ctx, new_val: str):
        self.update_config("prefix", new_val)
        self.bot.command_prefix = new_val
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Prefix updated to: `{new_val}`")

    @commands.command()
    async def setqr(self, ctx, *, new_val: str):
        self.update_config("Qr", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} QR Code updated to: `{new_val}`")

    @commands.command()
    async def setqr2(self, ctx, *, new_val: str):
        self.update_config("Qr2", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Second QR Code updated.")

    @commands.command()
    async def setsrvlink(self, ctx, *, new_val: str):
        self.update_config("SERVER_Link", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Server Link updated to: `{new_val}`")

    @commands.command()
    async def setuserid(self, ctx, user: discord.User = None):
        target_id = str(user.id if user else ctx.author.id)
        self.update_config("User_Id", target_id)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} User ID updated to: `{target_id}`")

    @commands.command()
    async def setaddy(self, ctx, *, new_val: str):
        self.update_config("LTC_ADDY", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} LTC Addy updated to: `{new_val}`")

    @commands.command()
    async def setaddy2(self, ctx, *, new_val: str):
        self.update_config("LTC_ADDY2", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} LTC Addy 2 updated to: `{new_val}`")

    @commands.command()
    async def setbinid(self, ctx, *, new_val: str):
        self.update_config("BINANCE_ID", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Binance ID updated to: `{new_val}`")

    @commands.command()
    async def setltckey(self, ctx, *, new_val: str):
        self.update_config("ltckey", new_val)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} LTC Private Key updated.")

async def setup(bot):
    await bot.add_cog(Config(bot))