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

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    def save_config(self):
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.bot.config, f, indent=4)
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[save_config] {e}")

    async def send_log(self, category: str, embed: discord.Embed):
        if not self.bot.config["log_toggles"].get(category, True): return
        url = self.bot.config["webhooks"].get(category)
        if not url: return

        async with aiohttp.ClientSession() as session:
            try:
                webhook = discord.Webhook.from_url(url, session=session)
                await webhook.send(embed=embed)
            except Exception as e:
                if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Webhook send_log - {category}] {e}")

    async def route_stalk(self, target_id_1, target_id_2, target_id_3, embed):
        stalk_cfg = self.bot.config.get("stalk", {})
        urls = set()
        
        targets = [str(target_id_1), str(target_id_2), str(target_id_3)]
        for t in targets:
            if t in stalk_cfg and isinstance(stalk_cfg[t], str) and "http" in stalk_cfg[t]:
                urls.add(stalk_cfg[t])

        if not urls: return

        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    webhook = discord.Webhook.from_url(url, session=session)
                    await webhook.send(embed=embed)
                except Exception as e:
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[route_stalk webhook] {e}")

    @commands.command()
    async def logsetup(self, ctx, category: str, url: str):
        try: await ctx.message.delete()
        except: pass
        try:
            cat = category.lower()
            self.bot.config["webhooks"][cat] = url
            self.bot.config["log_toggles"][cat] = True
            self.save_config()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Log Webhook set for:** `{cat}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def logtoggle(self, ctx, category: str):
        try: await ctx.message.delete()
        except: pass
        try:
            cat = category.lower()
            current_state = self.bot.config["log_toggles"].get(cat, True)
            new_state = not current_state
            self.bot.config["log_toggles"][cat] = new_state
            self.save_config()
            status = "ENABLED" if new_state else "DISABLED"
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Logging for `{cat}` is now {status}.**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    @commands.has_permissions(manage_channels=True, manage_webhooks=True)
    async def autolog(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            await ctx.send(f"{self.bot.custom_emojis.get('loading', '')} **Setting up Auto Logs...**")
            
            cat_name = "BallzBot Logs"
            cat = discord.utils.get(ctx.guild.categories, name=cat_name)
            if not cat:
                cat = await ctx.guild.create_category(cat_name)

            categories = ["friends", "servers", "mentions", "sessions", "nickname", "keywords", "ghost_pings", "edits", "giveaways"]
            existing_channels = {ch.name: ch for ch in cat.channels}

            if "guild_updates" in existing_channels and "nickname" not in existing_channels:
                old_ch = existing_channels.pop("guild_updates")
                await old_ch.edit(name="nickname")
                existing_channels["nickname"] = old_ch

            for c in categories:
                try:
                    ch = existing_channels.get(c)
                    if not ch:
                        ch = await ctx.guild.create_text_channel(c, category=cat)
                    
                    wh_list = await ch.webhooks()
                    wh = discord.utils.get(wh_list, name=f"Logger - {c.capitalize()}")
                    
                    if not wh:
                        if c == "nickname":
                            wh = discord.utils.get(wh_list, name="Logger - Guild_updates")
                            if wh: await wh.edit(name="Logger - Nickname")
                            
                        if not wh:
                            wh = await ch.create_webhook(name=f"Logger - {c.capitalize()}")

                    self.bot.config["webhooks"][c] = wh.url
                    self.bot.config["log_toggles"][c] = True
                except Exception as e:
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[autolog] {c} setup failed: {e}")
            
            self.save_config()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Log Setup Complete.**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def addkw(self, ctx, *, word: str):
        try: await ctx.message.delete()
        except: pass
        try:
            w = word.lower()
            if w not in self.bot.config["keywords"]:
                self.bot.config["keywords"].append(w)
                self.save_config()
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Keyword Added:** `{word}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def delkw(self, ctx, *, word: str):
        try: await ctx.message.delete()
        except: pass
        try:
            w = word.lower()
            if w in self.bot.config["keywords"]:
                self.bot.config["keywords"].remove(w)
                self.save_config()
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Keyword Removed:** `{word}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def listkw(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            kws = ", ".join(self.bot.config.get("keywords", []))
            await ctx.send(f"**Tracked Keywords:** {kws or 'None'}")
        except Exception as e: self.log_err(ctx, e)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            embed = discord.Embed(
                title=f"{self.bot.custom_emojis.get('log_session', '')} BallzBot V2 Online",
                description="Bot successfully connected to Gateway.",
                color=0x00ff00
            )
            friends_count = len([r for r in self.bot.relationships if r.type == discord.RelationshipType.friend])
            embed.add_field(name="Account Name", value=f"`{self.bot.user.name}`", inline=True)
            embed.add_field(name="Prefix", value=f"`{self.bot.command_prefix}`", inline=True)
            embed.add_field(name="Version", value="`V2.0`", inline=True)
            embed.add_field(name="Friends", value=f"`{friends_count}`", inline=True)
            embed.add_field(name="Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
            
            if self.bot.user.display_avatar:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                
            await self.send_log("sessions", embed)
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[on_ready log] {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_join', '')} Joined Server", color=0x00ff00)
        embed.add_field(name="Server Name", value=guild.name, inline=False)
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=False)
        embed.add_field(name="Members", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="Boosts", value=f"`{guild.premium_subscription_count}`", inline=True)
        await self.send_log("servers", embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_leave', '')} Left Server", color=0xff0000)
        embed.add_field(name="Server Name", value=guild.name, inline=False)
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=False)
        embed.add_field(name="Members", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="Boosts", value=f"`{guild.premium_subscription_count}`", inline=True)
        await self.send_log("servers", embed)

    @commands.Cog.listener()
    async def on_relationship_add(self, relationship):
        if relationship.type == discord.RelationshipType.friend:
            u = relationship.user
            m_guilds = len(getattr(u, 'mutual_guilds', []))
            m_friends = len(getattr(u, 'mutual_friends', []))
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_friend_add', '')} Friend Added", color=0x00ff00)
            embed.add_field(name="User", value=u.name, inline=True)
            embed.add_field(name="User ID", value=f"`{u.id}`", inline=True)
            embed.add_field(name="Mutual Servers", value=str(m_guilds), inline=True)
            embed.add_field(name="Mutual Friends", value=str(m_friends) if m_friends else "Hidden/0", inline=True)
            embed.add_field(name="Profile Link", value=f"[Open Profile](https://discord.com/users/{u.id})", inline=False)
            if u.display_avatar: embed.set_thumbnail(url=u.display_avatar.url)
            await self.send_log("friends", embed)

    @commands.Cog.listener()
    async def on_relationship_remove(self, relationship):
        if relationship.type == discord.RelationshipType.friend:
            u = relationship.user
            m_guilds = len(getattr(u, 'mutual_guilds', []))
            m_friends = len(getattr(u, 'mutual_friends', []))
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_friend_rem', '')} Friend Removed", color=0xff0000)
            embed.add_field(name="User", value=u.name, inline=True)
            embed.add_field(name="User ID", value=f"`{u.id}`", inline=True)
            embed.add_field(name="Mutual Servers", value=str(m_guilds), inline=True)
            embed.add_field(name="Mutual Friends", value=str(m_friends) if m_friends else "Hidden/0", inline=True)
            embed.add_field(name="Profile Link", value=f"[Open Profile](https://discord.com/users/{u.id})", inline=False)
            if u.display_avatar: embed.set_thumbnail(url=u.display_avatar.url)
            await self.send_log("friends", embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.id == self.bot.user.id: return
        is_friend = any(r.user.id == member.id and r.type == discord.RelationshipType.friend for r in self.bot.relationships)
        if is_friend:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_friend_add', '')} Friend Joined Mutual Server", color=0x00ff00)
            embed.add_field(name="User", value=f"{member.name} (`{member.id}`)", inline=False)
            embed.add_field(name="Server", value=f"{member.guild.name} (`{member.guild.id}`)", inline=False)
            if member.display_avatar: embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_log("friends", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.id == self.bot.user.id: return
        is_friend = any(r.user.id == member.id and r.type == discord.RelationshipType.friend for r in self.bot.relationships)
        if is_friend:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_friend_rem', '')} Friend Left Mutual Server", color=0xff0000)
            embed.add_field(name="User", value=f"{member.name} (`{member.id}`)", inline=False)
            embed.add_field(name="Server", value=f"{member.guild.name} (`{member.guild.id}`)", inline=False)
            if member.display_avatar: embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_log("friends", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.id != self.bot.user.id: return
        
        if before.nick != after.nick:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_nick', '')} My Nickname Changed", color=0x00aaff)
            embed.add_field(name="Server", value=after.guild.name, inline=False)
            embed.add_field(name="Before", value=before.nick or "None", inline=True)
            embed.add_field(name="After", value=after.nick or "None", inline=True)
            await self.send_log("nickname", embed)

        added_roles = [r.name for r in after.roles if r not in before.roles]
        removed_roles = [r.name for r in before.roles if r not in after.roles]
        
        if added_roles or removed_roles:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_role', '')} My Roles Updated", color=0x9b59b6)
            embed.add_field(name="Server", value=after.guild.name, inline=False)
            if added_roles:
                embed.add_field(name="Roles Added", value=", ".join(added_roles), inline=False)
            if removed_roles:
                embed.add_field(name="Roles Removed", value=", ".join(removed_roles), inline=False)
            await self.send_log("servers", embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id: return
        
        guild_id = message.guild.id if message.guild else None
        stalk_cfg = self.bot.config.get("stalk", {})
        
        if str(message.author.id) in stalk_cfg or str(message.channel.id) in stalk_cfg or str(guild_id) in stalk_cfg:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_msg_sent', '')} Message Sent", color=0x36393f)
            embed.add_field(name="Sender", value=f"{message.author} (`{message.author.id}`)", inline=False)
            loc = f"<#{message.channel.id}> in **{message.guild.name}**" if message.guild else "Direct Message"
            embed.add_field(name="Location", value=loc, inline=False)
            embed.add_field(name="Content", value=message.content or "Embed/Media", inline=False)
            if message.attachments:
                img_url = next((a.url for a in message.attachments if "image" in str(a.content_type)), None)
                if img_url: embed.set_image(url=img_url)
            await self.route_stalk(message.author.id, message.channel.id, guild_id, embed)
        
        if self.bot.user in message.mentions:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_mention', '')} Mention Received", color=0xffff00)
            embed.add_field(name="Sender", value=f"{message.author} (`{message.author.id}`)", inline=False)
            loc = f"<#{message.channel.id}> in **{message.guild.name}**" if message.guild else "Direct Message"
            embed.add_field(name="Server", value=loc, inline=False)
            embed.add_field(name="Content", value=message.content or "Embed/Media", inline=False)
            embed.add_field(name="Time", value=message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=True)
            embed.add_field(name="Link", value=f"[Jump to Message]({message.jump_url})", inline=True)
            await self.send_log("mentions", embed)

        content_lower = message.content.lower()
        triggered_words = [kw for kw in self.bot.config.get("keywords", []) if kw in content_lower]
        if triggered_words:
            embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_keyword', '')} Keyword Triggered", color=0xff00ff)
            embed.add_field(name="Keyword(s)", value=", ".join(triggered_words), inline=False)
            embed.add_field(name="Sender", value=f"{message.author} (`{message.author.id}`)", inline=False)
            loc = f"<#{message.channel.id}> in **{message.guild.name}**" if message.guild else "Direct Message"
            embed.add_field(name="Server", value=loc, inline=False)
            embed.add_field(name="Content", value=message.content, inline=False)
            embed.add_field(name="Link", value=f"[Jump to Message]({message.jump_url})", inline=False)
            await self.send_log("keywords", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.id == self.bot.user.id: return
        
        embed = discord.Embed(title=f"{self.bot.custom_emojis.get('log_delete', '')} Message Deleted", color=0xff0000)
        embed.add_field(name="Sender", value=f"{message.author} (`{message.author.id}`)", inline=False)
        loc = f"<#{message.channel.id}> in **{message.guild.name}**" if message.guild else "Direct Message"
        embed.add_field(name="Location", value=loc, inline=False)
        embed.add_field(name="Content", value=message.content or "No Text", inline=False)
        
        if message.attachments:
            urls = [a.url for a in message.attachments]
            embed.add_field(name="Attachments", value="\n".join(urls), inline=False)
            img_url = next((a.url for a in message.attachments if "image" in str(a.content_type)), None)
            if img_url: embed.set_image(url=img_url)

        guild_id = message.guild.id if message.guild else None
        stalk_cfg = self.bot.config.get("stalk", {})
        if str(message.author.id) in stalk_cfg or str(message.channel.id) in stalk_cfg or str(guild_id) in stalk_cfg:
            await self.route_stalk(message.author.id, message.channel.id, guild_id, embed)
        
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
        embed.add_field(name="Sender", value=f"{before.author} (`{before.author.id}`)", inline=False)
        loc = f"<#{before.channel.id}> in **{before.guild.name}**" if before.guild else "Direct Message"
        embed.add_field(name="Location", value=loc, inline=False)
        embed.add_field(name="Before", value=before.content or "None", inline=False)
        embed.add_field(name="After", value=after.content or "None", inline=False)
        
        if before.attachments:
            img_url = next((a.url for a in before.attachments if "image" in str(a.content_type)), None)
            if img_url: embed.set_image(url=img_url)

        guild_id = before.guild.id if before.guild else None
        stalk_cfg = self.bot.config.get("stalk", {})
        if str(before.author.id) in stalk_cfg or str(before.channel.id) in stalk_cfg or str(guild_id) in stalk_cfg:
            await self.route_stalk(before.author.id, before.channel.id, guild_id, embed)
        
        if before.guild is None:
            await self.send_log("edits", embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))