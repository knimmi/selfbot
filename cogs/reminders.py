import discord
from discord.ext import commands, tasks
import json
import os
import time

def parse_time_seconds(time_str: str) -> int:
    s = str(time_str).strip().lower()
    if s.endswith("s"): return max(1, int(s[:-1]))
    if s.endswith("m"): return max(1, int(s[:-1]) * 60)
    if s.endswith("h"): return max(1, int(s[:-1]) * 3600)
    if s.endswith("d"): return max(1, int(s[:-1]) * 86400)
    return max(1, int(s))

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders_file = "reminders.json"
        if not os.path.exists(self.reminders_file):
            with open(self.reminders_file, "w") as f:
                json.dump({}, f)
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    def load_reminders(self):
        with open(self.reminders_file, "r") as f:
            return json.load(f)

    def save_reminders(self, data):
        with open(self.reminders_file, "w") as f:
            json.dump(data, f, indent=4)

    @commands.command(aliases=["remindme", "rmd"])
    async def remind(self, ctx, duration: str, *, message: str):
        try: await ctx.message.delete()
        except: pass
        
        seconds = parse_time_seconds(duration)
        trigger_time = int(time.time()) + seconds
        reminders = self.load_reminders()
        
        rem_id = str(int(time.time() * 1000))[-6:]
        reminders[rem_id] = {
            "time": trigger_time,
            "message": message,
            "channel_id": ctx.channel.id
        }
        
        self.save_reminders(reminders)
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Reminder set for {duration}.** (ID: `{rem_id}`)")

    @commands.command()
    async def reminders(self, ctx):
        try: await ctx.message.delete()
        except: pass
        
        reminders = self.load_reminders()
        if not reminders:
            return await ctx.send(f"{self.bot.custom_emojis.get('remind', '')} You have no active reminders.")
            
        text = f"{self.bot.custom_emojis.get('remind', '')} **Active Reminders:**\n"
        for r_id, r_data in reminders.items():
            time_left = int(r_data['time'] - time.time())
            minutes, seconds = divmod(time_left, 60)
            hours, minutes = divmod(minutes, 60)
            text += f"`{r_id}` - In **{hours}h {minutes}m {seconds}s**: {r_data['message']}\n"
            
        await ctx.send(text)

    @commands.command()
    async def delreminder(self, ctx, rem_id: str):
        try: await ctx.message.delete()
        except: pass
        
        reminders = self.load_reminders()
        if rem_id in reminders:
            del reminders[rem_id]
            self.save_reminders(reminders)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Reminder `{rem_id}` deleted.**")
        else:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Reminder ID not found.**")

    @tasks.loop(seconds=3)
    async def reminder_loop(self):
        reminders = self.load_reminders()
        current_time = int(time.time())
        to_delete = []
        rem_emoji = self.bot.custom_emojis.get("remind", "")

        for r_id, r_data in reminders.items():
            if current_time >= r_data["time"]:
                try:
                    ch = self.bot.get_channel(r_data["channel_id"])
                    if not ch:
                        ch = await self.bot.fetch_channel(r_data["channel_id"])
                    await ch.send(f"{rem_emoji} **REMINDER:** {r_data['message']}")
                except:
                    pass
                to_delete.append(r_id)

        if to_delete:
            for d in to_delete:
                del reminders[d]
            self.save_reminders(reminders)

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminders(bot))