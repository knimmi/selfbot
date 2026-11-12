import base64
import datetime
import html
import json
import os
import secrets
import time
from collections import deque
from pathlib import Path

import discord
from aiohttp import web
from discord.ext import commands


class Dashboard(commands.Cog, name="Dashboard"):
    """Ghost-styled Web UI Dashboard running inside the bot's async event loop."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

        self.json_files = {
            "config": Path("config.json"),
            "afk": Path("afk.json"),
            "am": Path("am.json"),
            "ar": Path("ar.json"),
            "emojis": Path("emojis.json"),
        }

        # Automatically resolve credentials created by install.sh (.env, config.json, auth.json, or Docker ENV)
        creds = self._load_credentials()
        self.host = creds["host"]
        self.port = creds["port"]
        self.username = creds["username"]
        self.password = creds["password"]
        self.creds_source = creds["source"]

        self.activity_feed: deque[dict] = deque(maxlen=200)
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None

    def _load_credentials(self) -> dict:
        """Load Web UI username, password, host, and port from .env, config.json, dashboard.json, or ENV."""
        env_file_vars = {}
        env_path = Path(".env")
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_file_vars[k.strip()] = v.strip().strip('"').strip("'")
            except Exception:
                pass

        def get_env(*keys):
            for k in keys:
                val = os.getenv(k) or env_file_vars.get(k)
                if val:
                    return val
            return None

        config_data = {}
        for cfg_name in ("dashboard.json", "auth.json", "config.json"):
            p = Path(cfg_name)
            if p.exists():
                try:
                    loaded = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        config_data.update(loaded)
                except Exception:
                    pass

        # Support nested {"dashboard": {"username": "...", "password": "..."}} or top-level keys
        nested = (
            config_data.get("dashboard")
            or config_data.get("webui")
            or config_data.get("web")
            or {}
        )
        if not isinstance(nested, dict):
            nested = {}

        username = (
            get_env("DASHBOARD_USER", "DASHBOARD_USERNAME", "WEBUI_USER", "WEB_USER", "PANEL_USER", "USERNAME")
            or nested.get("username")
            or nested.get("user")
            or config_data.get("dashboard_username")
            or config_data.get("dashboard_user")
            or config_data.get("web_username")
            or config_data.get("web_user")
            or config_data.get("webui_user")
            or config_data.get("username")
            or "admin"
        )

        password = (
            get_env("DASHBOARD_PASS", "DASHBOARD_PASSWORD", "WEBUI_PASS", "WEB_PASS", "PANEL_PASS", "PASSWORD")
            or nested.get("password")
            or nested.get("pass")
            or config_data.get("dashboard_password")
            or config_data.get("dashboard_pass")
            or config_data.get("web_password")
            or config_data.get("web_pass")
            or config_data.get("webui_pass")
            or config_data.get("password")
            or "changeme"
        )

        port_raw = (
            get_env("DASHBOARD_PORT", "WEBUI_PORT", "WEB_PORT", "PORT")
            or nested.get("port")
            or config_data.get("dashboard_port")
            or config_data.get("web_port")
            or 8085
        )
        host = (
            get_env("DASHBOARD_HOST", "WEBUI_HOST", "HOST")
            or nested.get("host")
            or config_data.get("dashboard_host")
            or "0.0.0.0"
        )

        source = ".env / Docker ENV" if get_env("DASHBOARD_USER", "DASHBOARD_PASS", "WEBUI_USER", "WEBUI_PASS", "PASSWORD") else "config.json"
        return {
            "username": str(username),
            "password": str(password),
            "port": int(port_raw),
            "host": str(host),
            "source": source,
        }

    async def cog_load(self):
        self.bot.loop.create_task(self.start_webserver())

    def cog_unload(self):
        if self.runner:
            self.bot.loop.create_task(self.runner.cleanup())

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        self.activity_feed.appendleft({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "event": "COMMAND",
            "detail": f"{ctx.command.qualified_name} in {getattr(ctx.channel, 'name', 'DM')}",
        })

    # =========================================================================
    # BASIC AUTH MIDDLEWARE
    # =========================================================================

    @web.middleware
    async def auth_middleware(self, request: web.Request, handler):
        # Allow Discord's OpenGraph link crawler to fetch /og without Basic Auth
        if request.path == "/og":
            return await handler(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return web.Response(
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Ghost Selfbot Dashboard"'},
                text="Unauthorized",
            )
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            user, pwd = decoded.split(":", 1)
        except Exception:
            return web.Response(status=401, text="Invalid Authorization Header")

        if not (secrets.compare_digest(user, self.username) and secrets.compare_digest(pwd, self.password)):
            return web.Response(
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Ghost Selfbot Dashboard"'},
                text="Invalid credentials",
            )
        return await handler(request)

    # =========================================================================
    # API ROUTES
    # =========================================================================

    async def api_overview(self, request: web.Request):
        user = self.bot.user
        uptime_sec = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)

        cogs_info = []
        for cog_name, cog in self.bot.cogs.items():
            cmds = [{"name": c.name, "help": c.help or "No description"} for c in cog.get_commands()]
            cogs_info.append({"name": cog_name, "commands": cmds})

        # Fetch snipe & surveillance logs from modular Sniper and Surveillance cogs
        sniper_cog = self.bot.get_cog("Sniper")
        surv_cog = self.bot.get_cog("Surveillance")
        combined_feed = []
        if sniper_cog and hasattr(sniper_cog, "snipe_feed"):
            combined_feed.extend(list(sniper_cog.snipe_feed)[:40])
        if surv_cog and hasattr(surv_cog, "tracking_feed"):
            combined_feed.extend(list(surv_cog.tracking_feed)[:40])

        return web.json_response({
            "ready": self.bot.is_ready(),
            "username": str(user) if user else "Connecting...",
            "user_id": str(user.id) if user else "-",
            "avatar": str(user.display_avatar.url) if user and user.display_avatar else "",
            "ping_ms": round(self.bot.latency * 1000, 1) if self.bot.latency else 0,
            "guilds": len(self.bot.guilds),
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "prefix": str(self.bot.command_prefix) if isinstance(self.bot.command_prefix, str) else ".",
            "creds_source": self.creds_source,
            "cogs": cogs_info,
            "activity": list(self.activity_feed)[:50],
            "surveillance": combined_feed[:50],
        })

    async def api_get_file(self, request: web.Request):
        name = request.match_info.get("name", "config")
        path = self.json_files.get(name)
        if not path:
            return web.json_response({"error": "Unknown config file"}, status=400)
        if not path.exists():
            return web.json_response({})
        try:
            return web.json_response(json.loads(path.read_text(encoding="utf-8")))
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def api_save_file(self, request: web.Request):
        name = request.match_info.get("name", "config")
        path = self.json_files.get(name)
        if not path:
            return web.json_response({"error": "Unknown config file"}, status=400)
        data = await request.json()
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        self.activity_feed.appendleft({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "event": "CONFIG",
            "detail": f"Saved {path.name} via Web UI",
        })
        return web.json_response({"status": "saved"})

    async def api_reload_cog(self, request: web.Request):
        body = await request.json()
        ext = body.get("extension", "")
        if not ext.startswith("cogs."):
            ext = f"cogs.{ext.lower()}"
        try:
            await self.bot.reload_extension(ext)
            self.activity_feed.appendleft({
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "event": "COG RELOAD",
                "detail": f"Reloaded {ext}",
            })
            return web.json_response({"status": "reloaded", "extension": ext})
        except commands.ExtensionNotLoaded:
            try:
                await self.bot.load_extension(ext)
                return web.json_response({"status": "loaded", "extension": ext})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def api_presence(self, request: web.Request):
        body = await request.json()
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }
        activity_map = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
        }
        status = status_map.get(body.get("status", "online"), discord.Status.online)
        act_type = activity_map.get(body.get("type", "playing"), discord.ActivityType.playing)
        text = body.get("text", "").strip()

        activity = discord.Activity(type=act_type, name=text) if text else None
        await self.bot.change_presence(status=status, activity=activity)
        self.activity_feed.appendleft({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "event": "PRESENCE",
            "detail": f"Set {body.get('status')} / {text or 'Cleared'}",
        })
        return web.json_response({"status": "updated"})

    async def og_embed_page(self, request: web.Request):
        """Self-hosted OpenGraph meta-tag generator (replaces benny.fun completely)."""
        title = html.escape(request.query.get("title", "Ghost Selfbot"))
        desc = html.escape(request.query.get("description", ""))
        color = html.escape(request.query.get("color", "5865F2").lstrip("#"))
        image = html.escape(request.query.get("image", ""))

        img_tags = (
            f'<meta property="og:image" content="{image}" />\n'
            f'<meta name="twitter:card" content="summary_large_image" />'
            if image else ""
        )
        og_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta name="theme-color" content="#{color}" />
  {img_tags}
</head>
<body style="background:#0b0d13;color:#e2e8f0;font-family:sans-serif;padding:2rem;">
  <h2>{title}</h2>
  <p>{desc}</p>
</body>
</html>"""
        return web.Response(text=og_html, content_type="text/html")

    async def index_page(self, request: web.Request):
        return web.Response(text=HTML_TEMPLATE, content_type="text/html")

    async def start_webserver(self):
        await self.bot.wait_until_ready()
        app = web.Application(middlewares=[self.auth_middleware])
        app.router.add_get("/", self.index_page)
        app.router.add_get("/og", self.og_embed_page)
        app.router.add_get("/api/overview", self.api_overview)
        app.router.add_get("/api/file/{name}", self.api_get_file)
        app.router.add_post("/api/file/{name}", self.api_save_file)
        app.router.add_post("/api/cog/reload", self.api_reload_cog)
        app.router.add_post("/api/presence", self.api_presence)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        print(f"[Ghost Dashboard] Web UI listening on http://{self.host}:{self.port} (Auth loaded from {self.creds_source})")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Ghost Selfbot Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background-color: #0b0d13; color: #e2e8f0; font-family: 'Inter', system-ui, sans-serif; }
    .card { background-color: #131722; border: 1px solid #1f2637; border-radius: 0.75rem; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }
  </style>
</head>
<body class="min-h-screen p-6">
  <!-- Toast Notification Banner -->
  <div id="toast" class="fixed bottom-5 right-5 hidden px-4 py-3 rounded-lg shadow-lg border text-sm font-medium z-50 transition-all"></div>

  <div class="max-w-7xl mx-auto space-y-6">
    <!-- Top Account Bar -->
    <div class="card p-5 flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-4">
        <img id="avatar" src="https://cdn.discordapp.com/embed/avatars/0.png" class="w-14 h-14 rounded-full border-2 border-indigo-500" />
        <div>
          <div class="flex items-center gap-2">
            <h1 id="username" class="text-xl font-bold text-white">Loading...</h1>
            <span class="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">ONLINE</span>
          </div>
          <p class="text-xs text-slate-400 mt-0.5">ID: <span id="user_id">-</span> • Auth: <span id="creds_source" class="text-indigo-400">-</span></p>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-6 text-center">
        <div>
          <p class="text-xs text-slate-400 uppercase">Latency</p>
          <p id="ping" class="text-lg font-bold text-indigo-400">- ms</p>
        </div>
        <div>
          <p class="text-xs text-slate-400 uppercase">Servers</p>
          <p id="guilds" class="text-lg font-bold text-indigo-400">-</p>
        </div>
        <div>
          <p class="text-xs text-slate-400 uppercase">Uptime</p>
          <p id="uptime" class="text-lg font-bold text-indigo-400">-</p>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex gap-2 border-b border-slate-800 pb-3">
      <button onclick="switchTab('overview')" id="tab-overview" class="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white">Dashboard & Presence</button>
      <button onclick="switchTab('commands')" id="tab-commands" class="px-4 py-2 rounded-lg text-sm font-medium bg-slate-800/70 text-slate-300 hover:bg-slate-800">Cogs & Commands</button>
      <button onclick="switchTab('surveillance')" id="tab-surveillance" class="px-4 py-2 rounded-lg text-sm font-medium bg-slate-800/70 text-slate-300 hover:bg-slate-800">Ghost Surveillance & Snipes</button>
      <button onclick="switchTab('configs')" id="tab-configs" class="px-4 py-2 rounded-lg text-sm font-medium bg-slate-800/70 text-slate-300 hover:bg-slate-800">JSON Config Editor</button>
    </div>

    <!-- TAB 1: Overview & Presence -->
    <div id="view-overview" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-5 space-y-4">
        <h2 class="text-base font-semibold text-white">Rich Presence & Status Controller</h2>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-slate-400">Status</label>
            <select id="pres-status" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
              <option value="online">Online</option>
              <option value="idle">Idle</option>
              <option value="dnd">Do Not Disturb</option>
              <option value="invisible">Invisible</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-slate-400">Activity Type</label>
            <select id="pres-type" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm">
              <option value="playing">Playing</option>
              <option value="listening">Listening to</option>
              <option value="watching">Watching</option>
              <option value="competing">Competing in</option>
            </select>
          </div>
        </div>
        <div>
          <label class="text-xs text-slate-400">Activity Text (leave blank to clear)</label>
          <input id="pres-text" type="text" placeholder="Ghost v4 Selfbot" class="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm" />
        </div>
        <button onclick="updatePresence()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg text-sm transition">Update Presence</button>
      </div>

      <div class="card p-5 flex flex-col">
        <h2 class="text-base font-semibold text-white mb-3">Live Activity Log</h2>
        <div id="activity-list" class="space-y-2 overflow-y-auto max-h-64 text-xs font-mono"></div>
      </div>
    </div>

    <!-- TAB 2: Cogs & Commands -->
    <div id="view-commands" class="hidden space-y-4">
      <div class="card p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-sm font-semibold text-white">Hot-Reload Any Cog Extension</h2>
          <p class="text-xs text-slate-400">Reload or load a file inside <code>cogs/</code> (e.g. <code>sniper</code>, <code>surveillance</code>, <code>trolling</code>, <code>embeds</code>, <code>backup</code>, <code>account</code>).</p>
        </div>
        <div class="flex gap-2">
          <input id="cog-input" type="text" placeholder="e.g. sniper" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm" />
          <button onclick="reloadCog()" class="bg-indigo-600 hover:bg-indigo-500 px-4 py-1.5 rounded-lg text-sm font-medium">Reload</button>
        </div>
      </div>
      <div id="cogs-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
    </div>

    <!-- TAB 3: Surveillance & Snipes -->
    <div id="view-surveillance" class="hidden card p-5">
      <h2 class="text-base font-semibold text-white mb-3">Real-Time Snipes & Tracked User Feed</h2>
      <div id="surveillance-list" class="space-y-3 max-h-[500px] overflow-y-auto font-mono text-xs"></div>
    </div>

    <!-- TAB 4: JSON Config Editor -->
    <div id="view-configs" class="hidden card p-5 space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex gap-2">
          <button onclick="loadJsonFile('config')" class="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono">config.json</button>
          <button onclick="loadJsonFile('afk')" class="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono">afk.json</button>
          <button onclick="loadJsonFile('am')" class="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono">am.json</button>
          <button onclick="loadJsonFile('ar')" class="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono">ar.json</button>
          <button onclick="loadJsonFile('emojis')" class="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono">emojis.json</button>
        </div>
        <button onclick="saveJsonFile()" class="bg-emerald-600 hover:bg-emerald-500 px-4 py-1.5 rounded-lg text-sm font-medium">Save Active File</button>
      </div>
      <p class="text-xs text-slate-400">Editing: <code id="current-file-label" class="text-indigo-400">config.json</code></p>
      <textarea id="json-editor" class="w-full h-96 bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-emerald-300 focus:outline-none"></textarea>
    </div>
  </div>

  <script>
    let currentFile = 'config';

    function showToast(message, isError = false) {
      const toast = document.getElementById('toast');
      toast.textContent = message;
      toast.className = isError
        ? 'fixed bottom-5 right-5 px-4 py-3 rounded-lg shadow-lg border text-sm font-medium z-50 bg-rose-950 border-rose-700 text-rose-200'
        : 'fixed bottom-5 right-5 px-4 py-3 rounded-lg shadow-lg border text-sm font-medium z-50 bg-emerald-950 border-emerald-700 text-emerald-200';
      setTimeout(() => toast.classList.add('hidden'), 3500);
    }

    function switchTab(tab) {
      ['overview', 'commands', 'surveillance', 'configs'].forEach(t => {
        document.getElementById('view-' + t).classList.toggle('hidden', t !== tab);
        const btn = document.getElementById('tab-' + t);
        btn.className = t === tab
          ? 'px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white'
          : 'px-4 py-2 rounded-lg text-sm font-medium bg-slate-800/70 text-slate-300 hover:bg-slate-800';
      });
    }

    async function refreshOverview() {
      const res = await fetch('/api/overview');
      const data = await res.json();
      document.getElementById('username').textContent = data.username;
      document.getElementById('user_id').textContent = data.user_id;
      document.getElementById('creds_source').textContent = data.creds_source || 'config';
      if (data.avatar) document.getElementById('avatar').src = data.avatar;
      document.getElementById('ping').textContent = data.ping_ms + ' ms';
      document.getElementById('guilds').textContent = data.guilds;
      document.getElementById('uptime').textContent = data.uptime;

      const actEl = document.getElementById('activity-list');
      actEl.innerHTML = data.activity.length
        ? data.activity.map(a => `<div class="p-2 rounded bg-slate-900/80 border border-slate-800"><span class="text-slate-500">[${a.time}]</span> <span class="text-indigo-400 font-bold">${a.event}</span>: ${a.detail}</div>`).join('')
        : '<p class="text-slate-500">No commands executed yet.</p>';

      const cogsEl = document.getElementById('cogs-grid');
      cogsEl.innerHTML = data.cogs.map(cog => `
        <div class="card p-4 space-y-2">
          <div class="flex justify-between items-center border-b border-slate-800 pb-2">
            <h3 class="font-bold text-indigo-400">${cog.name}</h3>
            <span class="text-xs bg-slate-800 px-2 py-0.5 rounded">${cog.commands.length} cmds</span>
          </div>
          <div class="space-y-1 max-h-44 overflow-y-auto text-xs">
            ${cog.commands.map(c => `<div><code class="text-emerald-400 font-semibold">${c.name}</code> <span class="text-slate-400">- ${c.help}</span></div>`).join('')}
          </div>
        </div>
      `).join('');

      const survEl = document.getElementById('surveillance-list');
      survEl.innerHTML = data.surveillance.length
        ? data.surveillance.map(s => `
          <div class="p-3 rounded bg-slate-900 border border-slate-800">
            <div class="flex justify-between text-slate-400 mb-1">
              <span><strong class="${s.type === 'DELETE' ? 'text-rose-400' : (s.type === 'EDIT' ? 'text-amber-400' : 'text-indigo-400')}">[${s.type}]</strong> ${s.author} in ${s.guild_name} (#${s.channel_name})</span>
              <span>${s.timestamp}</span>
            </div>
            ${s.type === 'EDIT'
              ? `<div class="text-rose-300">Before: ${s.before}</div><div class="text-emerald-300">After: ${s.after}</div>`
              : `<div class="text-slate-200">${s.content}</div>`}
          </div>
        `).join('')
        : '<p class="text-slate-500">No deleted, edited, or tracked messages captured yet.</p>';
    }

    async function updatePresence() {
      const payload = {
        status: document.getElementById('pres-status').value,
        type: document.getElementById('pres-type').value,
        text: document.getElementById('pres-text').value
      };
      await fetch('/api/presence', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
      showToast('Rich Presence updated!');
      refreshOverview();
    }

    async function reloadCog() {
      const ext = document.getElementById('cog-input').value.trim();
      if (!ext) return;
      const res = await fetch('/api/cog/reload', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({extension: ext}) });
      const data = await res.json();
      if (data.error) {
        showToast('Error: ' + data.error, true);
      } else {
        showToast('Success: ' + data.status + ' ' + data.extension);
      }
      refreshOverview();
    }

    async function loadJsonFile(name) {
      currentFile = name;
      document.getElementById('current-file-label').textContent = name + '.json';
      const res = await fetch('/api/file/' + name);
      const data = await res.json();
      document.getElementById('json-editor').value = JSON.stringify(data, null, 4);
    }

    async function saveJsonFile() {
      try {
        const parsed = JSON.parse(document.getElementById('json-editor').value);
        await fetch('/api/file/' + currentFile, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(parsed)
        });
        showToast('Saved ' + currentFile + '.json!');
      } catch (e) {
        showToast('Invalid JSON: ' + e.message, true);
      }
    }

    loadJsonFile('config');
    refreshOverview();
    setInterval(refreshOverview, 3000);
  </script>
</body>
</html>
"""


async def setup(bot: commands.Bot):
    await bot.add_cog(Dashboard(bot))