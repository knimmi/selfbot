import os
import json
import discord
from discord.ext import commands
import colorama
from pystyle import Center, Colorate, Colors

colorama.init()

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# Load configuration globally
config = load_json("config.json")
custom_icons = load_json("emojis.json")

# Platform Spoofing Setup
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

# Attach variables to bot so cogs can use them
raj.config = config
raj.custom_emojis = custom_icons
raj.remove_command("help")

@raj.event
async def on_ready():
    print(Center.XCenter(Colorate.Vertical(Colors.green_to_yellow,
        f"""[=]-----------------------------------------------------------------------[=]
[  SELFCORD V1  |  MADE BY :- knimmi  |  LOGGED IN AS :- {raj.user.name}  ]
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

# Global Error Handler
@raj.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return # Silently ignore typos
    
    if isinstance(error, commands.MissingRequiredArgument):
        err_emoji = raj.custom_emojis.get('error', '❌')
        try:
            await ctx.send(f"{err_emoji} **Missing argument:** You need to provide `{error.param.name}`.")
        except: pass

if __name__ == "__main__":
    raj.run(config.get("token"))