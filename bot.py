import os
import json
import time
from datetime import datetime, timezone
import discord
from discord.ext import commands
import colorama
from pystyle import Center, Colorate, Colors
from discord.gateway import DiscordWebSocket
import logging
from logging.handlers import RotatingFileHandler

colorama.init()

# --- BOT LOGGER SETUP ---
bot_logger = logging.getLogger("BallzBot")
bot_logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler("bot.log", maxBytes=5*1024*1024, backupCount=2)
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
bot_logger.addHandler(file_handler)
# ------------------------

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_json("config.json")
custom_icons = load_json("emojis.json")

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

# --- GATEWAY MONKEYPATCH FOR PLATFORM SPOOFING ---
_original_send = DiscordWebSocket.send_as_json

async def patched_send(self, data):
    if data.get("op") == 2 and "d" in data and "properties" in data["d"]: 
        if spoof_kwargs:
            props = data["d"]["properties"]
            props["os"] = spoof_kwargs.get("os", props.get("os"))
            props["browser"] = spoof_kwargs.get("browser", props.get("browser"))
            props["device"] = spoof_kwargs.get("device", props.get("device"))
            props["$os"] = spoof_kwargs.get("os", props.get("$os", props.get("os")))
            props["$browser"] = spoof_kwargs.get("browser", props.get("$browser", props.get("browser")))
            props["$device"] = spoof_kwargs.get("device", props.get("$device", props.get("device")))
            if spoof_kwargs.get("browser") != "Chrome":
                props.pop("browser_user_agent", None)
                props.pop("browser_version", None)
                props.pop("os_version", None)
    return await _original_send(self, data)

DiscordWebSocket.send_as_json = patched_send
# -------------------------------------------------

raj = commands.Bot(
    description="SELFBOT CREATED BY knimmi",
    command_prefix=config.get("prefix", "."),
    self_bot=True,
    **spoof_kwargs 
)

raj.config = config
raj.custom_emojis = custom_icons
raj.start_time = datetime.now(timezone.utc)
raj.commands_executed = 0
raj.bot_logger = bot_logger 
raj.remove_command("help")

# --- GLOBAL RATE LIMITER (Protect Account from Spam Bans) ---
raj._global_cooldown = commands.CooldownMapping.from_cooldown(1, 1.5, commands.BucketType.user)

@raj.check
async def global_cooldown_check(ctx):
    bucket = raj._global_cooldown.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raj.bot_logger.warning(f"Rate Limit Shield: Dropped command '{ctx.message.content}' (Wait {retry_after:.2f}s)")
        return False

    if not raj.config.get("risk_mode", False) and ctx.command and ctx.command.name in ["spam", "clear", "dmall", "massdmfriends", "abuser"]:
        err = raj.custom_emojis.get("error", "")
        raj.loop.create_task(
            ctx.send(f"{err} **Command Blocked:** Risk Mode is currently **Disabled**. Enable it with `{raj.command_prefix}risk`.")
        )
        raj.bot_logger.warning(f"Blocked risky command: {ctx.message.content}")
        return False
        
    return True
# ------------------------------------------------------------

@raj.event
async def on_ready():
    bot_logger.info(f"Bot logged in successfully as {raj.user.name}")
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
                bot_logger.error(f"Failed to load {filename}: {e}")
                print(f"Failed to load {filename}: {e}")

@raj.event
async def on_command_completion(ctx):
    raj.commands_executed += 1
    loc = f"#{ctx.channel.name}" if hasattr(ctx.channel, 'name') else "DM"
    raj.bot_logger.info(f"CMD Executed | {loc} | {ctx.message.content}")

@raj.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
        
    if isinstance(error, commands.CommandOnCooldown):
        raj.bot_logger.warning(f"Command Cooldown Hit: {error}")
        return
        
    raj.bot_logger.error(f"CMD Error | {ctx.message.content} | {error}")
    
    if isinstance(error, commands.MissingRequiredArgument):
        err_emoji = raj.custom_emojis.get('error', '')
        try: await ctx.send(f"{err_emoji} **Missing argument:** `{error.param.name}` is required.")
        except: pass

if __name__ == "__main__":
    raj.run(config.get("token"))