import discord
from discord.ext import commands
import time
import json

class AntiScam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Format: {author_id: [{"channel_id": int, "time": float, "guild_id": int, "msg": discord.Message}]}
        self.activity_window = {} 
        if "antiscam_servers" not in self.bot.config:
            self.bot.config["antiscam_servers"] = []

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    @commands.command()
    async def antiscam(self, ctx, action: str = None, server_id: str = None):
        """Usage: .antiscam [add <server_id> | remove <server_id> | list]"""
        try: await ctx.message.delete()
        except: pass
        try:
            action = action.lower() if action else None
            
            if action == "add" and server_id:
                if server_id not in self.bot.config["antiscam_servers"]:
                    self.bot.config["antiscam_servers"].append(server_id)
                    self.save_config()
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Server `{server_id}` added to Anti-Scam target list.**")
            
            elif action == "remove" and server_id:
                if server_id in self.bot.config["antiscam_servers"]:
                    self.bot.config["antiscam_servers"].remove(server_id)
                    self.save_config()
                    await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Server `{server_id}` removed.**")
                else:
                    await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Server ID not in list.**")
            
            elif action == "list":
                servers = self.bot.config.get("antiscam_servers", [])
                if servers:
                    srv_list = "\n".join([f"- `{s}`" for s in servers])
                    await ctx.send(f"**Targeted Servers:**\n{srv_list}")
                else:
                    await ctx.send(f"**Target List is Empty.** *(Monitoring ALL servers)*")
            
            else:
                current = self.bot.config.get("antiscam_enabled", False)
                new_val = not current
                self.bot.config["antiscam_enabled"] = new_val
                self.save_config()
                
                status = "ENABLED" if new_val else "DISABLED"
                icon = self.bot.custom_emojis.get('check', '') if new_val else self.bot.custom_emojis.get('error', '')
                await ctx.send(f"{icon} **MrBeast Scam Detector is now:** `{status}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.bot.config.get("antiscam_enabled", False): return
        if message.author.id == self.bot.user.id or message.author.bot: return
        
        # Server Targeting Logic
        targeted_servers = self.bot.config.get("antiscam_servers", [])
        if targeted_servers and str(message.guild.id) not in targeted_servers:
            return 
        
        att_count = len(message.attachments) + len(message.embeds)
        if att_count < 4: return 

        now_ts = time.time()
        author_id = message.author.id
        guild_id = message.guild.id if message.guild else "DM"
        
        history = self.activity_window.get(author_id, [])
        valid_history = [r for r in history if (now_ts - r["time"]) <= 15 and r["guild_id"] == guild_id]
        
        valid_history.append({"channel_id": message.channel.id, "time": now_ts, "guild_id": guild_id, "msg": message})
        self.activity_window[author_id] = valid_history
        
        distinct_channels = len(set(r["channel_id"] for r in valid_history))
        
        if distinct_channels >= 3:
            try:
                if hasattr(self.bot, 'bot_logger'): 
                    self.bot.bot_logger.warning(f"[AntiScam] Caught {message.author.name} spamming {distinct_channels} channels!")
                
                if hasattr(message.author, 'block'):
                    try: await message.author.block()
                    except: pass

                if message.guild and message.guild.me.guild_permissions.manage_messages:
                    for r in valid_history:
                        try: await r["msg"].delete()
                        except: pass

                if message.guild and message.guild.me.guild_permissions.kick_members:
                    try: await message.author.kick(reason="MrBeast Scam Velocity Raid detected")
                    except: pass

                self.activity_window[author_id] = [] 
            except Exception as e:
                if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[AntiScam] Mitigation Error: {e}")

async def setup(bot):
    await bot.add_cog(AntiScam(bot))