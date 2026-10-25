import discord
from discord.ext import commands
import json
import asyncio

class Vouch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if "vouch_channels" not in self.bot.config:
            self.bot.config["vouch_channels"] = {}

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.bot.config, f, indent=4)

    @commands.command()
    async def genvouch(self, ctx, *, text: str):
        try: await ctx.message.delete()
        except: pass
        uid = self.bot.config.get("User_Id", self.bot.user.id)
        srv = self.bot.config.get("SERVER_Link", "")
        await ctx.send(f"+rep <@{uid}> {text}\n{srv}\n**PLEASE VOUCH ME HERE**")

    @commands.command()
    async def genexch(self, ctx, *, text: str):
        try: await ctx.message.delete()
        except: pass
        uid = self.bot.config.get("User_Id", self.bot.user.id)
        srv = self.bot.config.get("SERVER_Link", "")
        await ctx.send(f"+rep <@{uid}> {text} Exchange\n{srv}\n**PLEASE VOUCH ME HERE**")

    @commands.command()
    async def genf2c(self, ctx, fiat_amt: str, crypto_amt: str):
        try: await ctx.message.delete()
        except: pass
        uid = self.bot.config.get("User_Id", self.bot.user.id)
        srv = self.bot.config.get("SERVER_Link", "")
        await ctx.send(f"+rep <@{uid}> {fiat_amt} FIAT TO {crypto_amt} CRYPTO\n{srv}\n**PLEASE VOUCH ME HERE**")

    @commands.command()
    async def genc2f(self, ctx, crypto_amt: str, fiat_amt: str):
        try: await ctx.message.delete()
        except: pass
        uid = self.bot.config.get("User_Id", self.bot.user.id)
        srv = self.bot.config.get("SERVER_Link", "")
        await ctx.send(f"+rep <@{uid}> {crypto_amt} CRYPTO TO {fiat_amt} FIAT\n{srv}\n**PLEASE VOUCH ME HERE**")

    @commands.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def setupvouch(self, ctx, arg1: str, arg2: str = None):
        try: await ctx.message.delete()
        except: pass

        target_channel = ctx.channel
        role_identifier = arg1

        if arg1.isdigit() and len(arg1) >= 17 and arg2:
            ch_found = self.bot.get_channel(int(arg1))
            if ch_found:
                target_channel = ch_found
                role_identifier = arg2
        elif arg2 and arg2.isdigit() and len(arg2) >= 17:
            ch_found = self.bot.get_channel(int(arg2))
            if ch_found:
                target_channel = ch_found

        role = None
        clean_role_id = role_identifier.replace("<@&", "").replace(">", "").strip()
        if clean_role_id.isdigit(): role = ctx.guild.get_role(int(clean_role_id))
        if not role: role = discord.utils.get(ctx.guild.roles, name=role_identifier)
        if not role: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Role not found:** `{role_identifier}`")

        try:
            await target_channel.set_permissions(ctx.guild.default_role, send_messages=False, read_messages=True)
            await target_channel.set_permissions(role, send_messages=True, read_messages=True)
            
            self.bot.config["vouch_channels"][str(target_channel.id)] = {"guild_id": ctx.guild.id, "role_id": role.id}
            self.save_config()

            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Vouch Channel Configured!**\n- **Channel:** {target_channel.mention}\n- **Allowed Role:** {role.mention}")
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[setupvouch] {e}")
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Permission Error:** {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id or not message.guild: return
        if str(message.channel.id) in self.bot.config.get("vouch_channels", {}):
            reaction_emoji = self.bot.custom_emojis.get("vouch_reaction")
            if reaction_emoji:
                await asyncio.sleep(2.0)
                try: await message.add_reaction(reaction_emoji)
                except Exception as e: 
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Vouch AutoReact] Failed in {message.channel.name}: {e}")

async def setup(bot):
    await bot.add_cog(Vouch(bot))