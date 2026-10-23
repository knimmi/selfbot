import discord
from discord.ext import commands
import requests
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def joke(self, ctx):
        try: await ctx.message.delete()
        except: pass
        j = requests.get('https://official-joke-api.appspot.com/random_joke').json()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {j['setup']} - {j['punchline']}")

    @commands.command()
    async def meme(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(requests.get('https://meme-api.com/gimme').json()['url'])

    @commands.command()
    async def name(self, ctx, *, name: str):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Your name is: {name}")

    @commands.command()
    async def nitro(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Here's a link to Nitro: https://discord.com/nitro")

    @commands.command()
    async def checkprofile(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Check out {user.mention}'s profile: https://discord.com/users/{user.id}")

    @commands.command()
    async def blurpify(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention} has been blurpified! 🗯️")

    @commands.command()
    async def deepfry(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention}'s picture has been deep fried! 🔥")

    @commands.command()
    async def captcha(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention}, please complete the captcha! 🔒")

    @commands.command()
    async def threat(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention} has issued a threat! ⚠️")

    @commands.command()
    async def iphone(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention} just got a new iPhone! 📱")

    @commands.command()
    async def ship(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention}, you are shipped! {random.choice(['❤️', '💔', '💞', '💓', '💖'])}")

async def setup(bot):
    await bot.add_cog(Fun(bot))