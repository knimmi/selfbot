import discord
from discord.ext import commands
import requests

class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def avatar(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(user.display_avatar.url)
        except: await ctx.send("User Don't Have Avatar")

    @commands.command()
    async def icon(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(ctx.guild.icon.url if ctx.guild.icon else "No server icon")

    @commands.command()
    async def get_image(self, ctx, query):
        try: await ctx.message.delete()
        except: pass
        headers = {'Authorization': 'Client-ID F1kSmh4MALfMKjHRxk38dZmPEV0OxsHdzuruBS_Y7to'}
        try:
            r = requests.get("https://api.unsplash.com/search/photos", headers=headers, params={"query": query, 'per_page': 1, 'orientation': 'landscape'})
            if r.json()['results']:
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} `{query}`:\n{r.json()['results'][0]['urls']['regular']}")
        except:
            await ctx.send("`Error fetching image`")

async def setup(bot):
    await bot.add_cog(ImageCog(bot))