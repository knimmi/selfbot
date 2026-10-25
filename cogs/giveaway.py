import discord
from discord.ext import commands
import asyncio
import random
import json
import aiohttp
from datetime import datetime

class GiveawayJoiner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.history = set()
        
        if "giveaway" not in self.bot.config:
            self.bot.config["giveaway"] = {
                "enabled": False,
                "monitored_bots": [
                    "294882584201003009", 
                    "530082442967646230", 
                    "155149108183695360", 
                    "235148962103951360", 
                    "720351927581278219"  
                ],
                "delay_min": 2.0,
                "delay_max": 8.0,
                "stats": {"detected": 0, "joined": 0}
            }

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    async def send_webhook(self, title, description, color):
        # Pulls directly from the unified autolog webhooks dictionary
        webhook_url = self.bot.config.get("webhooks", {}).get("giveaways")
        if not webhook_url: return
        
        embed = {"title": title, "description": description, "color": color, "timestamp": datetime.utcnow().isoformat()}
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(webhook_url, json={"embeds": [embed]})
        except:
            pass

    @commands.command()
    async def gw(self, ctx, action: str = None):
        """Usage: .gw [toggle | status]"""
        try: await ctx.message.delete()
        except: pass
        try:
            cfg = self.bot.config["giveaway"]
            action = action.lower() if action else "status"

            if action == "toggle":
                cfg["enabled"] = not cfg["enabled"]
                self.save_config()
                state = "ENABLED" if cfg["enabled"] else "DISABLED"
                icon = self.bot.custom_emojis.get('check', '') if cfg["enabled"] else self.bot.custom_emojis.get('error', '')
                await ctx.send(f"{icon} **Giveaway Joiner is now:** `{state}`")
            else:
                state = "Active" if cfg["enabled"] else "Disabled"
                detected = cfg["stats"].get("detected", 0)
                joined = cfg["stats"].get("joined", 0)
                bots = len(cfg["monitored_bots"])
                await ctx.send(f"**🎉 Giveaway Joiner Status**\n- **State:** `{state}`\n- **Monitored Bots:** `{bots}`\n- **Detected:** `{detected}`\n- **Joined:** `{joined}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.Cog.listener()
    async def on_message(self, message):
        cfg = self.bot.config.get("giveaway", {})
        if not cfg.get("enabled", False): return
        if message.author.id == self.bot.user.id: return
        
        if str(message.author.id) not in cfg.get("monitored_bots", []): return

        content = (message.content or "").lower()
        if message.embeds:
            content += " " + (message.embeds[0].title or "").lower()
            content += " " + (message.embeds[0].description or "").lower()

        is_gw = any(k in content for k in ["giveaway", "sorteo", "prize", "drop", "🎁", "🎉", "winner"])
        if not is_gw: return
        
        if message.id in self.history: return
        self.history.add(message.id)

        # Lightweight Prize Extractor
        prize = "Unknown Prize"
        if message.embeds:
            for emb in message.embeds:
                if emb.title and "giveaway" not in emb.title.lower():
                    prize = emb.title[:60]
                    break
                elif emb.description:
                    prize = emb.description.split('\n')[0][:60]
                    break

        cfg["stats"]["detected"] = cfg["stats"].get("detected", 0) + 1
        self.save_config()

        server_name = message.guild.name if message.guild else 'DM'

        await self.send_webhook(
            "🔍 Giveaway Detected",
            f"**Detected Bot:** {message.author.mention}\n**Detected Prize:** `{prize}`\n**Detected Server:** {server_name}\n**Link:** [Jump to Message]({message.jump_url})",
            0xFFA500 
        )

        delay = random.uniform(cfg.get("delay_min", 2.0), cfg.get("delay_max", 8.0))
        await asyncio.sleep(delay)

        joined = False
        
        if message.components:
            for row in message.components:
                for child in row.children:
                    if isinstance(child, discord.Button):
                        label = (child.label or "").lower()
                        emoji = str(child.emoji or "")
                        custom_id = (child.custom_id or "").lower()
                        
                        if any(k in label for k in ['join', 'enter', 'participate']) or any(e in emoji for e in ['🎉', '🎁']) or 'giveaway' in custom_id:
                            try:
                                await child.click()
                                joined = True
                                break
                            except Exception as e:
                                if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[GW Joiner] Button Click Failed: {e}")
                if joined: break
        
        if not joined and message.reactions:
            for reaction in message.reactions:
                if str(reaction.emoji) in ["🎉", "🎁", "💎"]:
                    try:
                        await message.add_reaction(reaction.emoji)
                        joined = True
                        break
                    except Exception as e:
                        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[GW Joiner] Reaction Failed: {e}")
        
        if joined:
            cfg["stats"]["joined"] = cfg["stats"].get("joined", 0) + 1
            self.save_config()
            
            await self.send_webhook(
                "🎉 Giveaway Joined",
                f"**Detected Bot:** {message.author.mention}\n**Detected Prize:** `{prize}`\n**Detected Server:** {server_name}\n**Link:** [Jump to Message]({message.jump_url})",
                0x00FF00 
            )
            
            if hasattr(self.bot, 'bot_logger'): 
                self.bot.bot_logger.info(f"[GW Joiner] Successfully joined giveaway {message.id} in {server_name}")

async def setup(bot):
    await bot.add_cog(GiveawayJoiner(bot))