import discord
from discord.ext import commands
import threading
import os
import json
from flask import Flask, request, session, redirect, render_template_string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = os.urandom(24) 
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

bot_instance = None

TAILWIND_CONFIG = """
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          discord: { dark: '#202225', main: '#36393f', sidebar: '#2f3136', blurple: '#5865F2', green: '#57F287', red: '#ED4245' }
        }
      }
    }
  }
</script>
"""

LOGIN_HTML = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Login - BallzBot</title>
    {TAILWIND_CONFIG}
</head>
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

DASHBOARD_HTML = f"""
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
                <a href="#" class="flex items-center space-x-3 bg-discord-main p-3 rounded text-white font-medium hover:bg-gray-700 transition-colors"><i class="fa-solid fa-chart-line text-discord-blurple"></i><span>Dashboard</span></a>
            </nav>
        </div>
        
        <div class="p-4 bg-discord-dark flex items-center justify-between border-t border-gray-800">
            <div class="flex items-center space-x-3 overflow-hidden">
                <img src="{{{{ avatar_url }}}}" alt="Avatar" class="w-10 h-10 rounded-full border-2 border-discord-green object-cover">
                <div class="truncate">
                    <p class="text-sm font-bold text-white truncate">{{{{ bot_name }}}}</p>
                    <p class="text-xs text-discord-green font-semibold">Online</p>
                </div>
            </div>
            <a href="/logout" class="text-gray-400 hover:text-discord-red transition-colors" title="Logout"><i class="fa-solid fa-right-from-bracket"></i></a>
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col h-full overflow-y-auto bg-discord-main">
        <div class="p-8">
            
            <div class="flex justify-between items-center mb-8">
                <h2 class="text-3xl font-bold text-white">System Overview</h2>
                <div class="flex items-center space-x-2 bg-discord-dark px-4 py-2 rounded-full border border-gray-700">
                    <div class="w-3 h-3 bg-discord-green rounded-full animate-pulse"></div>
                    <span class="text-sm font-semibold tracking-wide text-gray-300">Session Secure</span>
                </div>
            </div>

            <!-- Stats Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                
                <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Uptime</h3>
                        <i class="fa-solid fa-clock text-discord-blurple text-xl"></i>
                    </div>
                    <p class="text-2xl font-bold text-white">{{{{ uptime }}}}</p>
                </div>
                
                <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Servers</h3>
                        <i class="fa-solid fa-server text-indigo-400 text-xl"></i>
                    </div>
                    <p class="text-2xl font-bold text-white">{{{{ guild_count }}}}</p>
                </div>

                <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Cmds Executed</h3>
                        <i class="fa-solid fa-terminal text-green-400 text-xl"></i>
                    </div>
                    <p class="text-2xl font-bold text-white">{{{{ commands_executed }}}}</p>
                </div>

                <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-gray-400 font-semibold text-sm uppercase tracking-wider">Risk Mode</h3>
                        <i class="fa-solid fa-shield-halved text-{{{{ 'discord-red' if risk_mode else 'discord-green' }}}} text-xl"></i>
                    </div>
                    <p class="text-2xl font-bold text-{{{{ 'discord-red' if risk_mode else 'discord-green' }}}}">{{{{ 'ENABLED' if risk_mode else 'DISABLED' }}}}</p>
                </div>

            </div>

            <!-- Bot Settings Card -->
            <div class="bg-discord-sidebar p-6 rounded-lg border border-gray-800 shadow-md">
                <h3 class="text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2">Active Configuration</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-discord-dark p-4 rounded border border-gray-700">
                        <p class="text-gray-400 text-xs font-bold uppercase mb-1">Command Prefix</p>
                        <p class="text-lg text-white font-mono">{{{{ prefix }}}}</p>
                    </div>
                    <div class="bg-discord-dark p-4 rounded border border-gray-700">
                        <p class="text-gray-400 text-xs font-bold uppercase mb-1">Spotify Auth</p>
                        <p class="text-lg text-white font-mono">{{{{ 'Linked' if spotify_linked else 'Not Configured' }}}}</p>
                    </div>
                </div>
            </div>

        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect('/login')
        
    delta = datetime.now(timezone.utc) - bot_instance.start_time
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime = f"{delta.days}d {hours}h {minutes}m"
    
    avatar = bot_instance.user.display_avatar.url if bot_instance.user.display_avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
    risk = bot_instance.config.get("risk_mode", False)
    sp_linked = bool(bot_instance.config.get("spotify_client_id"))

    return render_template_string(
        DASHBOARD_HTML, 
        bot_name=bot_instance.user.name,
        avatar_url=avatar,
        uptime=uptime,
        guild_count=len(bot_instance.guilds),
        commands_executed=bot_instance.commands_executed,
        risk_mode=risk,
        prefix=bot_instance.command_prefix,
        spotify_linked=sp_linked
    )

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        user = request.form.get('username', '')
        pwd = request.form.get('password', '')
        
        stored_user = bot_instance.config.get('dash_username')
        stored_hash = bot_instance.config.get('dash_hash')
        
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
    if not session.get('logged_in'):
        return redirect('/login')
        
    code = request.args.get('code')
    if code:
        return f"""
        <html>
        <head>
            <title>Spotify Linked</title>
            {TAILWIND_CONFIG}
        </head>
        <body class="bg-discord-dark flex items-center justify-center h-screen text-gray-200 font-sans">
            <div class="bg-discord-main p-8 rounded-lg shadow-lg w-full max-w-lg text-center border border-gray-700">
                <h3 class="text-3xl font-bold text-discord-green mb-4">Spotify Authorized!</h3>
                <p class="text-gray-400 mb-6">Copy the URL below and run it in Discord to complete setup:</p>
                <code class="block bg-discord-dark p-4 rounded border border-gray-700 text-discord-blurple text-left break-all font-mono shadow-inner mb-6">.spauth {request.url}</code>
                <a href="/" class="px-6 py-3 bg-discord-blurple hover:bg-indigo-500 text-white font-bold rounded transition-colors duration-200">Return to Dashboard</a>
            </div>
        </body>
        </html>
        """
    return redirect('/')

def run_app():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

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