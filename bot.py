import os
import json
import time
from datetime import datetime, timezone
import discord
from discord.ext import commands
import colorama
from pystyle import Center, Colorate, Colors

colorama.init()

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_json("config.json")
custom_icons = load_json("emojis.json")

# Ensure required keys exist
config.setdefault("risk_mode", False)
config.setdefault("vouch_channels", {})
config.setdefault("auto_slash", {})
config.setdefault("auto_mod", {})

pref = config.get("platform", "pc").lower()
spoof_kwargs = {}
if pref == "mobile":
    spoof_kwargs = {"os": "Android", "browser": "Discord Android", "device": "Android"}
elif pref == "ps5":
    spoof_kwargs = {"os": "PlayStation", "browser": "Discord Client", "device": "PlayStation 5"}
elif pref == "xbox":
    spoof_kwargs = {"os": "Windows", "browser": "Discord Client", "device": "Xbox Series X"}
elif pref == "vr":
    spoof_kwargs = {"os": "Windows", "browser": "Discord Client", "device": "Discord VR Headset"}
elif pref == "web":
    spoof_kwargs = {"os": "Windows", "browser": "Chrome", "device": "Windows"}

raj = commands.Bot(
    description="SELFBOT CREATED BY knimmi",
    command_prefix=config.get("prefix", "."),
    self_bot=True,
    **spoof_kwargs
)

# Global attributes attached to bot instance
raj.config = config
raj.custom_emojis = custom_icons
raj.start_time = datetime.now(timezone.utc)
raj.commands_executed = 0
raj.remove_command("help")

def check_risk(ctx) -> bool:
    """Returns True if command can proceed, False if blocked by risk settings."""
    if not raj.config.get("risk_mode", False):
        err = raj.custom_emojis.get("error", "")
        raj.loop.create_task(
            ctx.send(f"{err} **Command Blocked:** Risk Mode is currently **Disabled**. Enable it with `{raj.command_prefix}risk`.")
        )
        return False
    return True

raj.check_risk = check_risk

@raj.event
async def on_ready():
    print(Center.XCenter(Colorate.Vertical(Colors.green_to_yellow,
        f"""[=]-----------------------------------------------------------------------[=]
[  BallzBot V2  |  MADE BY :- knimmi  |  LOGGED IN AS :- {raj.user.name}  ]
[=]-----------------------------------------------------------------------[=]""", 1)))

@raj.event
async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await raj.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

@raj.event
async def on_command_completion(ctx):
    raj.commands_executed += 1

@raj.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        err_emoji = raj.custom_emojis.get('error', '')
        try:
            await ctx.send(f"{err_emoji} **Missing argument:** `{error.param.name}` is required.")
        except:
            pass

if __name__ == "__main__":
    raj.run(config.get("token"))