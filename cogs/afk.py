import discord
from discord.ext import commands

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_afk = False
        self.afk_message = ""
        self.afk_time = None
        self.missed_pings = []
        self.replied_users = set()

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    @commands.command()
    async def afk(self, ctx, *, message: str = None):
        try: await ctx.message.delete()
        except: pass
        try:
            self.is_afk = True
            
            # Use provided message, otherwise pull default from config
            if not message:
                message = self.bot.config.get("afk_default", "I am currently AFK.")
                
            self.afk_message = message
            self.afk_time = discord.utils.utcnow()
            self.missed_pings = []
            self.replied_users.clear()
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **AFK Enabled:** `{message}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def unafk(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            if not self.is_afk:
                return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **You are not currently AFK.**")

            self.is_afk = False
            time_away = discord.utils.utcnow() - self.afk_time
            hours, remainder = divmod(int(time_away.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)

            if not self.missed_pings:
                summary = "You missed 0 mentions or DMs."
            else:
                summary = "**Missed Pings & DMs:**\n"
                for p in self.missed_pings:
                    summary += f"- **{p['author']}** in `{p['location']}`: {p['content']}\n"

            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **AFK Removed.** You were gone for `{hours}h {minutes}m`.")
            
            try:
                if len(summary) > 1900: summary = summary[:1900] + "\n... (truncated)"
                await ctx.author.send(summary)
            except Exception as e:
                if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[unafk DM] {e}")
        except Exception as e: self.log_err(ctx, e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.is_afk or message.author.id == self.bot.user.id:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.bot.user in message.mentions

        if is_dm or is_mention:
            loc = "DM" if is_dm else message.guild.name
            self.missed_pings.append({
                "author": message.author.name,
                "location": loc,
                "content": message.content
            })

            if message.author.id not in self.replied_users:
                try:
                    await message.channel.send(f"**[AFK]** {self.afk_message}")
                    self.replied_users.add(message.author.id)
                except Exception as e:
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[AFK AutoReply] {e}")

async def setup(bot):
    await bot.add_cog(AFK(bot))