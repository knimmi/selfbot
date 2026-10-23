import discord
from discord.ext import commands
import os, sys, re, urllib.parse, urllib.request, asyncio, random

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
> {e.get('upi', '')} **UPI SECTION** :- `.help upi`
> {e.get('crypto', '')} **CRYPTO SECTION** :- `.help crypto`
> {e.get('message', '')} **MESSAGE SECTION** :- `.help msg`
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
> {e.get('status', '')} **DEVELOPER** :- `knimmi`"""
        elif "config" in cat:
            desc = f"""{e.get('crown', '')} **Config Section** {e.get('crown', '')}
{e.get('config', '')} **Set Upi** :- `.setupi <upi_id>`
{e.get('config', '')} **Set Upi 2** :- `.setupi2 <upi_id2>`
{e.get('config', '')} **Set Qr** :- `.setqr <qr_code>`
{e.get('config', '')} **Set Qr 2** :- `.setqr2 <qr_code2>`
{e.get('config', '')} **Set Server Link** :- `.setsrvlink <link>`
{e.get('config', '')} **Set User Id** :- `.setuserid <id>`
{e.get('config', '')} **Set Ltc Addy** :- `.setaddy <addy>`
{e.get('config', '')} **Set Ltc Addy 2** :- `.setaddy2 <addy2>`
{e.get('config', '')} **Set Binance Id** :- `.setbinid <id>`
{e.get('config', '')} **Set Ltc Key** :- `.setltckey <ltc_key>`"""
        elif "gnrl" in cat:
            desc = f"""{e.get('crown', '')} **General Section** {e.get('crown', '')}
{e.get('general', '')} **Show Allcmds** :- `.allcmds`
{e.get('general', '')} **Restart Bot** :- `.restart`
{e.get('general', '')} **Server Info** :- `.srvinfo`
{e.get('general', '')} **Selfbot Info** :- `.selfbot`
{e.get('general', '')} **User Info** :- `.user_info <@user>`
{e.get('general', '')} **Yt Search** :- `.yt <title-search>`
{e.get('general', '')} **Abuse** :- `.abuse <user>`"""
        elif "crypto" in cat:
            desc = f"""{e.get('crown', '')} **Crypto Section** {e.get('crown', '')}
{e.get('ltc', '')} **Send Ltc** :- `.send <addy> <amount>`
{e.get('ltc', '')} **Check Balance** :- `.bal <addy>`
{e.get('ltc', '')} **Check Mybal** :- `.mybal`
{e.get('ltc', '')} **Second Check Mybal** :- `.mybal2`
{e.get('ltc', '')} **Ltc Addy** :- `.addy`
{e.get('ltc', '')} **Second Ltc Addy** :- `.addy2`
{e.get('ltc', '')} **Ltc Custom Qr** :- `.ltcqr <addy> <usd_amt>`
{e.get('ltc', '')} **Binance ID** :- `.bid`
{e.get('ltc', '')} **Ltc Price In Usd** :- `.ltc`
{e.get('sol', '')} **Sol Price In Usd** :- `.sol`
{e.get('btc', '')} **Btc Price In Usd** :- `.btc`
{e.get('usdt', '')} **Usdt Price In Usd** :- `.usdt`"""
        elif "msg" in cat:
            desc = f"""{e.get('crown', '')} **Message Section** {e.get('crown', '')}
{e.get('message', '')} **Spam Msg** :- `.spam <amount> <msg>`
{e.get('message', '')} **Clear Msg** :- `.clear <amount>`
{e.get('message', '')} **Direct Msg** :- `.dm <@user> <msg>`
{e.get('message', '')} **Send Msg Ticket Create** :- `.sc <cg-id> <msg>`
{e.get('message', '')} **Remove Msg Ticket Create** :- `.stopsc <cg-id>`
{e.get('message', '')} **Translate Msg** :- `.translate <msg>`
{e.get('message', '')} **Dm All In Server** :- `.dmall <msg>`
{e.get('message', '')} **Mass Dm Friends** :- `.massdmfrnds <msg>`"""
        elif "status" in cat:
            desc = f"""{e.get('crown', '')} **Status Section** {e.get('crown', '')}
{e.get('status', '')} **Status Rotator** :- `.rotate <emoji id , msg> / <emoji id , msg> / <repeat again>`
{e.get('status', '')} **Stop Rotator** :- `.stop_rotate`
{e.get('status', '')} **Stream Status** :- `.stream <title>`
{e.get('status', '')} **Playing Status** :- `.play <title>`
{e.get('status', '')} **Watching Status** :- `.watching <title>`
{e.get('status', '')} **Listening Status** :- `.listening <title>`
{e.get('status', '')} **Custom Status** :- `.status <custom text>`
{e.get('status', '')} **Presence** :- `.presence <dnd,idle etc.>`
{e.get('status', '')} **Remove Status** :- `.stopactivity`"""
        elif "calc" in cat:
            desc = f"""{e.get('crown', '')} **Calculate Section** {e.get('crown', '')}
{e.get('calc', '')} **Calculate** :- `.math <equation>`
{e.get('calc', '')} **Inr To Crypto** :- `.i2c <inr amount>`
{e.get('calc', '')} **Crypto To Inr** :- `.c2i <crypto amount>`
{e.get('ltc', '')} **Ltc To Usd** :- `.l2u <ltc amount>`
{e.get('ltc', '')} **Usd To Ltc** :- `.u2l <usd amount>`"""
        elif "auto" in cat:
            desc = f"""{e.get('crown', '')} **Auto Sender Section** {e.get('crown', '')}
{e.get('auto', '')} **AutoRespond** :- `.ar <trigger>, <response>`
{e.get('auto', '')} **Remove Respond** :- `.removear <triger>`
{e.get('auto', '')} **AutoRespond List** :- `.ar_list`
{e.get('auto', '')} **AutoMsg** :- `.am <time> <chnl_id> <msg>`
{e.get('auto', '')} **Stop AutoMsg** :- `.am_stop <chnl_id>`
{e.get('auto', '')} **AutoMsg List** :- `.am_list`"""
        elif "afk" in cat:
            desc = f"""{e.get('crown', '')} **Afk Section** {e.get('crown', '')}
{e.get('afk', '')} **Afk** :- `.afk <reason>`
{e.get('afk', '')} **Remove Afk** :- `.unafk`"""
        elif "checker" in cat:
            desc = f"""{e.get('crown', '')} **Checker Section** {e.get('crown', '')}
{e.get('checker', '')} **Check Promo** :- `.checkpromo <promo>`
{e.get('checker', '')} **Check Token** :- `.checktoken <token>`"""
        elif "image" in cat:
            desc = f"""{e.get('crown', '')} **Image Section** {e.get('crown', '')}
{e.get('image', '')} **Get Avatar** :- `.avatar <@user>`
{e.get('image', '')} **Get Icon Of Server** :- `.icon`
{e.get('image', '')} **Get Image** :- `.get_image <query>`"""
        elif "upi" in cat:
            desc = f"""{e.get('crown', '')} **Upi Section** {e.get('crown', '')}
{e.get('upi', '')} **Upi Id** :- `.upi`
{e.get('upi', '')} **Second Upi Id** :- `.upi2`
{e.get('upi', '')} **Qr Code** :- `.qr`
{e.get('upi', '')} **Second Qr Code** :- `.qr2`
{e.get('upi', '')} **Custom Qr** :- `.cqr <amt> <note>`"""
        elif "mod" in cat:
            desc = f"""{e.get('crown', '')} **Moderation Section** {e.get('crown', '')}
{e.get('moderation', '')} **Ban** :- `.ban <user>`
{e.get('moderation', '')} **Kick** :- `.kick <user>`
{e.get('moderation', '')} **Ban Id** :- `.banid <userid>`
{e.get('moderation', '')} **Unban Id** :- `.unban <userid>`
{e.get('moderation', '')} **Nuke Channel** :- `.nuke`
{e.get('moderation', '')} **Nuke Server** :- `.nukesrv`
{e.get('moderation', '')} **Hide** :- `.hide`
{e.get('moderation', '')} **Unhide** :- `.unhide`
{e.get('moderation', '')} **Create Channel** :- `.chnl <chnl-name>`
{e.get('moderation', '')} **Create Role** :- `.role <role-name>`
{e.get('moderation', '')} **Srv Clone** :- `.csrv <copy id> <target id>`
{e.get('moderation', '')} **Steal Emoji** :- `.steal <emoji> [server_id] [name]`"""
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
{e.get('user', '')} **Leave All groups** :- `.leaveallgroups`
{e.get('user', '')} **Delete Friends** :- `.delallfriends`
{e.get('user', '')} **Close All Dms** :- `.closealldms`
{e.get('user', '')} **Set Nickname** :- `.setnick <server_id> <nickname>`
{e.get('user', '')} **Set Bio** :- `.setbio <text>`
{e.get('user', '')} **Set Pronouns** :- `.setpronouns <text>`
{e.get('user', '')} **Set Display Name** :- `.setdisplayname <name>`"""
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
{e.get('vouch', '')} **Vouch** :- `.vouch <product for much>`
{e.get('vouch', '')} **Exchange Vouch** :- `.exch <This To This>`
{e.get('vouch', '')} **I2c Vouch** :- `.i2cvouch <inr amt> <ltc amt>`
{e.get('vouch', '')} **C2i Vouch** :- `.c2ivouch <ltc amt> <inr amt>`"""
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
        categories = ['.help config', '.help gnrl', '.help upi', '.help crypto', '.help vouch', '.help msg', 
                      '.help status', '.help calc', '.help auto', '.help mod', '.help afk', '.help checker', 
                      '.help image', '.help fun', '.help vc', '.help user', '.help nsfw', '.help log']
        for cat in categories:
            await ctx.send(cat)
            await asyncio.sleep(1.5)

    @commands.command()
    async def restart(self, ctx):
        await ctx.reply(f'`-` **{self.bot.custom_emojis.get("check", "")} RESTARTING**')
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command()
    async def selfbot(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send('**SELFBOT DETAILS**\n- NAME > Knimmi SelfBot\n- VERSION > 1\n- DEVELOPER > `Knimmi`')

    @commands.command()
    async def srvinfo(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"**SERVER NAME** : __`{ctx.guild.name}`__\n`-` **ID** : `{ctx.guild.id}`\n`-` **CREATION** : `{ctx.guild.created_at}`\n`-` **OWNER** : `<@{ctx.guild.owner_id}>`")

    @commands.command()
    async def user_info(self, ctx, user: discord.User):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"## User Info\n- **Name**: `{user.name}`\n- **Display**: `{user.display_name}`\n- **ID**: `{user.id}`\n- **Avatar**: {user.display_avatar.url}")

    @commands.command()
    async def yt(self, ctx, *, search=''):
        try: await ctx.message.delete()
        except: pass
        if search == '': return await ctx.send(f'{self.bot.custom_emojis.get("error", "")} `PROVIDE A REQUEST...`')
        qs = urllib.parse.urlencode({"search_query": search})
        html = urllib.request.urlopen("http://www.youtube.com/results?" + qs)
        results = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        if results:
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')}\n`-` **URL** : http://www.youtube.com/watch?v={results[0]}")

    @commands.command()
    async def abuse(self, ctx, member: discord.Member = None):
        try: await ctx.message.delete()
        except: pass
        member = member or ctx.author
        abuses = ["teri ma ka bhosda", "maa chuda laude", "bhosdike", "chutiya", "madarchod", "behen ke laude", "gandu", "dumbass", "nigga", "bhadwe"]
        await ctx.send(f"{member.mention} **{random.choice(abuses)}**")

    # --- VOUCH COMMANDS ---
    @commands.command()
    async def exch(self, ctx, *, text):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f'+rep {self.bot.config.get("User_Id")} {text}\n{self.bot.config.get("SERVER_Link")}\n**PLEASE VOUCH ME HERE**')

    @commands.command()
    async def vouch(self, ctx, *, text):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f'+rep {self.bot.config.get("User_Id")} {text}\n{self.bot.config.get("SERVER_Link")}\n**PLEASE VOUCH ME HERE**')

    @commands.command()
    async def i2cvouch(self, ctx, inr, inr2):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f'+rep {self.bot.config.get("User_Id")} {inr} UPI TO {inr2} LTC\n{self.bot.config.get("SERVER_Link")}\n**PLEASE VOUCH ME HERE**')

    @commands.command()
    async def c2ivouch(self, ctx, inr, inr2):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f'+rep {self.bot.config.get("User_Id")} {inr} LTC TO {inr2} UPI\n{self.bot.config.get("SERVER_Link")}\n**PLEASE VOUCH ME HERE**')

async def setup(bot):
    await bot.add_cog(General(bot))