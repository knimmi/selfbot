import asyncio
import json
from pathlib import Path
import discord
from discord.ext import commands


class Auto(commands.Cog, name="Auto"):
    """Global Auto-Slash Commands, Disboard Auto-Bump, Auto-Messages (am.json), and Auto-Responder (ar.json)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.am_path = Path("am.json")
        self.ar_path = Path("ar.json")

        self.am_data: dict = self._load_json(self.am_path)
        self.ar_data: dict = self._load_json(self.ar_path)

        # Active asyncio tasks keyed by task_id
        self.slash_tasks: dict[str, asyncio.Task] = {}
        self.msg_tasks: dict[str, asyncio.Task] = {}

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {}

    def _save_json(self, path: Path, data: dict):
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")

    async def cog_load(self):
        self.bot.loop.create_task(self._restore_saved_tasks())

    def cog_unload(self):
        for t in list(self.slash_tasks.values()) + list(self.msg_tasks.values()):
            t.cancel()

    async def _resolve_text_channel(self, ctx: commands.Context | None, channel_input: str | int | None):
        """Resolve any guild text channel globally by ID or <#mention> so commands work from DMs or other servers."""
        if channel_input is None:
            return ctx.channel if ctx else None

        cleaned = str(channel_input).strip().lstrip("<#").rstrip(">")
        if cleaned.isdigit():
            cid = int(cleaned)
            ch = self.bot.get_channel(cid)
            if ch is None:
                try:
                    ch = await self.bot.fetch_channel(cid)
                except Exception:
                    ch = None
            return ch
        return ctx.channel if ctx else None

    async def _execute_slash_command(
        self,
        channel: discord.abc.Messageable,
        command_query: str,
        bot_id: int | None = None,
    ) -> tuple[bool, str]:
        """Find and invoke a real Discord Application SlashCommand in the target channel."""
        parts = command_query.strip().lstrip("/").split()
        if not parts:
            return False, "Empty command name."

        root_name = parts[0].lower()
        sub_name = parts[1].lower() if len(parts) > 1 else None

        try:
            commands_list = await channel.application_commands()
        except Exception as e:
            return False, f"Failed to fetch application commands for channel: {e}"

        matched_cmd = None
        for cmd in commands_list:
            if getattr(cmd, "name", "").lower() == root_name:
                if bot_id and getattr(cmd, "application_id", None) != bot_id:
                    continue
                matched_cmd = cmd
                break

        if not matched_cmd:
            return False, f"Slash command `/{root_name}` not found in <#{getattr(channel, 'id', '?')}>."

        try:
            # Handle subcommand if present (e.g. /fish sell or /bump)
            if sub_name and getattr(matched_cmd, "children", None):
                for child in matched_cmd.children:
                    if getattr(child, "name", "").lower() == sub_name:
                        await child(channel)
                        return True, f"Executed `/{root_name} {sub_name}` in <#{channel.id}>"

            await matched_cmd(channel)
            return True, f"Executed `/{root_name}` in <#{channel.id}>"
        except Exception as e:
            return False, f"Failed invoking `/{root_name}`: {e}"

    async def _restore_saved_tasks(self):
        await self.bot.wait_until_ready()
        # Restore saved auto-slash loops
        for task_id, cfg in self.am_data.get("slash", {}).items():
            self._start_slash_loop(task_id, cfg["channel_id"], cfg["interval"], cfg["command"], cfg.get("bot_id"))

        # Restore saved auto-message loops
        for task_id, cfg in self.am_data.get("messages", {}).items():
            self._start_msg_loop(task_id, cfg["channel_id"], cfg["interval"], cfg["text"])

    def _start_slash_loop(self, task_id: str, channel_id: int, interval: int, command_str: str, bot_id: int | None = None):
        if task_id in self.slash_tasks:
            self.slash_tasks[task_id].cancel()

        async def _loop():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                ch = await self._resolve_text_channel(None, channel_id)
                if ch:
                    await self._execute_slash_command(ch, command_str, bot_id)
                await asyncio.sleep(max(interval, 5))

        self.slash_tasks[task_id] = asyncio.create_task(_loop())

    def _start_msg_loop(self, task_id: str, channel_id: int, interval: int, text: str):
        if task_id in self.msg_tasks:
            self.msg_tasks[task_id].cancel()

        async def _loop():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                ch = await self._resolve_text_channel(None, channel_id)
                if ch:
                    try:
                        await ch.send(text)
                    except Exception:
                        pass
                await asyncio.sleep(max(interval, 5))

        self.msg_tasks[task_id] = asyncio.create_task(_loop())

    # =========================================================================
    # SLASH & AUTO-SLASH COMMANDS (Works from any server or DM)
    # =========================================================================

    @commands.command(
        name="slash",
        aliases=["runslash", "useslash"],
        help="Trigger a slash command once in any channel (pass channel ID or 'here'). Usage: .slash <channel_id|here> <command>",
    )
    async def slash(self, ctx: commands.Context, channel_target: str, *, command_query: str):
        ch = ctx.channel if channel_target.lower() in ("here", "this") else await self._resolve_text_channel(ctx, channel_target)
        if not ch:
            return await ctx.send("`[AutoSlash]` Channel not found. Provide a valid channel ID or `here`.", delete_after=7)

        ok, msg = await self._execute_slash_command(ch, command_query)
        await ctx.send(f"`[AutoSlash]` {msg}", delete_after=8)

    @commands.command(
        name="autoslash",
        aliases=["loopslash", "aslash"],
        help="Start an auto-slash loop in any channel. Usage: .autoslash <channel_id|here> <seconds> <command>",
    )
    async def autoslash(self, ctx: commands.Context, channel_target: str, interval: int, *, command_query: str):
        ch = ctx.channel if channel_target.lower() in ("here", "this") else await self._resolve_text_channel(ctx, channel_target)
        if not ch:
            return await ctx.send("`[AutoSlash]` Could not resolve that channel ID.", delete_after=7)

        task_id = f"{ch.id}:{command_query.strip().lstrip('/')}"
        slash_store = self.am_data.setdefault("slash", {})
        slash_store[task_id] = {
            "channel_id": ch.id,
            "interval": max(interval, 5),
            "command": command_query.strip().lstrip("/"),
            "bot_id": None,
        }
        self._save_json(self.am_path, self.am_data)
        self._start_slash_loop(task_id, ch.id, interval, command_query)
        await ctx.send(
            f"`[AutoSlash]` Started `/{command_query.lstrip('/')}` in <#{ch.id}> every **{interval}s** (ID: `{task_id}`).",
            delete_after=8,
        )

    @commands.command(
        name="autobump",
        help="Start automatic Disboard /bump every 2 hours (7215s) in any channel ID or 'here'.",
    )
    async def autobump(self, ctx: commands.Context, channel_target: str = "here"):
        await self.autoslash(ctx, channel_target, 7215, command_query="bump")

    @commands.command(name="stopautoslash", aliases=["delautoslash"], help="Stop an active auto-slash task by channel ID or 'all'.")
    async def stopautoslash(self, ctx: commands.Context, target: str = "all"):
        slash_store = self.am_data.get("slash", {})
        removed = 0
        for tid in list(slash_store.keys()):
            if target.lower() == "all" or target in tid:
                slash_store.pop(tid, None)
                t = self.slash_tasks.pop(tid, None)
                if t:
                    t.cancel()
                removed += 1
        self._save_json(self.am_path, self.am_data)
        await ctx.send(f"`[AutoSlash]` Stopped **{removed}** auto-slash loop(s).", delete_after=7)

    # =========================================================================
    # AUTO-MESSAGE & AUTO-RESPONDER (am.json & ar.json)
    # =========================================================================

    @commands.command(
        name="automsg",
        aliases=["am"],
        help="Loop sending a message in any channel ID or 'here'. Usage: .automsg <channel_id|here> <seconds> <text>",
    )
    async def automsg(self, ctx: commands.Context, channel_target: str, interval: int, *, text: str):
        ch = ctx.channel if channel_target.lower() in ("here", "this") else await self._resolve_text_channel(ctx, channel_target)
        if not ch:
            return await ctx.send("`[AutoMsg]` Channel not found.", delete_after=6)

        task_id = str(ch.id)
        msg_store = self.am_data.setdefault("messages", {})
        msg_store[task_id] = {"channel_id": ch.id, "interval": max(interval, 5), "text": text}
        self._save_json(self.am_path, self.am_data)
        self._start_msg_loop(task_id, ch.id, interval, text)
        await ctx.send(f"`[AutoMsg]` Sending message in <#{ch.id}> every **{interval}s**.", delete_after=7)

    @commands.command(name="stopautomsg", aliases=["stopam"], help="Stop auto-messages for a channel ID or 'all'.")
    async def stopautomsg(self, ctx: commands.Context, target: str = "all"):
        msg_store = self.am_data.get("messages", {})
        removed = 0
        for tid in list(msg_store.keys()):
            if target.lower() == "all" or target == tid:
                msg_store.pop(tid, None)
                t = self.msg_tasks.pop(tid, None)
                if t:
                    t.cancel()
                removed += 1
        self._save_json(self.am_path, self.am_data)
        await ctx.send(f"`[AutoMsg]` Stopped **{removed}** auto-message loop(s).", delete_after=7)

    @commands.command(name="addar", aliases=["autoreply"], help="Add an auto-responder trigger and reply to ar.json.")
    async def addar(self, ctx: commands.Context, trigger: str, *, reply: str):
        self.ar_data[trigger.lower()] = reply
        self._save_json(self.ar_path, self.ar_data)
        await ctx.send(f"`[AutoResponder]` Added trigger `{trigger.lower()}` -> `{reply}`", delete_after=7)

    @commands.command(name="delar", help="Remove an auto-responder trigger from ar.json.")
    async def delar(self, ctx: commands.Context, trigger: str):
        self.ar_data.pop(trigger.lower(), None)
        self._save_json(self.ar_path, self.ar_data)
        await ctx.send(f"`[AutoResponder]` Removed trigger `{trigger.lower()}`.", delete_after=7)

    @commands.command(name="autolist", help="List all active auto-slash, auto-message, and auto-responder tasks.")
    async def autolist(self, ctx: commands.Context):
        slash_items = [
            f"• /{v['command']} in <#{v['channel_id']}> every {v['interval']}s"
            for v in self.am_data.get("slash", {}).values()
        ]
        msg_items = [
            f"• '{v['text'][:30]}' in <#{v['channel_id']}> every {v['interval']}s"
            for v in self.am_data.get("messages", {}).values()
        ]
        ar_items = [f"• '{k}' -> '{v[:30]}'" for k, v in self.ar_data.items()]

        out = (
            "```ini\n"
            f"[Auto-Slash Loops ({len(slash_items)})]\n" + ("\n".join(slash_items) or "None") + "\n\n"
            f"[Auto-Message Loops ({len(msg_items)})]\n" + ("\n".join(msg_items) or "None") + "\n\n"
            f"[Auto-Responders ({len(ar_items)})]\n" + ("\n".join(ar_items) or "None") + "\n```"
        )
        await ctx.send(out)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author or message.author.id == self.bot.user.id:
            return
        content_lower = (message.content or "").lower().strip()
        if not content_lower:
            return
        for trigger, response in self.ar_data.items():
            if trigger in content_lower:
                try:
                    await message.channel.send(response)
                except Exception:
                    pass
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(Auto(bot))