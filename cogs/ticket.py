import discord
from discord.ext import commands
import json
import os

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if "tickets" not in self.bot.config:
            self.bot.config["tickets"] = {}

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    def get_cfg(self, guild_id):
        gid = str(guild_id)
        if gid not in self.bot.config["tickets"]:
            self.bot.config["tickets"][gid] = {
                "setup_msg_id": None,
                "role_id": None,
                "log_id": None,
                "msg_setup": "React below to open a ticket.",
                "msg_inside": "Welcome to your ticket! Support will be with you shortly.",
                "active": {}
            }
        return self.bot.config["tickets"][gid]

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def streact(self, ctx, emoji: str):
        try: await ctx.message.delete()
        except: pass
        self.bot.custom_emojis["ticket_react"] = emoji
        with open("emojis.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.custom_emojis, f, indent=4)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Ticket reaction set to:** {emoji}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def strole(self, ctx, role_id: int):
        try: await ctx.message.delete()
        except: pass
        cfg = self.get_cfg(ctx.guild.id)
        cfg["role_id"] = role_id
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Support Role Set:** `<@&{role_id}>`")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def stlog(self, ctx, channel_id: int):
        try: await ctx.message.delete()
        except: pass
        cfg = self.get_cfg(ctx.guild.id)
        cfg["log_id"] = channel_id
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Log Channel Set:** <#{channel_id}>")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def stmsgsetup(self, ctx, *, msg: str):
        try: await ctx.message.delete()
        except: pass
        cfg = self.get_cfg(ctx.guild.id)
        cfg["msg_setup"] = msg
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Setup Message Updated.**")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def stmsginside(self, ctx, *, msg: str):
        try: await ctx.message.delete()
        except: pass
        cfg = self.get_cfg(ctx.guild.id)
        cfg["msg_inside"] = msg
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Inside Message Updated.**")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setupticket(self, ctx, channel: discord.TextChannel):
        try: await ctx.message.delete()
        except: pass
        cfg = self.get_cfg(ctx.guild.id)
        
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        msg = await channel.send(f"{self.bot.custom_emojis.get('ticket', '')} {cfg['msg_setup']}")
        
        react_emoji = self.bot.custom_emojis.get("ticket_react")
        if react_emoji: await msg.add_reaction(react_emoji)
        
        cfg["setup_msg_id"] = msg.id
        self.save_config()
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Ticket Panel deployed in {channel.mention}**")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id or not payload.guild_id:
            return

        cfg = self.bot.config.get("tickets", {}).get(str(payload.guild_id))
        if not cfg or payload.message_id != cfg.get("setup_msg_id"):
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        
        try:
            msg = await channel.fetch_message(payload.message_id)
            member = guild.get_member(payload.user_id)
            await msg.remove_reaction(payload.emoji, member)
        except: pass

        if str(member.id) in cfg.get("active", {}):
            return 

        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        if cfg.get("role_id"):
            role = guild.get_role(cfg["role_id"])
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        t_ch = await guild.create_text_channel(name=f"ticket-{member.name}", category=category, overwrites=overwrites)
        
        cfg.setdefault("active", {})[str(member.id)] = t_ch.id
        self.save_config()

        ping_str = f"{member.mention}"
        if cfg.get("role_id"): ping_str += f" <@&{cfg['role_id']}>"
        await t_ch.send(f"{ping_str}\n{cfg['msg_inside']}")

    @commands.command()
    async def tclose(self, ctx):
        try: await ctx.message.delete()
        except: pass

        cfg = self.get_cfg(ctx.guild.id)
        log_id = cfg.get("log_id")
        
        owner_id = None
        for uid, cid in list(cfg.get("active", {}).items()):
            if cid == ctx.channel.id:
                owner_id = uid
                del cfg["active"][uid]
                self.save_config()
                break

        if not log_id:
            return await ctx.channel.delete()

        log_channel = self.bot.get_channel(int(log_id))
        if log_channel:
            messages = [msg async for msg in ctx.channel.history(limit=None)]
            html = f"<html><body style='background-color:#36393f; color:#dcddde; font-family:sans-serif;'><h1>Transcript: #{ctx.channel.name}</h1>"
            for msg in reversed(messages):
                html += f"<div style='margin-bottom:10px;'><b>{msg.author}</b> [{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}]: {msg.content}</div>"
            html += "</body></html>"

            file_path = f"transcript_{ctx.channel.name}.html"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)

            try:
                await log_channel.send(
                    content=f"{self.bot.custom_emojis.get('lock', '')} **Ticket Closed:** `#{ctx.channel.name}`\nOwner ID: `{owner_id}`",
                    file=discord.File(file_path)
                )
            except: pass
            finally:
                os.remove(file_path)
        
        await ctx.channel.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))