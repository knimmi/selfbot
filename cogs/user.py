import discord
from discord.ext import commands
import asyncio
import json

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def stalk(self, ctx, target_id: int):
        try: await ctx.message.delete()
        except: pass
        try:
            if "stalk" not in self.bot.config: self.bot.config["stalk"] = {}
            tid = str(target_id)
            if tid in self.bot.config["stalk"]:
                del self.bot.config["stalk"][tid]
                with open("config.json", "w", encoding="utf-8") as f: json.dump(self.bot.config, f, indent=4)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Stopped stalking:** `{target_id}`")
            else:
                ch = await ctx.guild.create_text_channel(f"stalk-{target_id}")
                self.bot.config["stalk"][tid] = ch.id
                with open("config.json", "w", encoding="utf-8") as f: json.dump(self.bot.config, f, indent=4)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Stalking `{target_id}` in {ch.mention}**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def lg(self, ctx, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        try: await guild.leave()
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def df(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        try:
            for rel in list(self.bot.relationships):
                if rel.user.id == user.id:
                    await rel.delete()
                    await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Removed Friend: {user.name}")
                    break
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def close(self, ctx, channel: discord.DMChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        if isinstance(ch, discord.DMChannel):
            try: await ch.close()
            except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def presence(self, ctx, state: str):
        try: await ctx.message.delete()
        except: pass
        s_map = { "online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "offline": discord.Status.invisible }
        if state.lower() in s_map:
            try:
                await self.bot.change_presence(status=s_map[state.lower()], activity=ctx.me.activity)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Presence**: `{state.capitalize()}`")
            except Exception as e: self.log_err(ctx, e)

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
                except Exception as e:
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[closealldms] Failed on {ch.recipient}: {e}")
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
                except Exception as e:
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[delallfriends] Failed on {rel.user}: {e}")
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
                except Exception as e:
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[leaveallgroups] Failed: {e}")

    @commands.command()
    async def setnick(self, ctx, srv_id: int = None, *, nickname: str):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        member = guild.get_member(self.bot.user.id)
        if member:
            try:
                await member.edit(nick=nickname)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Nickname changed in {guild.name} to:** `{nickname}`")
            except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setbio(self, ctx, *, bio: str):
        try: await ctx.message.delete()
        except: pass
        try:
            await self.bot.http.request(discord.http.Route("PATCH", "/users/@me/profile"), json={"bio": bio})
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Bio updated!**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setpronouns(self, ctx, *, pronouns: str):
        try: await ctx.message.delete()
        except: pass
        try:
            await self.bot.http.request(discord.http.Route("PATCH", "/users/@me/profile"), json={"pronouns": pronouns})
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Pronouns updated!**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def setdisplayname(self, ctx, *, name: str):
        try: await ctx.message.delete()
        except: pass
        try:
            await self.bot.http.request(discord.http.Route("PATCH", "/users/@me"), json={"global_name": name})
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Display name updated to:** `{name}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command(aliases=["ackall"])
    async def readall(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            for guild in self.bot.guilds: await guild.ack()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **All servers marked as read.**")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Failed to clear pings:** {e}")

async def setup(bot):
    await bot.add_cog(User(bot))