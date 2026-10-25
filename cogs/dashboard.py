import discord
from discord.ext import commands
import threading
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, session, redirect, render_template_string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timezone
from waitress import serve

# --- WEB LOGGER SETUP ---
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)
web_handler = RotatingFileHandler("web.log", maxBytes=5*1024*1024, backupCount=2)
web_handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
werkzeug_logger.addHandler(web_handler)
# ------------------------

app = Flask(__name__)
app.secret_key = os.urandom(24) 
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")

bot_instance = None

def get_tail(filepath, lines=100):
    if not os.path.exists(filepath): return "No log file generated yet."
    with open(filepath, "r", encoding="utf-8") as f:
        return "".join(f.readlines()[-lines:])

TAILWIND_CONFIG = """
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: { extend: { colors: { discord: { dark: '#202225', main: '#36393f', sidebar: '#2f3136', blurple: '#5865F2', green: '#57F287', red: '#ED4245' } } } }
  }
</script>
"""

LOGIN_HTML = f"""
<!DOCTYPE html>
<html>
<head><title>Login - BallzBot</title>{TAILWIND_CONFIG}</head>
<body class="bg-discord-dark flex items-center justify-center h-screen text-gray-200 font-sans">
    <div class="bg-discord-main p-8 rounded-lg shadow-lg w-96 text-center border border-gray-700">
        <h2 class="text-2xl font-bold text-white mb-6 tracking-wide">BALLZ<span class="text-discord-blurple">BOT</span></h2>
        <form method="POST" class="space-y-4">
            <input type="text" name="username" placeholder="Username" required class="w-full p-3 bg-discord-dark text-white rounded focus:outline-none focus:ring-2 focus:ring-discord-blurple border border-gray-700">
            <input type="password" name="password" placeholder="Password" required class="w-full p-3 bg-discord-dark text-white rounded focus:outline-none focus:ring-2 focus:ring-discord-blurple border border-gray-700">
            <button type="submit" class="w-full py-3 bg-discord-blurple hover:bg-indigo-500 text-white font-bold rounded transition-colors duration-200">Login</button>
        </form>
        {{% if error %}}<p class="text-discord-red mt-4 text-sm font-semibold">{{{{ error }}}}</p>{{% endif %}}
    </div>
</body>
</html>
"""

LAYOUT_HTML = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - BallzBot</title>
    {TAILWIND_CONFIG}
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-discord-dark text-gray-200 font-sans h-screen flex overflow-hidden">
    
    <!-- Sidebar -->
    <div class="w-64 bg-discord-sidebar flex flex-col justify-between shadow-xl hidden md:flex border-r border-gray-800">
        <div class="p-6">
            <h1 class="text-2xl font-black text-white tracking-widest mb-8">BALLZ<span class="text-discord-blurple">BOT</span></h1>
            <nav class="space-y-2">
                <a href="/" class="flex items-center space-x-3 p-3 rounded font-medium transition-colors {{{{ 'bg-discord-main text-white' if page == 'dashboard' else 'text-gray-400 hover:bg-gray-800 hover:text-white' }}}}">
                    <i class="fa-solid fa-chart-line {{{{ 'text-discord-blurple' if page == 'dashboard' else '' }}}} w-5"></i><span>Dashboard</span>
                </a>
                <a href="/logs/web" class="flex items-center space-x-3 p-3 rounded font-medium transition-colors {{{{ 'bg-discord-main text-white' if page == 'web_logs' else 'text-gray-400 hover:bg-gray-800 hover:text-white' }}}}">
                    <i class="fa-solid fa-globe {{{{ 'text-indigo-400' if page == 'web_logs' else '' }}}} w-5"></i><span>Web Traffic</span>
                </a>
                <a href="/logs/bot" class="flex items-center space-x-3 p-3 rounded font-medium transition-colors {{{{ 'bg-discord-main text-white' if page == 'bot_logs' else 'text-gray-400 hover:bg-gray-800 hover:text-white' }}}}">
                    <i class="fa-solid fa-terminal {{{{ 'text-green-400' if page == 'bot_logs' else '' }}}} w-5"></i><span>Bot Logs</span>
                </a>
                <a href="/config" class="flex items-center space-x-3 p-3 rounded font-medium transition-colors {{{{ 'bg-discord-main text-white' if page == 'config' else 'text-gray-400 hover:bg-gray-800 hover:text-white' }}}}">
                    <i class="fa-solid fa-gear {{{{ 'text-gray-300' if page == 'config' else '' }}}} w-5"></i><span>Config Panel</span>
                </a>
            </nav>
        </div>
        
        <div class="p-4 bg-discord-dark flex items-center justify-between border-t border-gray-800">
            <div class="flex items-center space-x-3 overflow-hidden">
                <img src="{{{{ avatar_url }}}}" class="w-10 h-10 rounded-full border-2 border-discord-green object-cover">
                <div class="truncate">
                    <p class="text-sm font-bold text-white truncate">{{{{ bot_name }}}}</p>
                    <p class="text-xs text-discord-green font-semibold">Online</p>
                </div>
            </div>
            <a href="/logout" class="text-gray-400 hover:text-discord-red transition-colors"><i class="fa-solid fa-right-from-bracket"></i></a>
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col h-full overflow-y-auto bg-discord-main">
        <div class="p-8">
            {{{{ content | safe }}}}
        </div>
    </div>
</body>
</html>
"""

VIEW_DASHBOARD = """
<div class="flex justify-between items-center mb-8">
    <h2 class="text-3xl font-bold text-white">System Overview</h2>
    <div class="flex items-center space-x-2 bg-discord-dark px-4 py-2 rounded-full border border-gray-700">
        <div class="w-3 h-3 bg-discord-green rounded-full animate-pulse"></div>
        <span class="text-sm font-semibold tracking-wide text-gray-300">Session Secure</span>
    </div>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
        <div class="flex justify-between items-center mb-4"><h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Uptime</h3><i class="fa-solid fa-clock text-discord-blurple text-xl"></i></div>
        <p class="text-2xl font-bold text-white" id="uptime-display">Loading...</p>
    </div>
    <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
        <div class="flex justify-between items-center mb-4"><h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Servers</h3><i class="fa-solid fa-server text-indigo-400 text-xl"></i></div>
        <p class="text-2xl font-bold text-white">{{ guild_count }}</p>
    </div>
    <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
        <div class="flex justify-between items-center mb-4"><h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Cmds Executed</h3><i class="fa-solid fa-terminal text-green-400 text-xl"></i></div>
        <p class="text-2xl font-bold text-white">{{ commands_executed }}</p>
    </div>
    <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
        <div class="flex justify-between items-center mb-4"><h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Risk Mode</h3><i class="fa-solid fa-shield-halved text-{{ 'discord-red' if risk_mode else 'discord-green' }} text-xl"></i></div>
        <p class="text-2xl font-bold text-{{ 'discord-red' if risk_mode else 'discord-green' }}">{{ 'ENABLED' if risk_mode else 'DISABLED' }}</p>
    </div>
</div>
<div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
    <h3 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Active Integrations</h3>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-discord-dark p-4 rounded border border-gray-700">
            <p class="text-gray-400 text-xs font-bold uppercase mb-1">Spotify Auth</p>
            <p class="text-lg text-white font-mono">{{ 'Linked & Active' if spotify_linked else 'Not Configured' }}</p>
        </div>
        <div class="bg-discord-dark p-4 rounded border border-gray-700">
            <p class="text-gray-400 text-xs font-bold uppercase mb-1">Spoofed Platform</p>
            <p class="text-lg text-white font-mono">{{ platform | upper }}</p>
        </div>
    </div>
</div>
<script>
    function updateUptime() {
        const start = {{ start_timestamp }};
        const now = Date.now() / 1000;
        let diff = Math.floor(now - start);
        let d = Math.floor(diff / 86400); diff %= 86400;
        let h = Math.floor(diff / 3600); diff %= 3600;
        let m = Math.floor(diff / 60);
        let s = diff % 60;
        document.getElementById('uptime-display').innerText = d + 'd ' + h + 'h ' + m + 'm ' + s + 's';
    }
    setInterval(updateUptime, 1000);
    updateUptime();
</script>
"""

VIEW_LOGS = """
<div class="flex justify-between items-center mb-4">
    <h2 class="text-3xl font-bold text-white">{{ title }}</h2>
    <a href="{{ request.path }}" class="bg-discord-dark hover:bg-gray-700 border border-gray-600 px-4 py-2 rounded text-sm font-semibold transition"><i class="fa-solid fa-rotate-right mr-2"></i>Refresh</a>
</div>
<div class="bg-[#000000] p-4 rounded-lg border border-gray-700 h-[70vh] overflow-y-auto shadow-inner">
    <pre class="text-green-400 font-mono text-sm whitespace-pre-wrap" id="log-box">{{ logs }}</pre>
</div>
<script>
    var logBox = document.getElementById('log-box');
    if(logBox) logBox.scrollTop = logBox.scrollHeight;
</script>
"""

VIEW_CONFIG = """
<div class="mb-6">
    <h2 class="text-3xl font-bold text-white">Bot Configuration</h2>
    <p class="text-gray-400 mt-2">Modify your runtime configurations. Settings save instantly to your config file.</p>
</div>
{% if success %}<div class="bg-discord-green text-black font-bold p-3 rounded mb-6"><i class="fa-solid fa-check-circle mr-2"></i>Configuration Saved Successfully.</div>{% endif %}
{% if error %}<div class="bg-discord-red text-white font-bold p-3 rounded mb-6"><i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ error }}</div>{% endif %}

<form method="POST" class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
            <label class="block text-gray-400 text-xs font-bold uppercase mb-2">Command Prefix</label>
            <input type="text" name="prefix" value="{{ config_data.get('prefix', '.') }}" class="w-full p-3 bg-discord-dark text-white rounded border border-gray-700 focus:outline-none focus:border-discord-blurple">
        </div>
        <div class="flex flex-col justify-center">
            <label class="block text-gray-400 text-xs font-bold uppercase mb-2">Risk Mode</label>
            <label class="inline-flex items-center cursor-pointer mt-1">
                <input type="checkbox" name="risk_mode" {% if config_data.get('risk_mode') %}checked{% endif %} class="form-checkbox h-6 w-6 text-discord-blurple bg-discord-dark border-gray-700 rounded focus:ring-0 cursor-pointer">
                <span class="ml-3 text-white font-medium">Enable Risky Commands (Mass DM, Spam)</span>
            </label>
        </div>
        <div>
            <label class="block text-gray-400 text-xs font-bold uppercase mb-2">Static QR Code 1 (Link)</label>
            <input type="text" name="qr" value="{{ config_data.get('Qr', '') }}" class="w-full p-3 bg-discord-dark text-white rounded border border-gray-700 focus:outline-none focus:border-discord-blurple">
        </div>
        <div>
            <label class="block text-gray-400 text-xs font-bold uppercase mb-2">Static QR Code 2 (Link)</label>
            <input type="text" name="qr2" value="{{ config_data.get('Qr2', '') }}" class="w-full p-3 bg-discord-dark text-white rounded border border-gray-700 focus:outline-none focus:border-discord-blurple">
        </div>
        <div class="md:col-span-2">
            <label class="block text-gray-400 text-xs font-bold uppercase mb-2">Vouch Server Link</label>
            <input type="text" name="server_link" value="{{ config_data.get('SERVER_Link', '') }}" class="w-full p-3 bg-discord-dark text-white rounded border border-gray-700 focus:outline-none focus:border-discord-blurple">
        </div>
    </div>
    
    <div>
        <label class="block text-gray-400 text-xs font-bold uppercase mb-2">Custom Emojis (JSON Format)</label>
        <textarea name="emojis" rows="12" class="w-full p-3 bg-discord-dark text-green-400 font-mono text-sm rounded border border-gray-700 focus:outline-none focus:border-discord-blurple">{{ emojis_json }}</textarea>
        <p class="text-xs text-gray-500 mt-2"><i class="fa-solid fa-triangle-exclamation mr-1"></i>Ensure this remains valid JSON formatting or changes will be rejected.</p>
    </div>
    
    <button type="submit" class="bg-discord-blurple hover:bg-indigo-500 text-white font-bold py-3 px-6 rounded transition-colors w-full md:w-auto">
        <i class="fa-solid fa-floppy-disk mr-2"></i>Save Configuration
    </button>
</form>
"""

def render_layout(page, content):
    avatar = bot_instance.user.display_avatar.url if bot_instance.user.display_avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
    return render_template_string(LAYOUT_HTML, content=content, page=page, bot_name=bot_instance.user.name, avatar_url=avatar)

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
        
    start_ts = bot_instance.start_time.timestamp()
    
    content = render_template_string(VIEW_DASHBOARD, 
        start_timestamp=start_ts,
        guild_count=len(bot_instance.guilds),
        commands_executed=bot_instance.commands_executed,
        risk_mode=bot_instance.config.get("risk_mode", False),
        platform=bot_instance.config.get("platform", "pc"),
        spotify_linked=bool(bot_instance.config.get("spotify_client_id"))
    )
    return render_layout("dashboard", content)

@app.route('/logs/web')
def web_logs():
    if not session.get('logged_in'): return redirect('/login')
    logs = get_tail("web.log")
    content = render_template_string(VIEW_LOGS, title="Web Traffic Logs", logs=logs)
    return render_layout("web_logs", content)

@app.route('/logs/bot')
def bot_logs():
    if not session.get('logged_in'): return redirect('/login')
    logs = get_tail("bot.log")
    content = render_template_string(VIEW_LOGS, title="Selfbot Execution Logs", logs=logs)
    return render_layout("bot_logs", content)

@app.route('/config', methods=['GET', 'POST'])
def config_panel():
    if not session.get('logged_in'): return redirect('/login')
    
    success = False
    error_msg = None
    
    try:
        if request.method == 'POST':
            bot_instance.config["prefix"] = request.form.get("prefix", ".")
            bot_instance.command_prefix = bot_instance.config["prefix"]
            bot_instance.config["Qr"] = request.form.get("qr", "")
            bot_instance.config["Qr2"] = request.form.get("qr2", "")
            bot_instance.config["SERVER_Link"] = request.form.get("server_link", "")
            bot_instance.config["risk_mode"] = request.form.get("risk_mode") == "on"
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(bot_instance.config, f, indent=4)
                
            raw_emojis = request.form.get("emojis", "").strip()
            if raw_emojis:
                try:
                    new_emojis = json.loads(raw_emojis)
                    if isinstance(new_emojis, dict):
                        if not isinstance(bot_instance.custom_emojis, dict):
                            bot_instance.custom_emojis = {}
                        bot_instance.custom_emojis.update(new_emojis)
                        with open("emojis.json", "w", encoding="utf-8") as f:
                            json.dump(bot_instance.custom_emojis, f, indent=4)
                    else:
                        error_msg = "Emojis field must be a valid JSON dictionary."
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON Formatting: {str(e)}"
            
            if not error_msg:
                success = True
    except Exception as e:
        error_msg = f"System Save Error: {str(e)}"
        werkzeug_logger.error(f"[Config Save Error] {e}")

    # Ensure it prints valid JSON to the frontend
    emojis_json = json.dumps(bot_instance.custom_emojis, indent=4) if isinstance(bot_instance.custom_emojis, dict) else "{}"
    content = render_template_string(VIEW_CONFIG, config_data=bot_instance.config, emojis_json=emojis_json, success=success, error=error_msg)
    return render_layout("config", content)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        user, pwd = request.form.get('username', ''), request.form.get('password', '')
        stored_user, stored_hash = bot_instance.config.get('dash_username'), bot_instance.config.get('dash_hash')
        
        if not stored_user or not stored_hash:
            return render_template_string(LOGIN_HTML, error="Dashboard credentials not configured.")
        if user == stored_user and check_password_hash(stored_hash, pwd):
            session['logged_in'] = True
            return redirect('/')
        else:
            return render_template_string(LOGIN_HTML, error="Authentication Failed.")
            
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/callback')
def spotify_callback():
    if not session.get('logged_in'): return redirect('/login')
    if request.args.get('code'):
        return f"<html><head><title>Spotify Linked</title>{TAILWIND_CONFIG}</head><body class='bg-discord-dark flex items-center justify-center h-screen text-gray-200 font-sans'><div class='bg-discord-main p-8 rounded-lg shadow-lg w-full max-w-lg text-center border border-gray-700'><h3 class='text-3xl font-bold text-discord-green mb-4'>Spotify Authorized!</h3><p class='text-gray-400 mb-6'>Copy the URL below and run it in Discord to complete setup:</p><code class='block bg-discord-dark p-4 rounded border border-gray-700 text-discord-blurple text-left break-all font-mono shadow-inner mb-6'>.spauth {request.url}</code><a href='/' class='px-6 py-3 bg-discord-blurple hover:bg-indigo-500 text-white font-bold rounded'>Return to Dashboard</a></div></body></html>"
    return redirect('/')

def run_app():
    werkzeug_logger.info("Starting production WSGI server on port 8080...")
    serve(app, host='0.0.0.0', port=8080, clear_untrusted_proxy_headers=False)

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global bot_instance
        bot_instance = bot
        
        raw_hash = self.bot.config.get("dash_hash", "")
        if raw_hash.startswith("raw:"):
            self.bot.config["dash_hash"] = generate_password_hash(raw_hash[4:])
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.bot.config, f, indent=4)
        
        self.server_thread = threading.Thread(target=run_app, daemon=True)
        self.server_thread.start()

async def setup(bot):
    await bot.add_cog(Dashboard(bot))