import json
import os
from pathlib import Path
from urllib.parse import urlencode

import discord
from discord.ext import commands


class Embeds(commands.Cog, name="Embeds"):
    """Self-Hosted OpenGraph Embeds, Webhook-Spoofed Native Embeds, and ANSI Embed Cards (No third-party APIs)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_self_hosted_url(self) -> str | None:
        """Read public_url from ENV or config.json for self-hosted OpenGraph link previews."""
        url = os.getenv("PUBLIC_EMBED_URL") or os.getenv("PUBLIC_URL")
        if url:
            return url.rstrip("/")
        cfg_path = Path("config.json")
        if cfg_path.exists():
            try:
                data = json.loads(cfg_path.read_text(encoding="utf-8"))
                url = data.get("public_url") or data.get("embed_url") or data.get("dashboard", {}).get("public_url")
                if url:
                    return str(url).rstrip("/")
            except Exception:
                pass
        return None

    @commands.command(
        name="ghostembed",
        aliases=["gembed", "embed"],
        help="Send a styled embed without external APIs (uses self-hosted /og if public_url is set, otherwise native ANSI card).",
    )
    async def ghostembed(self, ctx: commands.Context, title: str, description: str, color: str = "cyan"):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        base_url = self._get_self_hosted_url()
        if base_url:
            params = urlencode({"title": title, "description": description, "color": color.lstrip("#")})
            embed_url = f"{base_url}/og?{params}"
            hidden_wall = "||​||" * 198
            return await ctx.send(f"{hidden_wall} {embed_url}")

        # Zero-API Native ANSI Card Fallback
        ansi_colors = {
            "red": "\u001b[1;31m",
            "green": "\u001b[1;32m",
            "yellow": "\u001b[1;33m",
            "blue": "\u001b[1;34m",
            "pink": "\u001b[1;35m",
            "purple": "\u001b[1;35m",
            "cyan": "\u001b[1;36m",
            "white": "\u001b[1;37m",
        }
        c_code = ansi_colors.get(color.lower(), "\u001b[1;36m")
        reset = "\u001b[0m"
        dim = "\u001b[0;37m"
        border = "━" * max(len(title) + 4, 28)
        card = (
            f"```ansi\n"
            f"{c_code}┏{border}┓{reset}\n"
            f"{c_code}┃  {title}{reset}\n"
            f"{c_code}┣{border}┫{reset}\n"
            f"{dim}{description}{reset}\n"
            f"{c_code}┗{border}┛{reset}\n"
            f"```"
        )
        await ctx.send(card)

    @commands.command(
        name="whembed",
        aliases=["nativeembed", "webhookembed"],
        help="Send a 100% real Discord Embed disguised as your account via channel webhook (requires Manage Webhooks).",
    )
    @commands.guild_only()
    async def whembed(self, ctx: commands.Context, title: str, description: str, hex_color: str = "5865F2"):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        try:
            color_int = int(hex_color.lstrip("#"), 16)
        except ValueError:
            color_int = 0x5865F2

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color(color_int),
        )

        try:
            webhooks = await ctx.channel.webhooks()
            webhook = next((w for w in webhooks if w.name == "GhostSelfbotEmbed"), None)
            if webhook is None:
                webhook = await ctx.channel.create_webhook(name="GhostSelfbotEmbed")

            await webhook.send(
                embed=embed,
                username=ctx.author.display_name,
                avatar_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None,
            )
        except discord.Forbidden:
            await ctx.send("`[Ghost Embeds]` Missing `Manage Webhooks` permission here. Falling back to ANSI card:", delete_after=4)
            await self.ghostembed(ctx, title, description, "cyan")
        except Exception as e:
            await ctx.send(f"`[Ghost Embeds]` Webhook error: `{e}`", delete_after=6)

    @commands.command(name="imgembed", help="Send a self-hosted OpenGraph image embed (or clean markdown link if no public_url).")
    async def imgembed(self, ctx: commands.Context, title: str, image_url: str, color: str = "5865F2"):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        base_url = self._get_self_hosted_url()
        if base_url:
            params = urlencode({"title": title, "image": image_url, "color": color.lstrip("#")})
            hidden_wall = "||​||" * 198
            return await ctx.send(f"{hidden_wall} {base_url}/og?{params}")

        await ctx.send(f"**{title}**\n{image_url}")

    @commands.command(name="ansitext", aliases=["coloredtext"], help="Send an ANSI colored codeblock (colors: red, green, yellow, blue, pink, cyan).")
    async def ansitext(self, ctx: commands.Context, color: str, *, text: str):
        ansi_codes = {
            "red": "\u001b[1;31m",
            "green": "\u001b[1;32m",
            "yellow": "\u001b[1;33m",
            "blue": "\u001b[1;34m",
            "pink": "\u001b[1;35m",
            "cyan": "\u001b[1;36m",
            "white": "\u001b[1;37m",
        }
        code = ansi_codes.get(color.lower(), "\u001b[1;36m")
        reset = "\u001b[0m"
        await ctx.message.edit(content=f"```ansi\n{code}{text}{reset}\n```")


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))