import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import asyncio
import aiohttp
from collections import Counter

class Spotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = None
        
        client_id = self.bot.config.get("spotify_client_id")
        client_secret = self.bot.config.get("spotify_client_secret")
        
        if client_id and client_secret:
            self.sp_oauth = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri="https://self.knimmi.de/callback",
                scope="user-read-playback-state user-modify-playback-state user-top-read user-read-recently-played",
                cache_path=".spotify_cache",
                open_browser=False
            )
            token = self.sp_oauth.get_cached_token()
            if token:
                self.sp = spotipy.Spotify(auth_manager=self.sp_oauth)

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] Spotify Error: {e}")

    @commands.command()
    async def spsetup(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not hasattr(self, "sp_oauth"):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Missing Spotify Client ID/Secret in config.json**")
            
        url = self.sp_oauth.get_authorize_url()
        await ctx.send(f"{self.bot.custom_emojis.get('spotify', '')} **Spotify Auth:**\n1. Click here: {url}\n2. Log in and Accept.\n3. Copy the URL of the broken `localhost` page it takes you to.\n4. Run `.spauth <that_url>`")

    @commands.command()
    async def spauth(self, ctx, url: str):
        try: await ctx.message.delete()
        except: pass
        try:
            code = self.sp_oauth.parse_response_code(url)
            self.sp_oauth.get_access_token(code)
            self.sp = spotipy.Spotify(auth_manager=self.sp_oauth)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Spotify linked successfully.**")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Auth Failed:** {e}")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Run `.spsetup` first.**")
        
        try:
            playback = await asyncio.to_thread(self.sp.current_playback)
            if not playback or not playback.get('item'):
                return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Nothing is playing on Spotify right now.**")

            title = playback['item'].get('name', 'Unknown Title')
            artist = playback['item']['artists'][0].get('name', 'Unknown Artist') if playback['item'].get('artists') else 'Unknown Artist'
            album = playback['item']['album'].get('name', 'Unknown Album') if playback['item'].get('album') else 'Unknown Album'
            url = playback['item']['external_urls'].get('spotify', '') if playback['item'].get('external_urls') else ''
            
            await ctx.send(f"{self.bot.custom_emojis.get('spotify', '')} **Now Playing:** `{title}` by `{artist}`\n**Album:** `{album}`\n{url}")
        except Exception as e:
            self.log_err(ctx, e)

    @commands.command()
    async def skip(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            await asyncio.to_thread(self.sp.next_track)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Skipped track.**")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error:** {e}")

    @commands.command()
    async def pause(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            await asyncio.to_thread(self.sp.pause_playback)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Playback paused.**")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error:** {e}")

    @commands.command(aliases=["splay"])
    async def resume(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            await asyncio.to_thread(self.sp.start_playback)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Playback resumed.**")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error:** {e}")

    @commands.command()
    async def rt(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            results = await asyncio.to_thread(self.sp.current_user_recently_played, limit=10)
            msg = f"**{self.bot.custom_emojis.get('spotify', '')} Recently Played:**\n"
            for idx, item in enumerate(results.get('items', [])):
                track = item.get('track', {})
                name = track.get('name', 'Unknown Track')
                artist = track['artists'][0].get('name', 'Unknown Artist') if track.get('artists') else 'Unknown Artist'
                msg += f"`{idx + 1}.` **{name}** - {artist}\n"
            await ctx.send(msg)
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error.** Check logs.")

    @commands.command()
    async def tt(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            results = await asyncio.to_thread(self.sp.current_user_top_tracks, limit=10, time_range="short_term")
            msg = f"**{self.bot.custom_emojis.get('spotify', '')} Top Tracks (Last 4 Weeks):**\n"
            for idx, track in enumerate(results.get('items', [])):
                name = track.get('name', 'Unknown Track')
                artist = track['artists'][0].get('name', 'Unknown Artist') if track.get('artists') else 'Unknown Artist'
                popularity = track.get('popularity', 'N/A')
                msg += f"`{idx + 1}.` **{name}** - {artist} *(Pop: {popularity}/100)*\n"
            await ctx.send(msg)
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error.** Check logs.")

    @commands.command()
    async def ta(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            results = await asyncio.to_thread(self.sp.current_user_top_artists, limit=10, time_range="short_term")
            msg = f"**{self.bot.custom_emojis.get('spotify', '')} Top Artists (Last 4 Weeks):**\n"
            for idx, artist in enumerate(results.get('items', [])):
                msg += f"`{idx + 1}.` **{artist.get('name', 'Unknown Artist')}**\n"
            await ctx.send(msg)
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error.** Check logs.")

    @commands.command()
    async def tg(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            results = await asyncio.to_thread(self.sp.current_user_top_artists, limit=50, time_range="short_term")
            genres = []
            for artist in results.get('items', []):
                genres.extend(artist.get('genres', []))
            
            if not genres:
                return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Not enough data to calculate top genres.**")
                
            top_genres = Counter(genres).most_common(10)
            msg = f"**{self.bot.custom_emojis.get('spotify', '')} Top Genres (Last 4 Weeks):**\n"
            for idx, (genre, count) in enumerate(top_genres):
                msg += f"`{idx + 1}.` **{genre.title()}**\n"
            await ctx.send(msg)
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error.** Check logs.")

    @commands.command()
    async def lyrics(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Run `.spsetup` first.**")

        try:
            playback = await asyncio.to_thread(self.sp.current_playback)
            if not playback or not playback.get('item'):
                return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Nothing is playing.**")

            title = playback['item'].get('name', '')
            artist = playback['item']['artists'][0].get('name', '') if playback['item'].get('artists') else ''
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://some-random-api.com/lyrics?title={title} {artist}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        lyrics = data.get("lyrics", "")
                        if len(lyrics) > 1900:
                            lyrics = lyrics[:1900] + "\n... (truncated)"
                        await ctx.send(f"**Lyrics for {title} by {artist}:**\n{lyrics}")
                    else:
                        await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Lyrics not found for this track.**")
        except Exception as e:
            self.log_err(ctx, e)
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Lyrics API failed.**")

async def setup(bot):
    await bot.add_cog(Spotify(bot))