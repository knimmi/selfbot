import discord
from discord.ext import commands
import aiohttp
import json

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.User, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        await guild.ban(user)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Banned {user.name} from {guild.name}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.User, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        await guild.kick(user)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Kicked {user.name} from {guild.name}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        await guild.unban(user)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Unbanned {user.name} in {guild.name}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        new_ch = await ch.clone()
        await ch.delete()
        await new_ch.send(f"{self.bot.custom_emojis.get('check', '')} Channel nuked!")

    @commands.command()
    async def nukesrv(self, ctx, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        if not guild.me.guild_permissions.administrator: return
        for ch in guild.channels:
            try: await ch.delete()
            except: pass
        for _ in range(18):
            try: await guild.create_text_channel('nuked-by-Knimmi')
            except: pass

    @commands.command()
    async def hide(self, ctx, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {ch.mention} hidden.")

    @commands.command()
    async def unhide(self, ctx, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {ch.mention} visible.")

    @commands.command()
    async def lock(self, ctx, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {ch.mention} locked.")

    @commands.command()
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} {ch.mention} unlocked.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def rnchannel(self, ctx, name: str, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.edit(name=name)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Channel renamed to `{name}`")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def rncategory(self, ctx, name: str, category: discord.CategoryChannel = None):
        try: await ctx.message.delete()
        except: pass
        cat = category or ctx.channel.category
        if cat:
            await cat.edit(name=name)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Category renamed to `{name}`")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def delcategory(self, ctx, category: discord.CategoryChannel = None):
        try: await ctx.message.delete()
        except: pass
        cat = category or ctx.channel.category
        if cat:
            await cat.delete()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Category deleted.")

    @commands.command()
    async def chnldel(self, ctx, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.delete()

    @commands.command()
    async def roledel(self, ctx, role_id: int):
        try: await ctx.message.delete()
        except: pass
        role = ctx.guild.get_role(role_id)
        if role: await role.delete()

    @commands.command()
    async def slow(self, ctx, seconds: int, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.edit(slowmode_delay=seconds)

    @commands.command()
    async def unslow(self, ctx, channel: discord.TextChannel = None):
        try: await ctx.message.delete()
        except: pass
        ch = channel or ctx.channel
        await ch.edit(slowmode_delay=0)

    @commands.command()
    async def steal(self, ctx, emoji: discord.PartialEmoji, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(emoji.url)) as resp:
                    if resp.status == 200:
                        img = await resp.read()
                        new_e = await guild.create_custom_emoji(name=emoji.name, image=img)
                        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Stole {new_e} to {guild.name}")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command()
    async def demoji(self, ctx, emoji: discord.Emoji):
        try: await ctx.message.delete()
        except: pass
        await emoji.delete()

    @commands.command()
    async def mod(self, ctx, trigger: str, action: str, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        if "auto_mod" not in self.bot.config:
            self.bot.config["auto_mod"] = {}
        if str(guild.id) not in self.bot.config["auto_mod"]:
            self.bot.config["auto_mod"][str(guild.id)] = {}
        
        self.bot.config["auto_mod"][str(guild.id)][trigger.lower()] = action.lower()
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **AutoMod added:** `{trigger}` -> `{action}` in `{guild.name}`")

    @commands.command()
    async def delmod(self, ctx, trigger: str, srv_id: int = None):
        try: await ctx.message.delete()
        except: pass
        guild = self.bot.get_guild(srv_id) if srv_id else ctx.guild
        if str(guild.id) in self.bot.config.get("auto_mod", {}):
            if trigger.lower() in self.bot.config["auto_mod"][str(guild.id)]:
                del self.bot.config["auto_mod"][str(guild.id)][trigger.lower()]
                self.save_config()
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **AutoMod removed:** `{trigger}`")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def csrv(self, ctx, copy_id: int, target_id: int = None):
        try: await ctx.message.delete()
        except: pass
        target = self.bot.get_guild(target_id) if target_id else ctx.guild
        source = self.bot.get_guild(copy_id)

        if not source or not target:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid server ID.**")

        await ctx.send(f"{self.bot.custom_emojis.get('loading', '')} **Cloning `{source.name}` into `{target.name}`...**")
        
        for channel in target.channels:
            try: await channel.delete()
            except: pass
        for role in target.roles:
            if role != target.default_role and not role.managed:
                try: await role.delete()
                except: pass

        for role in reversed(source.roles):
            if role != source.default_role and not role.managed:
                try: await target.create_role(name=role.name, color=role.color, permissions=role.permissions, hoist=role.hoist)
                except: pass

        for category in source.categories:
            try:
                new_cat = await target.create_category(name=category.name)
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel):
                        await target.create_text_channel(name=channel.name, category=new_cat)
                    elif isinstance(channel, discord.VoiceChannel):
                        await target.create_voice_channel(name=channel.name, category=new_cat)
            except: pass

        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Server Clone Complete.**")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def massrole(self, ctx, action: str, role: discord.Role):
        try: await ctx.message.delete()
        except: pass
        action = action.lower()
        if action not in ["add", "remove"]: return
        
        count = 0
        for member in ctx.guild.members:
            try:
                if action == "add" and role not in member.roles:
                    await member.add_roles(role)
                    count += 1
                elif action == "remove" and role in member.roles:
                    await member.remove_roles(role)
                    count += 1
            except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Massrole:** {action}ed `{role.name}` for `{count}` users.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def massunban(self, ctx):
        try: await ctx.message.delete()
        except: pass
        count = 0
        async for ban_entry in ctx.guild.bans():
            try:
                await ctx.guild.unban(ban_entry.user)
                count += 1
            except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Pardoned {count} users.**")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.id == self.bot.user.id or not message.guild:
            return
        mod_data = self.bot.config.get("auto_mod", {}).get(str(message.guild.id), {})
        if mod_data:
            content = message.content.lower()
            for trigger, action in mod_data.items():
                if trigger in content:
                    if action == "delete":
                        try: await message.delete()
                        except: pass
                    elif action == "ban":
                        try: await message.guild.ban(message.author, reason="AutoMod")
                        except: pass
                    elif action == "timeout":
                        try: await message.author.timeout(discord.utils.utcnow() + discord.utils.timedelta(minutes=10))
                        except: pass

async def setup(bot):
    await bot.add_cog(Moderation(bot))