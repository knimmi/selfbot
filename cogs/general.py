import asyncio
import time
import discord
from discord.ext import commands


class General(commands.Cog, name="General"):
    """Dynamic Help Menu (auto-discovers all cogs & Ghost modules) and General Selfbot Utilities."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()
        # Remove default help command so our dynamic help menu takes over cleanly
        self.bot.remove_command("help")

    @commands.command(
        name="help",
        aliases=["h", "commands", "cmds"],
        help="Show all categories/cogs, or view detailed help for a specific cog or command.",
    )
    async def help_command(self, ctx: commands.Context, *, query: str = None):
        prefix = ctx.clean_prefix if hasattr(ctx, "clean_prefix") else "."

        if not query:
            lines = [
                f"[Ghost Selfbot Command Center — Prefix: {prefix}]",
                f"Use '{prefix}help <category>' or '{prefix}help <command>' for details.\n",
            ]
            total_cmds = 0
            for cog_name, cog in sorted(self.bot.cogs.items()):
                cmds = [c.name for c in cog.get_commands() if not c.hidden]
                if not cmds:
                    continue
                total_cmds += len(cmds)
                preview = ", ".join(sorted(cmds))
                lines.append(f"[{cog_name} ({len(cmds)})]\n  {preview}")

            lines.append(f"\nTotal Loaded Cogs: {len(self.bot.cogs)} | Total Commands: {total_cmds}")
            text = "\n".join(lines)
            # Split safely if over 1900 chars
            for i in range(0, len(text), 1850):
                await ctx.send(f"```ini\n{text[i:i+1850]}\n```")
            return

        # 1. Check if query matches a Cog name (case-insensitive)
        matched_cog = next(
            (cog for name, cog in self.bot.cogs.items() if name.lower() == query.lower()),
            None,
        )
        if matched_cog:
            cmds = matched_cog.get_commands()
            desc = matched_cog.__doc__ or "No category description."
            cmd_lines = [
                f"{prefix}{c.name:<15} ; {c.help or 'No description'}"
                for c in sorted(cmds, key=lambda x: x.name)
            ]
            body = "\n".join(cmd_lines) or "No commands in this category."
            return await ctx.send(
                f"```ini\n[{matched_cog.qualified_name} Category]\n; {desc}\n\n{body}\n```"
            )

        # 2. Check if query matches a specific command or alias
        cmd = self.bot.get_command(query.lower())
        if cmd:
            aliases = ", ".join(cmd.aliases) if cmd.aliases else "None"
            signature = f"{prefix}{cmd.qualified_name} {cmd.signature}".strip()
            return await ctx.send(
                f"```ini\n"
                f"[Command: {cmd.qualified_name}]\n"
                f"Usage       : {signature}\n"
                f"Aliases     : {aliases}\n"
                f"Category    : {cmd.cog_name or 'Uncategorized'}\n"
                f"Description : {cmd.help or 'No description provided.'}\n"
                f"```"
            )

        await ctx.send(f"`[Help]` No category or command found matching `{query}`.", delete_after=6)

    @commands.command(name="ping", help="Check websocket latency to Discord.")
    async def ping(self, ctx: commands.Context):
        ms = round(self.bot.latency * 1000, 1)
        await ctx.send(f"`[Ghost]` Pong! Latency: **{ms}ms**")

    @commands.command(name="uptime", help="Check how long the selfbot has been online.")
    async def uptime(self, ctx: commands.Context):
        elapsed = int(time.time() - self.start_time)
        days, rem = divmod(elapsed, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        await ctx.send(f"`[Ghost]` Uptime: **{days}d {hours}h {minutes}m {seconds}s**")

    @commands.command(
        name="serverinfo",
        aliases=["guildinfo", "sinfo"],
        help="Show server details (pass a guild_id to inspect any server from DMs!).",
    )
    async def serverinfo(self, ctx: commands.Context, guild_id: int = None):
        guild = self.bot.get_guild(guild_id) if guild_id else ctx.guild
        if not guild:
            return await ctx.send("`[Ghost]` Pass a valid `guild_id` when running `serverinfo` inside DMs.", delete_after=6)

        created = guild.created_at.strftime("%Y-%m-%d")
        info = (
            f"```ini\n"
            f"[Server Info: {guild.name}]\n"
            f"ID          : {guild.id}\n"
            f"Owner ID    : {guild.owner_id}\n"
            f"Members     : {guild.member_count}\n"
            f"Text/Voice  : {len(guild.text_channels)} text / {len(guild.voice_channels)} voice\n"
            f"Roles       : {len(guild.roles)}\n"
            f"Emojis      : {len(guild.emojis)}\n"
            f"Created     : {created}\n"
            f"```"
        )
        await ctx.send(info)

    @commands.command(name="purge", aliases=["clear", "prune"], help="Bulk-delete your own recent messages in the current channel or DM.")
    async def purge(self, ctx: commands.Context, amount: int = 20):
        deleted = 0
        async for m in ctx.channel.history(limit=amount * 4):
            if m.author.id == self.bot.user.id:
                try:
                    await m.delete()
                    deleted += 1
                    await asyncio.sleep(0.4)
                    if deleted >= amount:
                        break
                except Exception:
                    continue
        await ctx.send(f"`[Ghost]` Deleted **{deleted}** of your messages.", delete_after=4)

    @commands.command(name="reload", help="Hot-reload a cog extension (or 'all' to reload all cogs).")
    async def reload(self, ctx: commands.Context, extension: str = "all"):
        if extension.lower() == "all":
            reloaded = []
            failed = []
            for ext in list(self.bot.extensions.keys()):
                try:
                    await self.bot.reload_extension(ext)
                    reloaded.append(ext)
                except Exception as e:
                    failed.append(f"{ext} ({e})")
            msg = f"`[Ghost]` Reloaded **{len(reloaded)}** extensions."
            if failed:
                msg += f" Failed: {', '.join(failed)}"
            return await ctx.send(msg, delete_after=8)

        ext_name = extension if extension.startswith("cogs.") else f"cogs.{extension.lower()}"
        try:
            await self.bot.reload_extension(ext_name)
            await ctx.send(f"`[Ghost]` Reloaded `{ext_name}`.", delete_after=6)
        except commands.ExtensionNotLoaded:
            await self.bot.load_extension(ext_name)
            await ctx.send(f"`[Ghost]` Loaded `{ext_name}`.", delete_after=6)
        except Exception as e:
            await ctx.send(f"`[Ghost]` Error reloading `{ext_name}`: `{e}`", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))