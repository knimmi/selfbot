import discord
from discord.ext import commands
import aiohttp

class EZUp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def ezup(self, ctx):
        try: await ctx.message.delete()
        except: pass

        api_key = self.bot.config.get("ez_key")
        if not api_key:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error("[ezup] No API key set.")
            return

        if not ctx.message.attachments:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error("[ezup] No attachment found in message.")
            return

        attachment = ctx.message.attachments[0]
        if attachment.size > 100 * 1024 * 1024:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[ezup] File too large: {attachment.size} bytes.")
            return

        try:
            file_bytes = await attachment.read()
            data = aiohttp.FormData()
            data.add_field('file', file_bytes, filename=attachment.filename, content_type=attachment.content_type or 'application/octet-stream')
            
            headers = {"Key": api_key, "User-Agent": "BallzBot/2.0"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.e-z.gg/files", data=data, headers=headers, timeout=180) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("success"):
                            view_url = result.get("imageUrl") or result.get("url") or result.get("rawUrl")
                            # Sends ONLY the link to chat
                            await ctx.send(view_url)
                        else:
                            if hasattr(self.bot, 'bot_logger'): 
                                self.bot.bot_logger.error(f"[ezup] API Error: {result.get('message', 'Unknown')}")
                    else:
                        if hasattr(self.bot, 'bot_logger'): 
                            self.bot.bot_logger.error(f"[ezup] HTTP {resp.status} - Upload Failed.")
                        
        except Exception as e:
            self.log_err(ctx, e)

async def setup(bot):
    await bot.add_cog(EZUp(bot))