import discord
from discord.ext import commands
import json
from werkzeug.security import generate_password_hash

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] Config Error: {e}")

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
        try: await ctx.message.delete()
        except: pass
        try:
            current = self.bot.config.get("risk_mode", False)
            new_val = not current
            self.update_config("risk_mode", new_val)
            status = "ENABLED" if new_val else "DISABLED"
            icon = self.bot.custom_emojis.get('check', '') if new_val else self.bot.custom_emojis.get('error', '')
            await ctx.send(f"{icon} **Risk Mode is now:** `{status}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def emoji(self, ctx, name: str, emoji_value: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_emojis(name.lower(), emoji_value)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Emoji `{name.lower()}` set to:** {emoji_value}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def prefix(self, ctx, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("prefix", new_val)
            self.bot.command_prefix = new_val
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Prefix updated to: `{new_val}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setqr(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("Qr", new_val)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} QR Code updated to: `{new_val}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setqr2(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("Qr2", new_val)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Second QR Code updated.")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setsrvlink(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("SERVER_Link", new_val)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Server Link updated to: `{new_val}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setuserid(self, ctx, user: discord.User = None):
        try: await ctx.message.delete()
        except: pass
        try:
            target_id = str(user.id if user else ctx.author.id)
            self.update_config("User_Id", target_id)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} User ID updated to: `{target_id}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setaddy(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("LTC_ADDY", new_val)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} LTC Addy updated to: `{new_val}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setaddy2(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("LTC_ADDY2", new_val)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} LTC Addy 2 updated to: `{new_val}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setafkmsg(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("afk_default", new_val)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Default AFK message updated to: `{new_val}`")
        except Exception as e: self.log_err(ctx, e)
        
    @commands.command()
    async def setltckey(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("ltckey", new_val)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} LTC Private Key updated.")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setapikey(self, ctx, *, new_val: str):
        """Sets the Tatum API Key used for sending LTC."""
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("apikey", new_val.strip())
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Tatum API Key updated.")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setspclient(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("spotify_client_id", new_val.strip())
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Spotify Client ID updated.")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setspsecret(self, ctx, *, new_val: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.update_config("spotify_client_secret", new_val.strip())
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Spotify Client Secret updated.")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setdashcreds(self, ctx, username: str, password: str):
        try: await ctx.message.delete()
        except: pass
        try:
            self.bot.config["dash_username"] = username
            self.bot.config["dash_hash"] = generate_password_hash(password)
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.bot.config, f, indent=4)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Dashboard Credentials updated.**")
        except Exception as e: self.log_err(ctx, e)

async def setup(bot):
    await bot.add_cog(Config(bot))