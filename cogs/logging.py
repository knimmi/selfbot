import discord
from discord.ext import commands
import json
import aiohttp
from datetime import datetime
import asyncio

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Ensure our config file has the required structures
        if "webhooks" not in self.bot.config:
            self.bot.config["webhooks"] = {}
        if "keywords" not in self.bot.config:
            self.bot.config["keywords"] = []

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    async def send_log(self, category: str, embed: discord.Embed):
        webhook_url = self.bot.config["webhooks"].get(category)
        if not webhook_url:
            return

        embed.timestamp = datetime.utcnow()
        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(webhook_url, session=session)
                await webhook.send(
                    embed=embed, 
                    username="BallzBot Logger", 
                    avatar_url=self.bot.user.display_avatar.url
                )
        except Exception as e:
            print(f"Failed to send {category} log: {e}")

    # --- COMMANDS ---

    @commands.command()
    @commands.has_permissions(manage_channels=True, manage_webhooks=True)
    async def autolog(self, ctx):
        """Automatically builds the logging category, channels, and webhooks."""
        try: await ctx.message.delete()
        except: pass
        
        await ctx.send(f"{self.bot.custom_emojis.get('log', '')} **Setting up auto-logging... Please wait.**")
        
        try:
            # Create the master category
            cat = await ctx.guild.create_category("Webhook Logs")
            categories = ["friends", "servers", "mentions", "sessions", "guild_updates", "keywords"]
            
            for cat_name in categories:
                # Create the channel and webhook
                ch = await ctx.guild.create_text_channel(cat_name, category=cat)
                wh = await ch.create_webhook(name=f"{cat_name.capitalize()}")
                # Save to config
                self.bot.config["webhooks"][cat_name] = wh.url
                await asyncio.sleep(1.5) # Avoid Discord API rate limits
                
            self.save_config()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto-Logging Setup Complete!** Check the new channels below.")
            
        except discord.Forbidden:
            await ctx.send(f"{self.bot.custom_emojis.get('arrow', '')} **Error:** I need `Manage Channels` and `Manage Webhooks` permissions in this server to do that.")
        except Exception as e:
            await ctx.send(f"{self.bot.custom_emojis.get('arrow', '')} **Error during setup:** {e}")

    @commands.command()
    async def logsetup(self, ctx, category: str, url: str):
        """Manually map a webhook to a specific category."""
        try: await ctx.message.delete()
        except: pass
        valid_cats = ["friends", "servers", "mentions", "sessions", "guild_updates", "keywords"]
        if category.lower() not in valid_cats:
            await ctx.send(f"{self.bot.custom_emojis.get('arrow', '')} **Invalid Category!** Use: `{', '.join(valid_cats)}`")
            return
        
        self.bot.config["webhooks"][category.lower()] = url
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **{category.capitalize()}** logging webhook configured!")

    @commands.command()
    async def addkw(self, ctx, *, word: str):
        try: await ctx.message.delete()
        except: pass
        if word.lower() not in [kw.lower() for kw in self.bot.config["keywords"]]:
            self.bot.config["keywords"].append(word)
            self.save_config()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Added keyword: `{word}`")
        else:
            await ctx.send(f"{self.bot.custom_emojis.get('arrow', '')} Keyword already exists.")

    @commands.command()
    async def delkw(self, ctx, *, word: str):
        try: await ctx.message.delete()
        except: pass
        self.bot.config["keywords"] = [kw for kw in self.bot.config["keywords"] if kw.lower() != word.lower()]
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Removed keyword: `{word}`")

    @commands.command()
    async def listkw(self, ctx):
        try: await ctx.message.delete()
        except: pass
        kws = ", ".join(f"`{k}`" for k in self.bot.config["keywords"]) or "None"
        await ctx.send(f"{self.bot.custom_emojis.get('log', '')} **Tracked Keywords:** {kws}")

    # --- EVENTS ---

    # 1. Friend Updates
    @commands.Cog.listener()
    async def on_relationship_add(self, relationship):
        rt = relationship.type
        user = relationship.user
        e_user = self.bot.custom_emojis.get("user", "")
        e_check = self.bot.custom_emojis.get("check", "")
        e_mod = self.bot.custom_emojis.get("moderation", "")
        
        if rt == discord.RelationshipType.incoming_request:
            title = f"{e_user} Incoming Friend Request"
            color = 0xF1C40F
        elif rt == discord.RelationshipType.outgoing_request:
            title = f"{e_user} Sent Friend Request"
            color = 0x3498DB
        elif rt == discord.RelationshipType.friend:
            title = f"{e_check} New Friend Added"
            color = 0x2ECC71
        elif rt == discord.RelationshipType.blocked:
            title = f"{e_mod} User Blocked"
            color = 0xE74C3C
        else:
            return

        embed = discord.Embed(title=title, description=f"**User:** {user.mention} (`{user.name}` | `{user.id}`)", color=color)
        await self.send_log("friends", embed)

    @commands.Cog.listener()
    async def on_relationship_remove(self, relationship):
        rt = relationship.type
        user = relationship.user
        e_arrow = self.bot.custom_emojis.get("arrow", "")
        e_check = self.bot.custom_emojis.get("check", "")
        
        if rt == discord.RelationshipType.friend:
            title = f"{e_arrow} Friend Removed"
        elif rt == discord.RelationshipType.blocked:
            title = f"{e_check} User Unblocked"
        elif rt == discord.RelationshipType.incoming_request:
            title = f"{e_arrow} Incoming Request Cancelled/Ignored"
        elif rt == discord.RelationshipType.outgoing_request:
            title = f"{e_arrow} Outgoing Request Cancelled"
        else:
            title = f"{e_arrow} Relationship Removed: {rt.name}"

        embed = discord.Embed(title=title, description=f"**User:** {user.mention} (`{user.name}` | `{user.id}`)", color=0x95A5A6)
        await self.send_log("friends", embed)

    # 2. Server Updates
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        e_gen = self.bot.custom_emojis.get("general", "")
        embed = discord.Embed(title=f"{e_gen} Joined Server", description=f"**Name:** {guild.name}\n**ID:** `{guild.id}`\n**Members:** {guild.member_count}", color=0x2ECC71)
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        await self.send_log("servers", embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        e_arrow = self.bot.custom_emojis.get("arrow", "")
        embed = discord.Embed(title=f"{e_arrow} Left/Kicked from Server", description=f"**Name:** {guild.name}\n**ID:** `{guild.id}`", color=0xE74C3C)
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        await self.send_log("servers", embed)

    # 3. Mentions, Ghost Pings & Keywords
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id:
            return

        e_msg = self.bot.custom_emojis.get("message", "")
        e_log = self.bot.custom_emojis.get("log", "")

        # Check Mentions (Pings)
        if self.bot.user in message.mentions:
            embed = discord.Embed(title=f"{e_msg} You Were Mentioned", description=message.content, color=0xF1C40F)
            embed.add_field(name="Author", value=f"{message.author.mention} (`{message.author.id}`)")
            embed.add_field(name="Location", value=f"{message.channel.mention} in `{message.guild.name if message.guild else 'DMs'}`")
            embed.add_field(name="Jump", value=f"[Click Here]({message.jump_url})", inline=False)
            await self.send_log("mentions", embed)

        # Check Keywords
        tracked_kws = self.bot.config["keywords"]
        if tracked_kws and message.content:
            content_lower = message.content.lower()
            found_kws = [kw for kw in tracked_kws if kw.lower() in content_lower]
            if found_kws:
                embed = discord.Embed(title=f"{e_log} Keyword Triggered", description=message.content, color=0x9B59B6)
                embed.add_field(name="Keyword(s)", value=", ".join(found_kws))
                embed.add_field(name="Author", value=f"{message.author.mention}")
                embed.add_field(name="Location", value=f"{message.channel.mention} in `{message.guild.name if message.guild else 'DMs'}`")
                embed.add_field(name="Jump", value=f"[Click Here]({message.jump_url})", inline=False)
                await self.send_log("keywords", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        e_msg = self.bot.custom_emojis.get("message", "")
        
        # Ghost Ping via Deletion
        if self.bot.user in message.mentions and message.author.id != self.bot.user.id:
            embed = discord.Embed(title=f"{e_msg} Ghost Ping (Message Deleted)", description=message.content, color=0xE91E63)
            embed.add_field(name="Author", value=f"{message.author.mention} (`{message.author.id}`)")
            embed.add_field(name="Location", value=f"{message.channel.mention} in `{message.guild.name if message.guild else 'DMs'}`")
            await self.send_log("mentions", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        e_msg = self.bot.custom_emojis.get("message", "")
        
        # Ghost Ping via Edit (Mention removed)
        if self.bot.user in before.mentions and self.bot.user not in after.mentions and before.author.id != self.bot.user.id:
            embed = discord.Embed(title=f"{e_msg} Ghost Ping (Mention Removed)", color=0xE91E63)
            embed.add_field(name="Before", value=before.content or "*Empty*", inline=False)
            embed.add_field(name="After", value=after.content or "*Empty*", inline=False)
            embed.add_field(name="Author", value=f"{before.author.mention}")
            embed.add_field(name="Location", value=f"{before.channel.mention}")
            await self.send_log("mentions", embed)

    # 4. Role & Nickname Changes (Guild Updates)
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.id != self.bot.user.id:
            return 

        e_cfg = self.bot.custom_emojis.get("config", "")

        # Nickname Change
        if before.nick != after.nick:
            embed = discord.Embed(title=f"{e_cfg} Nickname Changed", color=0x3498DB)
            embed.add_field(name="Server", value=f"{before.guild.name} (`{before.guild.id}`)")
            embed.add_field(name="Old Nick", value=before.nick or "*None*")
            embed.add_field(name="New Nick", value=after.nick or "*None*")
            await self.send_log("guild_updates", embed)

        # Role Change
        if before.roles != after.roles:
            added = [r.name for r in after.roles if r not in before.roles]
            removed = [r.name for r in before.roles if r not in after.roles]
            if added or removed:
                embed = discord.Embed(title=f"{e_cfg} Roles Changed", color=0x3498DB)
                embed.add_field(name="Server", value=f"{before.guild.name} (`{before.guild.id}`)", inline=False)
                if added: embed.add_field(name="Added", value=", ".join(added))
                if removed: embed.add_field(name="Removed", value=", ".join(removed))
                await self.send_log("guild_updates", embed)

    # 5. Session Logging
    @commands.Cog.listener()
    async def on_ready(self):
        e_stat = self.bot.custom_emojis.get("status", "")
        embed = discord.Embed(title=f"{e_stat} Session Ready", description=f"Successfully logged in as `{self.bot.user}`", color=0x2ECC71)
        await self.send_log("sessions", embed)

    @commands.Cog.listener()
    async def on_connect(self):
        e_stat = self.bot.custom_emojis.get("status", "")
        embed = discord.Embed(title=f"{e_stat} Gateway Connected", description="Established connection to Discord Gateway.", color=0x3498DB)
        await self.send_log("sessions", embed)

    @commands.Cog.listener()
    async def on_disconnect(self):
        e_stat = self.bot.custom_emojis.get("status", "")
        embed = discord.Embed(title=f"{e_stat} Gateway Disconnected", description="Lost connection to Discord Gateway.", color=0xE74C3C)
        await self.send_log("sessions", embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))