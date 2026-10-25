import discord
from discord.ext import commands, tasks
import asyncio

class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rotator_msgs = []
        self.rotator_task.start()

    def cog_unload(self):
        self.rotator_task.cancel()
        
    def is_valid_image(self, url: str) -> bool:
        if not url: return True
        # Discord requires direct image links. Blocks generic google search urls.
        valid_exts = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
        return any(ext in url.lower() for ext in valid_exts) or "discordapp.com/attachments" in url or "imgur.com" in url

    @tasks.loop(seconds=10)
    async def rotator_task(self):
        if not self.rotator_msgs: return
        for status_text in self.rotator_msgs:
            if not self.rotator_msgs: break
            act = discord.CustomActivity(name=status_text.strip())
            await self.bot.change_presence(status=discord.Status.dnd, activity=act)
            await asyncio.sleep(10)

    @commands.command()
    async def status(self, ctx, *, text: str):
        """Sets custom status. Example: .status Online and Selling!"""
        try: await ctx.message.delete()
        except: pass
        act = discord.CustomActivity(name=text)
        await self.bot.change_presence(status=discord.Status.dnd, activity=act)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Status Set**: `{text}`")

    @commands.command()
    async def rotate(self, ctx, *, raw_text: str):
        """Example: .rotate Open / Closed / Sleeping"""
        try: await ctx.message.delete()
        except: pass
        self.rotator_msgs = [msg.strip() for msg in raw_text.split("/") if msg.strip()]
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Status Rotator started with {len(self.rotator_msgs)} phases.**")

    @commands.command(aliases=["stoprotate"])
    async def stop_rotate(self, ctx):
        try: await ctx.message.delete()
        except: pass
        self.rotator_msgs = []
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Status Rotator stopped.**")

    @commands.command()
    async def stream(self, ctx, title: str, img_url: str = None):
        try: await ctx.message.delete()
        except: pass
        
        if not self.is_valid_image(img_url):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid Image:** URL must be a direct link (.png/.jpg) or a Discord Attachment.")
            
        act = discord.Streaming(name=title, url="https://twitch.tv/twitch")
        if img_url:
            act.large_image_url = img_url
            
        await self.bot.change_presence(activity=act)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Stream Status Set:** `{title}`")

    @commands.command()
    async def play(self, ctx, title: str, img_url: str = None):
        try: await ctx.message.delete()
        except: pass
        
        if not self.is_valid_image(img_url):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid Image:** URL must be a direct link (.png/.jpg) or a Discord Attachment.")
            
        act = discord.Activity(type=discord.ActivityType.playing, name=title)
        if img_url:
            act.large_image_url = img_url
            
        await self.bot.change_presence(activity=act)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Playing Status Set:** `{title}`")

    @commands.command(aliases=["watch"])
    async def watching(self, ctx, title: str, img_url: str = None):
        try: await ctx.message.delete()
        except: pass
        
        if not self.is_valid_image(img_url):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid Image:** URL must be a direct link (.png/.jpg) or a Discord Attachment.")
            
        act = discord.Activity(type=discord.ActivityType.watching, name=title)
        if img_url:
            act.large_image_url = img_url
            
        await self.bot.change_presence(activity=act)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Watching Status Set:** `{title}`")

    @commands.command(aliases=["listen"])
    async def listening(self, ctx, title: str, img_url: str = None):
        try: await ctx.message.delete()
        except: pass
        
        if not self.is_valid_image(img_url):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid Image:** URL must be a direct link (.png/.jpg) or a Discord Attachment.")
            
        act = discord.Activity(type=discord.ActivityType.listening, name=title)
        if img_url:
            act.large_image_url = img_url
            
        await self.bot.change_presence(activity=act)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Listening Status Set:** `{title}`")

    @commands.command()
    async def stopactivity(self, ctx):
        try: await ctx.message.delete()
        except: pass
        self.rotator_msgs = []
        await self.bot.change_presence(activity=None, status=discord.Status.dnd)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Activity Cleared.**")

async def setup(bot):
    await bot.add_cog(StatusCommands(bot))