import asyncio
import discord
from discord.ext import commands


class VC(commands.Cog, name="VC"):
    """Global Voice Channel Manager: Join, Leave, 24/7 Stay, Mute/Deaf/Cam/Stream from ANY server or DM."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Guild ID -> {"channel_id": int, "mute": bool, "deaf": bool, "video": bool}
        self.stay_247: dict[int, dict] = {}
        self.reconnect_task: asyncio.Task | None = None

    async def cog_load(self):
        self.reconnect_task = asyncio.create_task(self._keep_alive_loop())

    def cog_unload(self):
        if self.reconnect_task:
            self.reconnect_task.cancel()

    async def _resolve_voice_channel(
        self, ctx: commands.Context, query: str | None = None
    ) -> discord.VoiceChannel | discord.StageChannel | None:
        """Resolve a Voice/Stage channel globally across ALL servers (works from DMs or other servers)."""
        if not query:
            if ctx.guild and isinstance(ctx.author, discord.Member) and ctx.author.voice:
                return ctx.author.voice.channel
            # Check if the user is in a voice channel in ANY mutual guild
            for g in self.bot.guilds:
                member = g.get_member(self.bot.user.id)
                if member and member.voice and member.voice.channel:
                    return member.voice.channel
            return None

        cleaned = query.strip().lstrip("<#").rstrip(">")

        # 1. Try numeric Channel ID globally
        if cleaned.isdigit():
            cid = int(cleaned)
            ch = self.bot.get_channel(cid)
            if ch is None:
                try:
                    ch = await self.bot.fetch_channel(cid)
                except Exception:
                    ch = None
            if isinstance(ch, (discord.VoiceChannel, discord.StageChannel)):
                return ch

        # 2. Try matching by name in current guild first
        q_lower = query.lower().strip()
        if ctx.guild:
            for ch in ctx.guild.voice_channels + ctx.guild.stage_channels:
                if ch.name.lower() == q_lower or q_lower in ch.name.lower():
                    return ch

        # 3. Search across ALL joined servers globally
        for g in self.bot.guilds:
            for ch in g.voice_channels + g.stage_channels:
                if ch.name.lower() == q_lower:
                    return ch
        for g in self.bot.guilds:
            for ch in g.voice_channels + g.stage_channels:
                if q_lower in ch.name.lower():
                    return ch

        return None

    async def _connect_or_state(
        self,
        channel: discord.VoiceChannel | discord.StageChannel,
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
    ):
        """Connect to a voice channel from anywhere using gateway voice state + client connection."""
        guild = channel.guild
        try:
            await guild.change_voice_state(
                channel=channel,
                self_mute=self_mute,
                self_deaf=self_deaf,
                self_video=self_video,
            )
        except Exception:
            # Fallback to VoiceClient.connect if change_voice_state isn't directly supported
            vc = guild.voice_client
            if vc:
                await vc.move_to(channel)
            else:
                await channel.connect(reconnect=True, self_mute=self_mute, self_deaf=self_deaf)

    async def _keep_alive_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                for guild_id, cfg in list(self.stay_247.items()):
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue
                    me = guild.get_member(self.bot.user.id)
                    in_target = me and me.voice and me.voice.channel and me.voice.channel.id == cfg["channel_id"]
                    if not in_target:
                        ch = self.bot.get_channel(cfg["channel_id"])
                        if isinstance(ch, (discord.VoiceChannel, discord.StageChannel)):
                            await self._connect_or_state(
                                ch,
                                self_mute=cfg["mute"],
                                self_deaf=cfg["deaf"],
                                self_video=cfg["video"],
                            )
            except Exception:
                pass
            await asyncio.sleep(15)

    @commands.command(
        name="joinvc",
        aliases=["vcjoin", "jvc", "connect"],
        help="Join any voice channel by ID or name from ANY server or DM. Usage: .joinvc <id/name> [mute] [deaf]",
    )
    async def joinvc(
        self,
        ctx: commands.Context,
        channel_query: str = None,
        mute: bool = False,
        deaf: bool = False,
    ):
        target = await self._resolve_voice_channel(ctx, channel_query)
        if not target:
            return await ctx.send(
                "`[VC]` Could not find that voice channel. Pass a **Voice Channel ID** or exact name.",
                delete_after=7,
            )

        await self._connect_or_state(target, self_mute=mute, self_deaf=deaf)
        await ctx.send(
            f"`[VC]` Joined **{target.name}** in **{target.guild.name}** (`{target.id}`) [Mute: `{mute}` | Deaf: `{deaf}`]",
            delete_after=8,
        )

    @commands.command(
        name="247vc",
        aliases=["vc247", "stayvc"],
        help="Toggle 24/7 auto-reconnect for a voice channel (works from any server or DM).",
    )
    async def vc247(
        self,
        ctx: commands.Context,
        channel_query: str = None,
        mute: bool = True,
        deaf: bool = True,
    ):
        target = await self._resolve_voice_channel(ctx, channel_query)
        if not target:
            return await ctx.send("`[VC]` Specify a valid Voice Channel ID or name.", delete_after=7)

        if target.guild.id in self.stay_247:
            del self.stay_247[target.guild.id]
            return await ctx.send(f"`[VC]` Disabled 24/7 mode for **{target.guild.name}**.", delete_after=7)

        self.stay_247[target.guild.id] = {
            "channel_id": target.id,
            "mute": mute,
            "deaf": deaf,
            "video": False,
        }
        await self._connect_or_state(target, self_mute=mute, self_deaf=deaf)
        await ctx.send(
            f"`[VC]` Enabled 24/7 VC stay in **{target.name}** (**{target.guild.name}**).",
            delete_after=8,
        )

    @commands.command(
        name="leavevc",
        aliases=["vcleave", "lvc", "disconnect"],
        help="Disconnect from voice in the current server, a specified guild ID, or all servers if run in DMs.",
    )
    async def leavevc(self, ctx: commands.Context, guild_id: int = None):
        target_guilds = []
        if guild_id:
            g = self.bot.get_guild(guild_id)
            if g:
                target_guilds.append(g)
        elif ctx.guild:
            me = ctx.guild.get_member(self.bot.user.id)
            if me and me.voice and me.voice.channel:
                target_guilds.append(ctx.guild)

        # If run in DM or not in VC in the current server, find all guilds where the bot is in voice
        if not target_guilds:
            for g in self.bot.guilds:
                me = g.get_member(self.bot.user.id)
                if (me and me.voice and me.voice.channel) or g.voice_client:
                    target_guilds.append(g)

        if not target_guilds:
            return await ctx.send("`[VC]` Not currently connected to any voice channels.", delete_after=6)

        left_names = []
        for g in target_guilds:
            self.stay_247.pop(g.id, None)
            try:
                if g.voice_client:
                    await g.voice_client.disconnect(force=True)
                await g.change_voice_state(channel=None)
                left_names.append(g.name)
            except Exception:
                pass

        await ctx.send(f"`[VC]` Disconnected from voice in: **{', '.join(left_names)}**", delete_after=7)

    @commands.command(name="vcmute", help="Toggle self-mute in your active voice channel.")
    async def vcmute(self, ctx: commands.Context):
        target = await self._resolve_voice_channel(ctx, None)
        if not target:
            return await ctx.send("`[VC]` You are not in a voice channel.", delete_after=6)
        me = target.guild.get_member(self.bot.user.id)
        new_mute = not (me.voice.self_mute if me and me.voice else False)
        deaf = me.voice.self_deaf if me and me.voice else False
        video = me.voice.self_video if me and me.voice else False
        await self._connect_or_state(target, self_mute=new_mute, self_deaf=deaf, self_video=video)
        await ctx.send(f"`[VC]` Self-Mute set to **{new_mute}** in **{target.name}**.", delete_after=6)

    @commands.command(name="vcdeaf", help="Toggle self-deafen in your active voice channel.")
    async def vcdeaf(self, ctx: commands.Context):
        target = await self._resolve_voice_channel(ctx, None)
        if not target:
            return await ctx.send("`[VC]` You are not in a voice channel.", delete_after=6)
        me = target.guild.get_member(self.bot.user.id)
        mute = me.voice.self_mute if me and me.voice else False
        new_deaf = not (me.voice.self_deaf if me and me.voice else False)
        video = me.voice.self_video if me and me.voice else False
        await self._connect_or_state(target, self_mute=mute, self_deaf=new_deaf, self_video=video)
        await ctx.send(f"`[VC]` Self-Deaf set to **{new_deaf}** in **{target.name}**.", delete_after=6)

    @commands.command(name="vccam", aliases=["fakecam"], help="Toggle fake camera indicator in your active voice channel.")
    async def vccam(self, ctx: commands.Context):
        target = await self._resolve_voice_channel(ctx, None)
        if not target:
            return await ctx.send("`[VC]` You are not in a voice channel.", delete_after=6)
        me = target.guild.get_member(self.bot.user.id)
        mute = me.voice.self_mute if me and me.voice else False
        deaf = me.voice.self_deaf if me and me.voice else False
        new_video = not (me.voice.self_video if me and me.voice else False)
        await self._connect_or_state(target, self_mute=mute, self_deaf=deaf, self_video=new_video)
        await ctx.send(f"`[VC]` Fake Camera set to **{new_video}** in **{target.name}**.", delete_after=6)

    @commands.command(name="vcstatus", help="Show all voice channels your account is currently connected to.")
    async def vcstatus(self, ctx: commands.Context):
        active = []
        for g in self.bot.guilds:
            me = g.get_member(self.bot.user.id)
            if me and me.voice and me.voice.channel:
                ch = me.voice.channel
                active.append(
                    f"• {g.name} -> #{ch.name} (ID: {ch.id}) "
                    f"[Mute: {me.voice.self_mute} | Deaf: {me.voice.self_deaf} | Cam: {me.voice.self_video}]"
                )
        if not active:
            return await ctx.send("`[VC]` Not currently in any voice channel.", delete_after=6)
        await ctx.send("```ini\n[Active Voice Connections]\n" + "\n".join(active) + "\n```")


async def setup(bot: commands.Bot):
    await bot.add_cog(VC(bot))