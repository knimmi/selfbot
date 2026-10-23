import json
import os
import discord
from discord.ext import commands, tasks

class Auto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks_dict = {}

    def load_auto_messages(self):
        try:
            with open("am.json", "r", encoding="utf-8") as f: return json.load(f)
        except FileNotFoundError: return {}

    def save_auto_messages(self, data):
        with open("am.json", "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

    @commands.command()
    async def ar(self, ctx, *, trigger_and_response: str):
        try: await ctx.message.delete()
        except: pass
        trigger, response = map(str.strip, trigger_and_response.split(','))
        data = {}
        if os.path.exists('ar.json'):
            with open('ar.json', 'r') as file: data = json.load(file)
        data[trigger] = response
        with open('ar.json', 'w') as file: json.dump(data, file, indent=4)
        
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Response Added:** **{trigger}** - **{response}**")

    @commands.command()
    async def removear(self, ctx, trigger: str):
        try: await ctx.message.delete()
        except: pass
        with open('ar.json', 'r') as file: data = json.load(file)
        if trigger in data:
            del data[trigger]
            with open('ar.json', 'w') as file: json.dump(data, file, indent=4)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Response Removed** **{trigger}**")
        else:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Trigger not found.**")

    @commands.command()
    async def ar_list(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if os.path.exists("ar.json"):
            with open("ar.json", "r") as f: await ctx.send(f.read())

    @commands.command()
    async def am(self, ctx, time_in_sec: int, channel_id: int, *, content: str):
        try: await ctx.message.delete()
        except: pass
        channel = self.bot.get_channel(channel_id)
        if not channel or time_in_sec <= 0: return
        
        auto_msgs = self.load_auto_messages()
        auto_msgs[str(channel_id)] = {"time": time_in_sec, "content": content}
        self.save_auto_messages(auto_msgs)

        @tasks.loop(seconds=time_in_sec)
        async def auto_message_task():
            await channel.send(content)

        auto_message_task.start()
        self.tasks_dict[channel_id] = auto_message_task
        await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Message Set to every {time_in_sec} seconds in channel {channel_id}.**")

    @commands.command()
    async def am_stop(self, ctx, channel_id: int):
        try: await ctx.message.delete()
        except: pass
        if channel_id in self.tasks_dict:
            self.tasks_dict[channel_id].stop()
            del self.tasks_dict[channel_id]
            auto_msgs = self.load_auto_messages()
            auto_msgs.pop(str(channel_id), None)
            self.save_auto_messages(auto_msgs)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Message Stopped for channel {channel_id}.**")
        else:
            await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **No active Auto Message found for that channel.**")

    @commands.command()
    async def am_list(self, ctx):
        try: await ctx.message.delete()
        except: pass
        if os.path.exists("am.json"):
            with open("am.json", "r") as f: await ctx.send(f.read())

async def setup(bot):
    await bot.add_cog(Auto(bot))