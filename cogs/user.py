import discord
from discord.ext import commands
import asyncio

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def closealldms(self, ctx):
        try: await ctx.message.delete()
        except: pass
        closed = 0
        for ch in list(self.bot.private_channels):
            if isinstance(ch, discord.DMChannel):
                try:
                    await ch.close()
                    closed += 1
                    await asyncio.sleep(1.0)
                except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Closed {closed} DMs.")

    @commands.command()
    async def delallfriends(self, ctx):
        try: await ctx.message.delete()
        except: pass
        removed = 0
        for rel in list(self.bot.relationships):
            if rel.type == discord.RelationshipType.friend:
                try:
                    await rel.delete()
                    removed += 1
                    await asyncio.sleep(2.0)
                except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Removed {removed} friends.")

    @commands.command()
    async def leaveallgroups(self, ctx):
        try: await ctx.message.delete()
        except: pass
        for ch in list(self.bot.private_channels):
            if isinstance(ch, discord.GroupChannel):
                try:
                    await ch.leave()
                    await asyncio.sleep(1.5)
                except: pass

    @commands.command()
    async def setnick(self, ctx, server_id: int, *, nickname: str):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(server_id)
        if not guild:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Server not found!**")
        
        member = guild.get_member(self.bot.user.id)
        if not member:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **You are not in that server!**")
            
        try:
            await member.edit(nick=nickname)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Nickname changed in {guild.name} to:** `{nickname}`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Failed to change nickname:** {e}")

    @commands.command()
    async def setbio(self, ctx, *, bio: str):
        try: await ctx.message.delete()
        except: pass
        try:
            await self.bot.http.request(
                discord.http.Route("PATCH", "/users/@me/profile"), 
                json={"bio": bio}
            )
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Bio updated!**")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    @commands.command()
    async def setpronouns(self, ctx, *, pronouns: str):
        try: await ctx.message.delete()
        except: pass
        try:
            await self.bot.http.request(
                discord.http.Route("PATCH", "/users/@me/profile"), 
                json={"pronouns": pronouns}
            )
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Pronouns updated to:** `{pronouns}`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

    @commands.command(aliases=["setname", "setglobalname"])
    async def setdisplayname(self, ctx, *, name: str):
        try: await ctx.message.delete()
        except: pass
        try:
            await self.bot.http.request(
                discord.http.Route("PATCH", "/users/@me"), 
                json={"global_name": name}
            )
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Display name updated to:** `{name}`")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

async def setup(bot):
    await bot.add_cog(User(bot))