import json
import os
import re
import asyncio
import discord
from discord.ext import commands

def parse_time_seconds(time_str: str) -> int:
    s = str(time_str).strip().lower()
    if s.endswith("s"): return max(1, int(s[:-1]))
    if s.endswith("m"): return max(1, int(s[:-1]) * 60)
    if s.endswith("h"): return max(1, int(s[:-1]) * 3600)
    if s.endswith("d"): return max(1, int(s[:-1]) * 86400)
    return max(1, int(s))

class Auto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.am_tasks = {}
        self.as_tasks = {}
        self.bot.loop.create_task(self.start_saved_tasks())

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    def load_json(self, filename, default):
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Auto Load] {e}")
        return default

    def save_json(self, filename, data):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Auto Save] {e}")

    async def start_saved_tasks(self):
        await self.bot.wait_until_ready()
        try:
            am_data = self.load_json("am.json", {})
            for chnl_id_str, item in list(am_data.items()):
                self.create_am_task(int(chnl_id_str), item["time"], item["content"])

            as_data = self.bot.config.get("auto_slash", {})
            for chnl_id_str, item in list(as_data.items()):
                self.create_as_task(int(chnl_id_str), item["bot_id"], item["cmd"], item["time"], item.get("options", {}))
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Auto Start Tasks] {e}")

    @commands.command()
    async def ar(self, ctx, *, trigger_and_response: str):
        try: await ctx.message.delete()
        except: pass
        if "," not in trigger_and_response:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Format:** `.ar <trigger>, <response>`")
        try:
            trigger, response = map(str.strip, trigger_and_response.split(",", 1))
            data = self.load_json("ar.json", {})
            data[trigger.lower()] = response
            self.save_json("ar.json", data)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Exact Auto Response Added:** `{trigger}` -> `{response}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def removear(self, ctx, *, trigger: str):
        try: await ctx.message.delete()
        except: pass
        try:
            data = self.load_json("ar.json", {})
            t_clean = trigger.strip().lower()
            if t_clean in data:
                del data[t_clean]
                self.save_json("ar.json", data)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Removed: `{trigger}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def arr(self, ctx, *, trigger_and_response: str):
        try: await ctx.message.delete()
        except: pass
        if "," not in trigger_and_response:
            return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Format:** `.arr <regex_pattern>, <response>`")
        try:
            trigger, response = map(str.strip, trigger_and_response.split(",", 1))
            try: re.compile(trigger)
            except re.error as e:
                return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Invalid Regex:** {e}")

            data = self.load_json("arr.json", {})
            data[trigger] = response
            self.save_json("arr.json", data)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Regex Auto Response Added:** `{trigger}` -> `{response}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def removearr(self, ctx, *, trigger: str):
        try: await ctx.message.delete()
        except: pass
        try:
            data = self.load_json("arr.json", {})
            if trigger in data:
                del data[trigger]
                self.save_json("arr.json", data)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} Removed Regex: `{trigger}`")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def autoreact(self, ctx, user: discord.User, emoji: str):
        try: await ctx.message.delete()
        except: pass
        try:
            data = self.load_json("autoreact.json", {})
            if str(user.id) in data and data[str(user.id)] == emoji:
                del data[str(user.id)]
                self.save_json("autoreact.json", data)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **AutoReact Stopped for:** {user.name}")
            else:
                data[str(user.id)] = emoji
                self.save_json("autoreact.json", data)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **AutoReact Enabled:** I will react to {user.name} with {emoji}")
        except Exception as e: self.log_err(ctx, e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id: return
        try:
            react_data = self.load_json("autoreact.json", {})
            if str(message.author.id) in react_data:
                try: await message.add_reaction(react_data[str(message.author.id)])
                except Exception as e: 
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[AutoReact] {e}")

            ar_data = self.load_json("ar.json", {})
            if message.content and message.content.lower() in ar_data:
                try: await message.channel.send(ar_data[message.content.lower()])
                except Exception as e: 
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Exact AR] {e}")
                return 

            arr_data = self.load_json("arr.json", {})
            if message.content:
                for pattern, response in arr_data.items():
                    if re.search(pattern, message.content, re.IGNORECASE):
                        try: await message.channel.send(response)
                        except Exception as e:
                            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Regex AR] {e}")
                        break
        except Exception as e:
            if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[Auto on_message] {e}")

    def create_am_task(self, channel_id: int, seconds: int, content: str):
        if channel_id in self.am_tasks: self.am_tasks[channel_id].cancel()
        async def _loop():
            while True:
                await asyncio.sleep(seconds)
                ch = self.bot.get_channel(channel_id)
                if ch:
                    try: await ch.send(content)
                    except Exception as e:
                        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[AutoMsg Loop] {e}")
        self.am_tasks[channel_id] = self.bot.loop.create_task(_loop())

    @commands.command()
    async def am(self, ctx, time_str: str, channel_id: int = None, *, content: str = None):
        try: await ctx.message.delete()
        except: pass
        try:
            if channel_id is None:
                channel_id = ctx.channel.id
                content = ctx.message.content.split(' ', 2)[2] if len(ctx.message.content.split(' ')) > 2 else ""
            if not content: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Usage:** `.am <time> [chnl_id] <message>`")

            sec = parse_time_seconds(time_str)
            self.create_am_task(channel_id, sec, content)
            data = self.load_json("am.json", {})
            data[str(channel_id)] = {"time": sec, "content": content}
            self.save_json("am.json", data)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Message running.**")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def stopam(self, ctx, channel_id: int = None):
        try: await ctx.message.delete()
        except: pass
        try:
            target = channel_id or ctx.channel.id
            if target in self.am_tasks:
                self.am_tasks[target].cancel()
                del self.am_tasks[target]
                data = self.load_json("am.json", {})
                data.pop(str(target), None)
                self.save_json("am.json", data)
                await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Message stopped.**")
        except Exception as e: self.log_err(ctx, e)

    def create_as_task(self, channel_id: int, bot_id: int, cmd_name: str, seconds: int, options: dict):
        if channel_id in self.as_tasks: self.as_tasks[channel_id].cancel()
        async def _slash_loop():
            while True:
                await asyncio.sleep(seconds)
                ch = self.bot.get_channel(channel_id)
                if not ch: continue
                try:
                    cmds = await ch.application_commands()
                    for c in cmds:
                        app_id = getattr(c, "application_id", None) or getattr(getattr(c, "application", None), "id", None)
                        if str(app_id) == str(bot_id) and c.name.lower() == cmd_name.lower():
                            await c(channel=ch, **options)
                            break
                except Exception as e:
                    if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[AutoSlash Loop] {e}")
        self.as_tasks[channel_id] = self.bot.loop.create_task(_slash_loop())

    @commands.command()
    async def as_(self, ctx, bot_id: int, channel: discord.TextChannel, cmd_name: str, time_str: str, *, raw_options: str = ""):
        try: await ctx.message.delete()
        except: pass
        try:
            sec = parse_time_seconds(time_str)
            options = {}
            if raw_options:
                for pair in raw_options.split():
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        options[k.strip()] = int(v) if v.isdigit() else v.strip()

            self.create_as_task(channel.id, bot_id, cmd_name, sec, options)
            if "auto_slash" not in self.bot.config: self.bot.config["auto_slash"] = {}
            self.bot.config["auto_slash"][str(channel.id)] = {"bot_id": bot_id, "cmd": cmd_name, "time": sec, "options": options}
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.bot.config, f, indent=4)
            await ctx.send(f"{self.bot.custom_emojis.get('check', '')} **Auto Slash scheduled.**")
        except Exception as e: self.log_err(ctx, e)

async def setup(bot):
    await bot.add_cog(Auto(bot))