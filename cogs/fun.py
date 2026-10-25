import discord
from discord.ext import commands
import requests

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def joke(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            j = requests.get('https://official-joke-api.appspot.com/random_joke', timeout=5).json()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {j['setup']} - {j['punchline']}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def meme(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            url = requests.get('https://meme-api.com/gimme', timeout=5).json()['url']
            await ctx.send(url)
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def name(self, ctx, *, name: str):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Your name is: {name}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def nitro(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Here's a link to Nitro: https://discord.com/nitro")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def checkprofile(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Check out {user.mention}'s profile: https://discord.com/users/{user.id}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def blurpify(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention} has been blurpified! {self.bot.custom_emojis.get('fun_blurp', '')}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def deepfry(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention}'s picture has been deep fried! {self.bot.custom_emojis.get('fun_fire', '')}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def captcha(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention}, please complete the captcha! {self.bot.custom_emojis.get('fun_lock', '')}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def threat(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention} has issued a threat! {self.bot.custom_emojis.get('fun_warn', '')}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def iphone(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention} just got a new iPhone! {self.bot.custom_emojis.get('fun_phone', '')}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def ship(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {user.mention}, you are shipped! {self.bot.custom_emojis.get('fun_heart', '')}")
        except Exception as e: self.log_err(ctx, e)

async def setup(bot):
    await bot.add_cog(Fun(bot))