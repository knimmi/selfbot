import discord
from discord.ext import commands
import json
import aiohttp

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if "webhooks" not in self.bot.config:
            self.bot.config["webhooks"] = {}
        if "log_toggles" not in self.bot.config:
            self.bot.config["log_toggles"] = {}
        if "keywords" not in self.bot.config:
            self.bot.config["keywords"] = []

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    async def send_log(self, category: str, embed: discord.Embed):
        if not self.bot.config["log_toggles"].get(category, True):
            return
            
        url = self.bot.config["webhooks"].get(category)
        if not url: return

        async with aiohttp.ClientSession() as session:
            try:
                webhook = discord.Webhook.from_url(url, session=session)
                await webhook.send(embed=embed)
            except: pass

    async def route_stalk(self, target_id_1, target_id_2, embed):
        stalk_cfg = self.bot.config.get("stalk", {})
        
        if str(target_id_1) in stalk_cfg:
            ch = self.bot.get_channel(stalk_cfg[str(target_id_1)])
            if ch:
                try: await ch.send(embed=embed)
                except: pass
                
        if target_id_2 and str(target_id_2) in stalk_cfg:
            ch = self.bot.get_channel(stalk_cfg[str(target_id_2)])
            if ch:
                try: await ch.send(embed=embed)
                except: pass

    @commands.command()
    async def logsetup(self, ctx, category: str, url: str):
        try: await ctx.message.delete()
        except: pass
        cat = category.lower()
        self.bot.config["webhooks"][cat] = url
        self.bot.config["log_toggles"][cat] = True
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Log Webhook set for:** `{cat}`")

    @commands.command()
    async def logtoggle(self, ctx, category: str):
        try: await ctx.message.delete()
        except: pass
        cat = category.lower()
        current_state = self.bot.config["log_toggles"].get(cat, True)
        new_state = not current_state
        self.bot.config["log_toggles"][cat] = new_state
        self.save_config()
        status = "ENABLED" if new_state else "DISABLED"
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Logging for `{cat}` is now {status}.**")

    @commands.command()
    @commands.has_permissions(manage_channels=True, manage_webhooks=True)
    async def autolog(self, ctx):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(f"{self.bot.custom_emojis.get('loading', '')} **Setting up Auto Logs...**")
        cat = await ctx.guild.create_category("BallzBot Logs")
        categories = ["friends", "servers", "mentions", "sessions", "nickname", "keywords", "ghost_pings", "edits"]
        for c in categories:
            try:
                ch = await ctx.guild.create_text_channel(c, category=cat)
                wh = await ch.create_webhook(name=f"Logger - {c.capitalize()}")
                self.bot.config["webhooks"][c] = wh.url
                self.bot.config["log_toggles"][c] = True
            except: pass
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Log Setup Complete.**")

    @commands.command()
    async def addkw(self, ctx, *, word: str):
        try: await ctx.message.delete()
        except: pass
        w = word.lower()
        if w not in self.bot.config["keywords"]:
            self.bot.config["keywords"].append(w)
            self.save_config()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Keyword Added:** `{word}`")

    @commands.command()
    async def delkw(self, ctx, *, word: str):
        try: await ctx.message.delete()
        except: pass
        w = word.lower()
        if w in self.bot.config["keywords"]:
            self.bot.config["keywords"].remove(w)
            self.save_config()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Keyword Removed:** `{word}`")

    @commands.command()
    async def listkw(self, ctx):
        try: await ctx.message.delete()
        except: pass
        kws = ", ".join(self.bot.config.get("keywords", []))
        await ctx.send(f"**Tracked Keywords:** {kws or 'None'}")

    @commands.Cog.listener()
    async def on_ready(self):
        embed = discord.Embed(
            title=f"{self.bot.custom_emojis.get('log_session', '✅')} BallzBot V2 Online",
            description="Bot successfully connected to Gateway.",
            color=0x00ff00
        )
        embed.add_field(name="Account Name", value=f"`{self.bot.user.name}`", inline=True)
        embed.add_field(name="Prefix", value=f"`{self.bot.command_prefix}`", inline=True)
        embed.add_field(name="Version", value="`V2.0`", inline=True)
        embed.add_field(name="Friends", value=f"`{len(self.bot.user.friends)}`", inline=True)
        embed.add_field(name="Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        
        if self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
        await self.send_log("sessions", embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_join', '')} Joined Server", description=f"**Name:** {guild.name}\n**ID:** `{guild.id}`\n**Members:** {guild.member_count}", color=0x00ff00)
        await self.send_log("servers", embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_leave', '')} Left Server", description=f"**Name:** {guild.name}\n**ID:** `{guild.id}`", color=0xff0000)
        await self.send_log("servers", embed)

    @commands.Cog.listener()
    async def on_relationship_add(self, relationship):
        if relationship.type == discord.RelationshipType.friend:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_friend_add', '')} Friend Added", description=f"**User:** {relationship.user.name} (`{relationship.user.id}`)", color=0x00ff00)
            await self.send_log("friends", embed)

    @commands.Cog.listener()
    async def on_relationship_remove(self, relationship):
        if relationship.type == discord.RelationshipType.friend:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_friend_rem', '')} Friend Removed", description=f"**User:** {relationship.user.name} (`{relationship.user.id}`)", color=0xff0000)
            await self.send_log("friends", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_nick', '')} Nickname Changed", color=0x00aaff)
            embed.add_field(name="User", value=f"{after.name} (`{after.id}`)", inline=False)
            embed.add_field(name="Server", value=after.guild.name, inline=False)
            embed.add_field(name="Before", value=before.nick or "None", inline=True)
            embed.add_field(name="After", value=after.nick or "None", inline=True)
            await self.send_log("nickname", embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id: return
        
        stalk_cfg = self.bot.config.get("stalk", {})
        if str(message.author.id) in stalk_cfg or str(message.channel.id) in stalk_cfg:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_msg_sent', '')} Message Sent", color=0x36393f)
            embed.add_field(name="Author", value=f"{message.author} (`{message.author.id}`)", inline=False)
            embed.add_field(name="Content", value=message.content or "Embed/Media", inline=False)
            if message.attachments and "image" in str(message.attachments[0].content_type):
                embed.set_image(url=message.attachments[0].url)
            await self.route_stalk(message.author.id, message.channel.id, embed)
        
        if self.bot.user in message.mentions:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_mention', '')} Mention Received", color=0xffff00)
            embed.add_field(name="Author", value=f"{message.author} (`{message.author.id}`)", inline=False)
            loc = f"<#{message.channel.id}> in **{message.guild.name}**" if message.guild else "Direct Message"
            embed.add_field(name="Location", value=loc, inline=False)
            embed.add_field(name="Content", value=message.content or "Embed/Media", inline=False)
            await self.send_log("mentions", embed)

        content_lower = message.content.lower()
        triggered_words = [kw for kw in self.bot.config.get("keywords", []) if kw in content_lower]
        if triggered_words:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_keyword', '')} Keyword Triggered", color=0xff00ff)
            embed.add_field(name="Keyword(s)", value=", ".join(triggered_words), inline=False)
            embed.add_field(name="Author", value=f"{message.author} (`{message.author.id}`)", inline=False)
            loc = f"<#{message.channel.id}> in **{message.guild.name}**" if message.guild else "Direct Message"
            embed.add_field(name="Location", value=loc, inline=False)
            embed.add_field(name="Content", value=message.content, inline=False)
            await self.send_log("keywords", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.id == self.bot.user.id: return
        
        embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_delete', '')} Message Deleted", color=0xff0000)
        embed.add_field(name="Author", value=f"{message.author} (`{message.author.id}`)", inline=False)
        loc = f"<#{message.channel.id}> in **{message.guild.name}**" if message.guild else "Direct Message"
        embed.add_field(name="Location", value=loc, inline=False)
        embed.add_field(name="Content", value=message.content or "No Text", inline=False)
        
        if message.attachments:
            urls = [a.url for a in message.attachments]
            embed.add_field(name="Attachments", value="\n".join(urls), inline=False)
            if message.attachments[0].content_type and "image" in message.attachments[0].content_type:
                embed.set_image(url=message.attachments[0].url)

        await self.route_stalk(message.author.id, message.channel.id, embed)
        
        is_ghost_ping = self.bot.user in message.mentions
        if is_ghost_ping: 
            embed.set_footer(text=f"{self.bot.custom_emojis.get('log_warning', '')} GHOST PING DETECTED")
            await self.send_log("ghost_pings", embed)
        elif message.guild is None: 
            await self.send_log("edits", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.id == self.bot.user.id or before.content == after.content: return
        
        embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_edit', '')} Message Edited", color=0xffaa00)
        embed.add_field(name="Author", value=f"{before.author} (`{before.author.id}`)", inline=False)
        loc = f"<#{before.channel.id}> in **{before.guild.name}**" if before.guild else "Direct Message"
        embed.add_field(name="Location", value=loc, inline=False)
        embed.add_field(name="Before", value=before.content or "None", inline=False)
        embed.add_field(name="After", value=after.content or "None", inline=False)
        
        await self.route_stalk(before.author.id, before.channel.id, embed)
        
        if before.guild is None:
            await self.send_log("edits", embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))