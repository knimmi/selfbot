import json
import asyncio
import discord
from discord.ext import commands

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_data = {}
        self.user_cooldowns = {}
        self.load_afk_data()

    def save_afk_data(self):
        with open("afk.json", "w", encoding="utf-8") as f:
            json.dump(self.afk_data, f)

    def load_afk_data(self):
        try:
            with open("afk.json", "r", encoding="utf-8") as f:
                self.afk_data = json.load(f)
        except FileNotFoundError:
            self.afk_data = {}

    @commands.command()
    async def afk(self, ctx, *, reason="busy so don't ping"):
        try: await ctx.message.delete()
        except: pass
        self.afk_data[str(ctx.author.id)] = reason
        self.save_afk_data()
        arrow = self.bot.custom_emojis.get('check', '')
        await ctx.send(f"{arrow} **You are now AFK..**")

    @commands.command()
    async def unafk(self, ctx):
        try: await ctx.message.delete()
        except: pass
        user_id = str(ctx.author.id)
        arrow = self.bot.custom_emojis.get('check', '')
        if user_id in self.afk_data:
            del self.afk_data[user_id]
            self.save_afk_data()
            await ctx.send(f"{arrow} **You are no longer AFK**")
        else:
            await ctx.send(f"{ctx.author.mention}, {arrow} **you are not AFK**")

    async def ignore_user_for_duration(self, user_id, duration):
        self.user_cooldowns[user_id] = True
        await asyncio.sleep(duration)
        self.user_cooldowns.pop(user_id, None)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return
        for user_id, reason in self.afk_data.items():
            if f"<@{user_id}>" in message.content or (message.reference and getattr(message.reference.cached_message, 'author', None) and str(message.reference.cached_message.author.id) == user_id):
                if message.author.id not in self.user_cooldowns:
                    await message.channel.send(f"{message.author.mention}, **I am afk rn**., **{reason}**")
                    await self.ignore_user_for_duration(message.author.id, 30)
                break

async def setup(bot):
    await bot.add_cog(AFK(bot))