import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import asyncio
import aiohttp

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
                redirect_uri="http://localhost:8080/callback",
                scope="user-read-playback-state user-modify-playback-state user-top-read",
                cache_path=".spotify_cache",
                open_browser=False
            )
            # Auto-login if cache exists
            token = self.sp_oauth.get_cached_token()
            if token:
                self.sp = spotipy.Spotify(auth_manager=self.sp_oauth)

    @commands.command()
    async def spsetup(self, ctx):
        """Generates the Spotify login link for initial setup."""
        try: await ctx.message.delete()
        except: pass
        if not hasattr(self, "sp_oauth"):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Missing Spotify Client ID/Secret in config.json**")
            
        url = self.sp_oauth.get_authorize_url()
        await ctx.send(f"{self.bot.custom_emojis.get('spotify', '')} **Spotify Auth:**\n1. Click here: {url}\n2. Log in and Accept.\n3. Copy the URL of the broken `localhost` page it takes you to.\n4. Run `.spauth <that_url>`")

    @commands.command()
    async def spauth(self, ctx, url: str):
        """Completes the Spotify authentication."""
        try: await ctx.message.delete()
        except: pass
        try:
            code = self.sp_oauth.parse_response_code(url)
            self.sp_oauth.get_access_token(code)
            self.sp = spotipy.Spotify(auth_manager=self.sp_oauth)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Spotify linked successfully.**")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Auth Failed:** {e}")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Run `.spsetup` first.**")
        
        playback = await asyncio.to_thread(self.sp.current_playback)
        if not playback or not playback.get('item'):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Nothing is playing on Spotify right now.**")

        title = playback['item']['name']
        artist = playback['item']['artists'][0]['name']
        album = playback['item']['album']['name']
        url = playback['item']['external_urls']['spotify']
        
        await ctx.send(f"{self.bot.custom_emojis.get('spotify', '')} **Now Playing:** `{title}` by `{artist}`\n**Album:** `{album}`\n{url}")

    @commands.command()
    async def skip(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            await asyncio.to_thread(self.sp.next_track)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Skipped track.**")
        except Exception as e:
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
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error:** {e}")

    @commands.command(aliases=["play"])
    async def resume(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            await asyncio.to_thread(self.sp.start_playback)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Playback resumed.**")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error:** {e}")

    @commands.command()
    async def tt(self, ctx):
        """Shows your top 10 most played tracks."""
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return
        try:
            results = await asyncio.to_thread(self.sp.current_user_top_tracks, limit=10, time_range="short_term")
            msg = f"**{self.bot.custom_emojis.get('spotify', '')} Your Top Tracks (Recent):**\n"
            for idx, track in enumerate(results['items']):
                msg += f"`{idx + 1}.` **{track['name']}** - {track['artists'][0]['name']}\n"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Spotify Error:** {e}")

    @commands.command()
    async def lyrics(self, ctx):
        """Fetches lyrics for the currently playing Spotify song."""
        try: await ctx.message.delete()
        except: pass
        if not self.sp: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Run `.spsetup` first.**")

        playback = await asyncio.to_thread(self.sp.current_playback)
        if not playback or not playback.get('item'):
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Nothing is playing.**")

        title = playback['item']['name']
        artist = playback['item']['artists'][0]['name']
        
        async with aiohttp.ClientSession() as session:
            try:
                # Uses Some-Random-API for lyrics scraping
                async with session.get(f"https://some-random-api.com/lyrics?title={title} {artist}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        lyrics = data.get("lyrics", "")
                        
                        if len(lyrics) > 1900:
                            lyrics = lyrics[:1900] + "\n... (truncated)"
                            
                        await ctx.send(f"**Lyrics for {title} by {artist}:**\n{lyrics}")
                    else:
                        await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Lyrics not found for this track.**")
            except:
                await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Lyrics API failed.**")

async def setup(bot):
    await bot.add_cog(Spotify(bot))