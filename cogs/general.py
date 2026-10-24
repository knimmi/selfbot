import discord
from discord.ext import commands
import os
import sys
import re
import urllib.parse
import urllib.request
import asyncio
import random
from datetime import datetime, timezone

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, helpcategory="none"):
        try: await ctx.message.delete()
        except: pass
        
        e = self.bot.custom_emojis
        cat = helpcategory.lower().replace("[", "").replace("]", "")
        
        if cat == "none":
            desc = f"""# {e.get('crown', '')} __B A L L Z B O T__ {e.get('crown', '')}

> **{e.get('help', '')} HELP MODULES**
> 
> {e.get('general', '')} **GENERAL SECTION** :- `.help gnrl`
> {e.get('config', '')} **CONFIG SECTION** :- `.help config`
> {e.get('crypto', '')} **CRYPTO SECTION** :- `.help crypto`
> {e.get('spotify', '')} **SPOTIFY SECTION** :- `.help spotify`
> {e.get('remind', '')} **REMINDERS SECTION** :- `.help reminders`
> {e.get('message', '')} **MESSAGE SECTION** :- `.help msg`
> {e.get('ticket', '')} **TICKET SECTION** :- `.help ticket`
> {e.get('status', '')} **STATUS SECTION** :- `.help status`
> {e.get('calc', '')} **CALCULATE SECTION** :- `.help calc`
> {e.get('auto', '')} **AUTO MSG SECTION** :- `.help auto`
> {e.get('vouch', '')} **VOUCH SECTION** :- `.help vouch`
> {e.get('moderation', '')} **MODERATION SECTION** :- `.help mod`
> {e.get('afk', '')} **AFK SECTION** :- `.help afk`
> {e.get('checker', '')} **CHECKER SECTION** :- `.help checker`
> {e.get('image', '')} **IMAGE SECTION** :- `.help image`
> {e.get('fun', '')} **FUN SECTION** :- `.help fun`
> {e.get('vc', '')} **VC SECTION** :- `.help vc`
> {e.get('user', '')} **USER SECTION** :- `.help user`
> {e.get('nsfw', '')} **NSFW SECTION** :- `.help nsfw`
> {e.get('log', '')} **LOGGING SECTION** :- `.help log`

> {e.get('config', '')} **SET PREFIX** :- `.prefix <prefix>`
> {e.get('status', '')} **RISK MODE** :- `.risk`"""
        elif "config" in cat:
            desc = f"""{e.get('crown', '')} **Config Section** {e.get('crown', '')}
{e.get('config', '')} **Set QR Code** :- `.setqr <qr_link>`
{e.get('config', '')} **Set Server Link** :- `.setsrvlink <server_link>`
{e.get('config', '')} **Set User ID** :- `.setuserid [user]`
{e.get('config', '')} **Set LTC Addy** :- `.setaddy <ltc_addy>`
{e.get('config', '')} **Set LTC Addy 2** :- `.setaddy2 <ltc_addy>`
{e.get('config', '')} **Set LTC Key** :- `.setltckey <ltc_key>`
{e.get('config', '')} **Set Dashboard Creds** :- `.setdashcreds <user> <pass>`
{e.get('config', '')} **Customise Emoji** :- `.emoji <name> <emoji>`
{e.get('config', '')} **Toggle Risk Mode** :- `.risk`"""
        elif "gnrl" in cat:
            desc = f"""{e.get('crown', '')} **General Section** {e.get('crown', '')}
{e.get('general', '')} **Show All Commands** :- `.allcmds`
{e.get('general', '')} **Restart Bot** :- `.restart`
{e.get('general', '')} **Server Info** :- `.srvinfo [server_id/link]`
{e.get('general', '')} **Selfbot Info** :- `.selfbot`
{e.get('general', '')} **User Info** :- `.user_info [user_id/@user]`
{e.get('general', '')} **YouTube Search** :- `.ytsearch <title>`
{e.get('general', '')} **(Risk) Abuse** :- `.abuser [user_id/@user]`"""
        elif "spotify" in cat:
            desc = f"""{e.get('crown', '')} **Spotify Section** {e.get('crown', '')}
{e.get('spotify', '')} **Now Playing** :- `.np` (or `.spotify`)
{e.get('spotify', '')} **Skip Track** :- `.skip`
{e.get('spotify', '')} **Pause Playback** :- `.pause`
{e.get('spotify', '')} **Resume Playback** :- `.resume` (or `.play`)
{e.get('spotify', '')} **Top Tracks** :- `.tt`
{e.get('spotify', '')} **Track Lyrics** :- `.lyrics`
{e.get('spotify', '')} **Setup Auth URL** :- `.spsetup`
{e.get('spotify', '')} **Complete Auth** :- `.spauth <url>`"""
        elif "reminders" in cat or "remind" in cat:
            desc = f"""{e.get('crown', '')} **Reminders Section** {e.get('crown', '')}
{e.get('remind', '')} **Set Reminder** :- `.remind <duration> <message>`
{e.get('remind', '')} **List Reminders** :- `.reminders`
{e.get('remind', '')} **Delete Reminder** :- `.delreminder <id>`"""
        elif "ticket" in cat:
            desc = f"""{e.get('crown', '')} **Ticket Section** {e.get('crown', '')}
{e.get('ticket', '')} **Create Ticket** :- `.sc <category_id> <message>`
{e.get('ticket', '')} **Close Ticket** :- `.stopsc <channel_id>`"""
        elif "crypto" in cat:
            desc = f"""{e.get('crown', '')} **Crypto Section** {e.get('crown', '')}
{e.get('ltc', '')} **Send LTC** :- `.send <addy> <amount>`
{e.get('ltc', '')} **Check Balance** :- `.bal <addy>`
{e.get('ltc', '')} **Check My Balance** :- `.mybal`
{e.get('ltc', '')} **Check My Second Balance** :- `.mybal2`
{e.get('ltc', '')} **LTC Addy** :- `.addy`
{e.get('ltc', '')} **Second LTC Addy** :- `.addy2`
{e.get('ltc', '')} **LTC Custom QR** :- `.ltcqr <addy> <eur_amt>`
{e.get('ltc', '')} **Binance ID** :- `.bid`
{e.get('ltc', '')} **Static QR Code** :- `.qr`
{e.get('ltc', '')} **Static QR Code 2** :- `.qr2`
{e.get('ltc', '')} **LTC Price In EUR** :- `.ltc`
{e.get('sol', '')} **SOL Price In EUR** :- `.sol`
{e.get('btc', '')} **BTC Price In EUR** :- `.btc`
{e.get('usdt', '')} **USDC Price In EUR** :- `.usdc`"""
        elif "msg" in cat:
            desc = f"""{e.get('crown', '')} **Message Section** {e.get('crown', '')}
{e.get('message', '')} **(Risk) Spam Msg** :- `.spam <amount> <msg>`
{e.get('message', '')} **(Risk) Clear Msg** :- `.clear <amount>`
{e.get('message', '')} **Direct Msg** :- `.dm <@user> <msg>`
{e.get('message', '')} **Send Msg Ticket Create** :- `.sc <cg-id> <msg>`
{e.get('message', '')} **Remove Msg Ticket Create** :- `.stopsc <cg-id>`
{e.get('message', '')} **Translate Msg** :- `.translate <msg>`
{e.get('message', '')} **(Risk) Dm All In Server** :- `.dmall <msg>`
{e.get('message', '')} **(Risk) Mass Dm Friends** :- `.massdmfriends <msg>`"""
        elif "status" in cat:
            desc = f"""{e.get('crown', '')} **Status Section** {e.get('crown', '')}
{e.get('status', '')} **Custom Status** :- `.status <custom text>`
{e.get('status', '')} **Status Rotator** :- `.rotate <msg> / <msg> / <msg>`
{e.get('status', '')} **Stop Rotator** :- `.stop_rotate`
{e.get('status', '')} **Stream Status** :- `.stream <title> [img_url]`
{e.get('status', '')} **Playing Status** :- `.play <title> [img_url]`
{e.get('status', '')} **Watching Status** :- `.watching <title> [img_url]`
{e.get('status', '')} **Listening Status** :- `.listening <title> [img_url]`
{e.get('status', '')} **Remove Status** :- `.stopactivity`"""
        elif "calc" in cat:
            desc = f"""{e.get('crown', '')} **Calculate Section** {e.get('crown', '')}
{e.get('calc', '')} **Calculate** :- `.math <equation>`
{e.get('calc', '')} **Fiat To Crypto** :- `.f2c <fiat_name> <amount> <crypto_name>`
{e.get('calc', '')} **Crypto To Fiat** :- `.c2f <crypto_name> <amount> <fiat_name>`
{e.get('ltc', '')} **Ltc To EUR** :- `.l2e <ltc amount>`
{e.get('ltc', '')} **EUR To Ltc** :- `.e2l <eur amount>`"""
        elif "auto" in cat:
            desc = f"""{e.get('crown', '')} **Auto Sender Section** {e.get('crown', '')}
{e.get('auto', '')} **Auto Respond** :- `.ar <trigger>, <response>`
{e.get('auto', '')} **Remove Respond** :- `.removear <trigger>`
{e.get('auto', '')} **Auto Respond List** :- `.arlist`
{e.get('auto', '')} **Auto Message** :- `.am <time> [chnl_id] <msg>`
{e.get('auto', '')} **Stop Auto Message** :- `.stopam [chnl_id]`
{e.get('auto', '')} **Auto Message List** :- `.amlist`
{e.get('auto', '')} **Auto Slash** :- `.as <bot_id> <chnl_id> <cmd> <time> [key=val]`
{e.get('auto', '')} **Stop Auto Slash** :- `.asstop [chnl_id]`
{e.get('auto', '')} **Auto Slash List** :- `.aslist`"""
        elif "afk" in cat:
            desc = f"""{e.get('crown', '')} **Afk Section** {e.get('crown', '')}
{e.get('afk', '')} **Toggle AFK** :- `.afk [msg]`
{e.get('afk', '')} **Remove AFK** :- `.unafk`"""
        elif "checker" in cat:
            desc = f"""{e.get('crown', '')} **Checker Section** {e.get('crown', '')}
{e.get('checker', '')} **Check Promo** :- `.checkpromo <promo>`
{e.get('checker', '')} **Check Token** :- `.checktoken <token>`"""
        elif "image" in cat:
            desc = f"""{e.get('crown', '')} **Image Section** {e.get('crown', '')}
{e.get('image', '')} **Get Avatar** :- `.avatar <@user>`
{e.get('image', '')} **Get Icon Of Server** :- `.icon`
{e.get('image', '')} **Get Image** :- `.get_image <query>`"""
        elif "mod" in cat:
            desc = f"""{e.get('crown', '')} **Moderation Section** {e.get('crown', '')}
{e.get('moderation', '')} **Ban** :- `.ban <user> [srv_id]`
{e.get('moderation', '')} **Kick** :- `.kick <user> [srv_id]`
{e.get('moderation', '')} **Unban** :- `.unban <user> [srv_id]`
{e.get('moderation', '')} **Nuke Channel** :- `.nuke [chnl_id]`
{e.get('moderation', '')} **Nuke Server** :- `.nukesrv [srv_id]`
{e.get('moderation', '')} **Hide Channel** :- `.hide [chnl_id]`
{e.get('moderation', '')} **Unhide Channel** :- `.unhide [chnl_id]`
{e.get('moderation', '')} **Lock Channel** :- `.lock [chnl_id]`
{e.get('moderation', '')} **Unlock Channel** :- `.unlock [chnl_id]`
{e.get('moderation', '')} **Delete Channel** :- `.chnldel [chnl_id]`
{e.get('moderation', '')} **Delete Role** :- `.roledel <role_id>`
{e.get('moderation', '')} **Slowmode** :- `.slow <seconds> [chnl_id]`
{e.get('moderation', '')} **Remove Slowmode** :- `.unslow [chnl_id]`
{e.get('moderation', '')} **Create Channel** :- `.chnl <chnl-name>`
{e.get('moderation', '')} **Create Role** :- `.role <role-name>`
{e.get('moderation', '')} **Srv Clone** :- `.csrv <copy id> <target id>`
{e.get('moderation', '')} **Steal Emoji** :- `.steal <emoji> [srv_id]`
{e.get('moderation', '')} **Delete Emoji** :- `.demoji <emoji>`
{e.get('moderation', '')} **AutoMod Add** :- `.mod <trigger> <delete/timeout/ban> [srv_id]`
{e.get('moderation', '')} **AutoMod Del** :- `.delmod <trigger> [srv_id]`"""
        elif "fun" in cat:
            desc = f"""{e.get('crown', '')} **Fun Section** {e.get('crown', '')}
{e.get('fun', '')} **Gen Joke** :- `.joke`
{e.get('fun', '')} **Gen Meme** :- `.meme`
{e.get('fun', '')} **Name** :- `.name <name>`
{e.get('fun', '')} **Fake Nitro** :- `.nitro`
{e.get('fun', '')} **Check Profile** :- `.checkprofile <user>`
{e.get('fun', '')} **Blurpify** :- `.blurpify <user>`
{e.get('fun', '')} **Deepfry** :- `.deepfry <user>`
{e.get('fun', '')} **Fake Captcha** :- `.captcha <user>`
{e.get('fun', '')} **Threat** :- `.threat <user>`
{e.get('fun', '')} **Fake Iphone Gift** :- `.iphone <user>`
{e.get('fun', '')} **Fake Shipping** :- `.ship <user>`"""
        elif "vc" in cat:
            desc = f"""{e.get('crown', '')} **Vc Section** {e.get('crown', '')}
{e.get('vc', '')} **Vc Kick** :- `.vckick <user>`
{e.get('vc', '')} **Vc Move All** :- `.vcmoveall <from chnl id> <to chnl id>`
{e.get('vc', '')} **Vc Mute** :- `.vcmute <user>`
{e.get('vc', '')} **Vc Unmute** :- `.vcunmute <user>`
{e.get('vc', '')} **Vc Deafen** :- `.vcdeafen <user>`
{e.get('vc', '')} **Vc Undeafen** :- `.vcundeafen <user>`
{e.get('vc', '')} **Vc Move** :- `.vcmove <user> <channelid>`
{e.get('vc', '')} **Vc Join** :- `.vcjoin <channelid>`
{e.get('vc', '')} **Vc leave** :- `.vcleave`
{e.get('vc', '')} **Vc Set Limit** :- `.vclimit <limit> <channel-id>`
{e.get('vc', '')} **Vc Stream Spoof** :- `.vcstream`
{e.get('vc', '')} **Vc Camera Spoof** :- `.vccam`
{e.get('vc', '')} **Transcript** :- `.transcript <amt of msg>`"""
        elif "user" in cat:
            desc = f"""{e.get('crown', '')} **User Section** {e.get('crown', '')}
{e.get('user', '')} **Leave Server** :- `.lg [srv_id]`
{e.get('user', '')} **Leave All groups** :- `.leaveallgroups`
{e.get('user', '')} **Delete Friend** :- `.df <user>`
{e.get('user', '')} **Delete All Friends** :- `.delallfriends`
{e.get('user', '')} **Close DM** :- `.close [chnl_id]`
{e.get('user', '')} **Close All Dms** :- `.closealldms`
{e.get('user', '')} **Set Nickname** :- `.setnick [srv_id] <nickname>`
{e.get('user', '')} **Set Bio** :- `.setbio <text>`
{e.get('user', '')} **Set Pronouns** :- `.setpronouns <text>`
{e.get('user', '')} **Set Display Name** :- `.setdisplayname <name>`
{e.get('user', '')} **Set Presence** :- `.presence <online/idle/dnd/offline>`"""
        elif "nsfw" in cat:
            desc = f"""{e.get('crown', '')} **NSFW Section** {e.get('crown', '')}
{e.get('nsfw', '')} **Hass** :- `.hass`
{e.get('nsfw', '')} **Ass** :- `.ass`
{e.get('nsfw', '')} **Boobs** :- `.boobs`
{e.get('nsfw', '')} **lewdneko** :- `.lewdneko`
{e.get('nsfw', '')} **Blowjob** :- `.blowjob`
{e.get('nsfw', '')} **Hentai** :- `.hentai`"""
        elif "vouch" in cat:
            desc = f"""{e.get('crown', '')} **Vouch Section** {e.get('crown', '')}
{e.get('vouch', '')} **Setup Vouch Channel** :- `.setupvouch [chnl_id] <role>`
{e.get('vouch', '')} **Vouch Template** :- `.genvouch <product for price>`
{e.get('vouch', '')} **Exchange Template** :- `.genexch <This for That>`
{e.get('vouch', '')} **Fiat-Crypto Vouch** :- `.genf2c <fiat amt> <crypto amt>`
{e.get('vouch', '')} **Crypto-Fiat Vouch** :- `.genc2f <crypto amt> <fiat amt>`"""
        elif "log" in cat:
            desc = f"""{e.get('crown', '')} **Logging Section** {e.get('crown', '')}
{e.get('log', '')} **Auto Log Setup** :- `.autolog`
{e.get('log', '')} **Set Webhook** :- `.logsetup <category> <url>`
*(Categories: friends, servers, mentions, sessions, guild_updates, keywords)*
{e.get('log', '')} **Add Keyword** :- `.addkw <word>`
{e.get('log', '')} **Remove Keyword** :- `.delkw <word>`
{e.get('log', '')} **List Keywords** :- `.listkw`"""
        else:
            desc = f"{e.get('error', '')} **Module not found:** `{helpcategory}`\nRun `.allcmds` to see all commands."
            
        await ctx.send(desc)

    @commands.command()
    async def allcmds(self, ctx):
        try: await ctx.message.delete()
        except: pass
        categories = ['.help config', '.help gnrl', '.help crypto', '.help spotify', '.help reminders', '.help ticket', '.help vouch', '.help msg', 
                      '.help status', '.help calc', '.help auto', '.help mod', '.help afk', '.help checker', 
                      '.help image', '.help fun', '.help vc', '.help user', '.help nsfw', '.help log']
        for cat in categories:
            await ctx.send(cat)
            await asyncio.sleep(1.2)

    @commands.command()
    async def restart(self, ctx):
        await ctx.reply(f'`-` **{self.bot.custom_emojis.get("check", "")} RESTARTING**')
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command()
    async def selfbot(self, ctx):
        try: await ctx.message.delete()
        except: pass
        
        now = datetime.now(timezone.utc)
        delta = now - self.bot.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        risk_str = "ENABLED" if self.bot.config.get("risk_mode", False) else "DISABLED"

        info = f"""### {self.bot.custom_emojis.get('crown', '')} BallzBot Information
- **Developer:** `knimmi`
- **Uptime:** `{uptime_str}`
- **Commands Executed:** `{self.bot.commands_executed}`
- **Cached Guilds:** `{len(self.bot.guilds)}`
- **Friends:** `{len(self.bot.user.friends)}`
- **Risk Mode:** `{risk_str}`"""
        await ctx.send(info)

    @commands.command(aliases=["srv"])
    async def srvinfo(self, ctx, target: str = None):
        """Shows server info. Target can be a guild ID, an invite link, or blank for current guild."""
        try: await ctx.message.delete()
        except: pass
        
        guild = None
        if target is None:
            guild = ctx.guild
        elif target.isdigit():
            guild = self.bot.get_guild(int(target))
        elif "discord.gg" in target or "discord.com/invite" in target:
            invite_code = target.split("/")[-1]
            try:
                invite = await self.bot.fetch_invite(invite_code)
                guild = invite.guild
            except Exception as e:
                return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid Invite:** {e}")
        
        if not guild:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Server not found.**")

        created = guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        owner = getattr(guild, "owner", f"ID: {getattr(guild, 'owner_id', 'Unknown')}")
        desc = f"""### {self.bot.custom_emojis.get('general', '')} Server Info: {guild.name}
- **Server ID:** `{guild.id}`
- **Created:** `{created}`
- **Owner:** `{owner}`
- **Members:** `{getattr(guild, 'member_count', 'Unknown')}`
- **Icon URL:** {guild.icon.url if guild.icon else 'No Icon'}"""
        await ctx.send(desc)

    @commands.command(aliases=["whois", "ui"])
    async def user_info(self, ctx, user: discord.User = None):
        """Displays user info. Supports @mention, raw ID, or blank (defaults to self)."""
        try: await ctx.message.delete()
        except: pass
        
        target = user or ctx.author
        created = target.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        account_age = (datetime.now(timezone.utc) - target.created_at).days
        
        is_friend = target in self.bot.user.friends
        is_blocked = target in self.bot.user.blocked
        rel_str = "Friend" if is_friend else ("Blocked" if is_blocked else "None")
        
        mutuals = len(target.mutual_guilds) if hasattr(target, "mutual_guilds") else 0
        avatar_url = target.display_avatar.url

        info = f"""### {self.bot.custom_emojis.get('user', '')} User Profile: {target.name}
- **Display Name:** `{target.display_name}`
- **User ID:** `{target.id}`
- **Bot Account?** `{target.bot}`
- **Account Created:** `{created}` (`{account_age}` days ago)
- **Relationship:** `{rel_str}`
- **Mutual Servers:** `{mutuals}`
- **Avatar:** {avatar_url}"""
        await ctx.send(info)

    @commands.command()
    async def ytsearch(self, ctx, *, search: str):
        try: await ctx.message.delete()
        except: pass
        qs = urllib.parse.urlencode({"search_query": search})
        try:
            html = urllib.request.urlopen("http://www.youtube.com/results?" + qs)
            results = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            if results:
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Result for `{search}`:** http://www.youtube.com/watch?v={results[0]}")
            else:
                await ctx.send(f"{self.bot.custom_emojis.get('error', '')} No results found.")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Search error:** {e}")

    @commands.command(aliases=["abuse"])
    async def abuser(self, ctx, user: discord.User = None):
        try: await ctx.message.delete()
        except: pass
        if not self.bot.check_risk(ctx):
            return
        target = user or ctx.author
        abuses = ["teri ma ka bhosda", "maa chuda laude", "bhosdike", "chutiya", "madarchod", "behen ke laude", "gandu", "dumbass", "bhadwe"]
        await ctx.send(f"{target.mention} **{random.choice(abuses)}**")

async def setup(bot):
    await bot.add_cog(General(bot))