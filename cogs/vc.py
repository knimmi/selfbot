import discord
from discord.ext import commands

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, ctx, member: discord.Member):
        return ctx.author.guild_permissions.move_members

    @commands.command(name='vckick', aliases=['vkick'])
    async def vckick(self, ctx, user: discord.Member):
        try: await ctx.message.delete()
        except: pass
        if await self.check_permissions(ctx, user) and user.voice:
            await user.move_to(None)

    @commands.command(name='vcmoveall', aliases=['moveall'])
    async def vcmoveall(self, ctx, channel1_id: int, channel2_id: int):
        try: await ctx.message.delete()
        except: pass
        ch1 = self.bot.get_channel(channel1_id)
        ch2 = self.bot.get_channel(channel2_id)
        if isinstance(ch1, discord.VoiceChannel) and isinstance(ch2, discord.VoiceChannel):
            for member in ch1.members:
                if await self.check_permissions(ctx, member):
                    await member.move_to(ch2)

    @commands.command(name='vcmute', aliases=['stfu'])
    async def vcmute(self, ctx, user: discord.Member):
        try: await ctx.message.delete()
        except: pass
        if await self.check_permissions(ctx, user) and user.voice:
            await user.edit(mute=True)

    @commands.command()
    async def vcunmute(self, ctx, member: discord.Member):
        try: await ctx.message.delete()
        except: pass
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.edit(mute=False)

    @commands.command()
    async def vcdeafen(self, ctx, member: discord.Member):
        try: await ctx.message.delete()
        except: pass
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.edit(deafen=True)

    @commands.command()
    async def vcundeafen(self, ctx, member: discord.Member):
        try: await ctx.message.delete()
        except: pass
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.edit(deafen=False)

    @commands.command()
    async def vcmove(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        try: await ctx.message.delete()
        except: pass
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.move_to(channel)

    @commands.command()
    async def vcjoin(self, ctx, channel: discord.VoiceChannel):
        try: await ctx.message.delete()
        except: pass
        await self.bot.ws.send_as_json({
            "op": 4,
            "d": {
                "guild_id": str(ctx.guild.id),
                "channel_id": str(channel.id),
                "self_mute": False,
                "self_deaf": False
            }
        })
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Joined** {channel.mention}")

    @commands.command()
    async def vcleave(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await self.bot.ws.send_as_json({
            "op": 4,
            "d": {
                "guild_id": str(ctx.guild.id) if ctx.guild else None,
                "channel_id": None,
                "self_mute": False,
                "self_deaf": False
            }
        })
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Left VC**")

    @commands.command()
    async def vclimit(self, ctx, limit: int, channel: discord.VoiceChannel = None):
        try: await ctx.message.delete()
        except: pass
        channel = channel or ctx.author.voice.channel
        await channel.edit(user_limit=limit)

    @commands.command()
    async def vccam(self, ctx):
        """Spoofs a fake video/camera session in your current voice channel."""
        try: await ctx.message.delete()
        except: pass
        if not ctx.author.voice:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **You need to be in a VC first!**")
        
        await self.bot.ws.send_as_json({
            "op": 4,
            "d": {
                "guild_id": str(ctx.guild.id) if ctx.guild else None,
                "channel_id": str(ctx.author.voice.channel.id),
                "self_mute": ctx.author.voice.self_mute,
                "self_deaf": ctx.author.voice.self_deaf,
                "self_video": True
            }
        })
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Spoofing Camera in VC!**")

    @commands.command()
    async def vcstream(self, ctx):
        """Spoofs a fake screenshare/Live session in your current voice channel."""
        try: await ctx.message.delete()
        except: pass
        if not ctx.author.voice:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **You need to be in a VC first!**")
        
        await self.bot.ws.send_as_json({
            "op": 4,
            "d": {
                "guild_id": str(ctx.guild.id) if ctx.guild else None,
                "channel_id": str(ctx.author.voice.channel.id),
                "self_mute": ctx.author.voice.self_mute,
                "self_deaf": ctx.author.voice.self_deaf,
                "self_stream": True
            }
        })
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Spoofing Stream (Live) in VC!**")

async def setup(bot):
    await bot.add_cog(Voice(bot))