@nightyScript(
    name="Honeypot",
    author="factz",
    description="Advanced honeypot & bait channel defense system with channel pool picker, granular role/user/permission whitelisting, automated actions (delete, kick, ban, timeout), live telemetry, and incident logging.",
    usage="UI Script — opens in Honeypot tab. Chat commands: <p>honeypot status | on | off | add <ch_id> | remove <ch_id> | clear"
)
def honeypot_script():
    """
    HONEYPOT DEFENSE SYSTEM
    -----------------------
    Monitors designated bait / trap channels in real time.
    When unauthorized users post a message in any watched honeypot channel,
    automated moderation actions are deployed based on your configuration.

    FEATURES:
    - Telemetry & Status: Wide overview card with real-time statistics counters.
    - Channel Pool: Select server and manage monitored channels.
    - Actions: Delete Message, Kick, Ban (with configurable message history deletion), and Timeout.
    - Permissions & Whitelist: Ignore Administrator, Manage Server, Manage Channels, Manage Messages, Kick/Ban perms, Bots, and custom Users & Roles.
    - Active Pools & Whitelists: Dedicated management card with overview and single-click removal.
    - Incident Logs & Inspector: Searchable table and detailed inspector card.
    """

    import os
    import sys
    import json
    import random
    import asyncio
    import traceback
    import subprocess
    from pathlib import Path
    from datetime import datetime, timedelta, timezone

    try:
        import discord
    except ImportError:
        discord = None

    # ==================== CONSTANTS & PERSISTENCE ====================
    SCRIPT_NAME = "Honeypot"
    JSON_DIR = Path(getScriptsPath()) / "json"
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE = JSON_DIR / "honeypot_settings.json"

    DEFAULT_SETTINGS = {
        "enabled": True,
        "target_guild_id": "",
        "watched_channels": [],  # list of str channel IDs
        "watched_channel_metadata": {},  # str(cid) -> {"name": str, "guild_name": str, "guild_id": str}
        "actions": {
            "delete_message": True,
            "kick_user": False,
            "ban_user": False,
            "ban_delete_days": 1,
            "timeout_user": False,
            "timeout_duration": 300  # seconds
        },
        "whitelist": {
            "users": [],  # list of str user IDs
            "roles": [],  # list of str role IDs
            "exempt_admin": True,
            "exempt_manage_guild": True,
            "exempt_manage_channels": True,
            "exempt_manage_messages": True,
            "exempt_kick_ban": True,
            "ignore_bots": False,
            "ignore_webhooks": False
        },
        "whitelist_metadata": {},  # "user:ID" or "role:ID" -> {"type": str, "name": str, ...}
        "stats": {
            "total_triggers": 0,
            "messages_deleted": 0,
            "users_kicked": 0,
            "users_banned": 0,
            "users_timed_out": 0,
            "whitelist_bypasses": 0,
            "last_trigger_time": "Never"
        },
        "incidents": []  # list of incident dicts (max 100)
    }

    def load_settings():
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        merged = DEFAULT_SETTINGS.copy()
                        # Deep merge actions
                        merged["actions"] = DEFAULT_SETTINGS["actions"].copy()
                        merged["actions"].update(data.get("actions", {}))
                        # Deep merge whitelist
                        merged["whitelist"] = DEFAULT_SETTINGS["whitelist"].copy()
                        merged["whitelist"].update(data.get("whitelist", {}))
                        # Deep merge stats
                        merged["stats"] = DEFAULT_SETTINGS["stats"].copy()
                        merged["stats"].update(data.get("stats", {}))
                        # Root keys
                        merged["enabled"] = data.get("enabled", True)
                        merged["target_guild_id"] = str(data.get("target_guild_id", ""))
                        merged["watched_channels"] = [str(c) for c in data.get("watched_channels", [])]
                        merged["watched_channel_metadata"] = data.get("watched_channel_metadata", {})
                        merged["whitelist_metadata"] = data.get("whitelist_metadata", {})
                        merged["incidents"] = data.get("incidents", [])
                        return merged
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error loading settings: {e}", type_="ERROR")
        return DEFAULT_SETTINGS.copy()

    def save_settings(data):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error saving settings: {e}", type_="ERROR")
            return False

    settings = load_settings()

    def persist():
        save_settings(settings)

    # UI References dictionary
    ui_refs = {}

    # ==================== CLIPBOARD HELPER ====================
    def copy_to_clipboard(text):
        try:
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
                root.destroy()
                return True
            except Exception:
                pass

            if sys.platform == 'win32':
                cmd = f"Set-Clipboard -Value '{text}'"
                subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=True, timeout=2)
                return True
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Clipboard copy failed: {e}", type_="WARN")
        return False

    # ==================== TELEMETRY & UI UPDATERS ====================
    def format_pool_management_display():
        users = settings["whitelist"].get("users", [])
        roles = settings["whitelist"].get("roles", [])
        channels = settings.get("watched_channels", [])
        wl_meta = settings.get("whitelist_metadata", {})
        ch_meta = settings.get("watched_channel_metadata", {})

        remove_items = [{"id": "none", "title": "Select an entry to remove..."}]
        lines = []

        # 1. Whitelist Section
        total_wl = len(users) + len(roles)
        lines.append(f"Active Whitelist ({total_wl}):")
        if not users and not roles:
            lines.append("• None configured.")
        else:
            if users:
                for uid in users[:8]:
                    info = wl_meta.get(f"user:{uid}", {})
                    u_name = info.get("name") or info.get("tag") or f"User-{uid}"
                    lines.append(f"• User: @{u_name} ({uid})")
                    remove_items.append({"id": f"user:{uid}", "title": f"User: @{u_name} ({uid})"})
                if len(users) > 8:
                    lines.append(f"• ... and {len(users) - 8} more user(s).")

            if roles:
                for rid in roles[:8]:
                    info = wl_meta.get(f"role:{rid}", {})
                    r_name = info.get("name", f"Role-{rid}")
                    g_name = info.get("guild_name", "")
                    g_str = f" [{g_name}]" if g_name else ""
                    lines.append(f"• Role: {r_name} ({rid}){g_str}")
                    remove_items.append({"id": f"role:{rid}", "title": f"Role: {r_name} ({rid}){g_str}"})
                if len(roles) > 8:
                    lines.append(f"• ... and {len(roles) - 8} more role(s).")

        lines.append("")
        # 2. Channel Pool Section
        lines.append(f"Active Watched Channels ({len(channels)}):")
        if not channels:
            lines.append("• None configured.")
        else:
            for cid in channels[:8]:
                info = ch_meta.get(cid, {})
                c_name = info.get("name", "channel")
                g_name = info.get("guild_name", "")
                g_str = f" [{g_name}]" if g_name else ""
                lines.append(f"• #{c_name} ({cid}){g_str}")
                remove_items.append({"id": f"channel:{cid}", "title": f"Channel: #{c_name} ({cid}){g_str}"})
            if len(channels) > 8:
                lines.append(f"• ... and {len(channels) - 8} more channel(s).")

        return "\n".join(lines), remove_items

    def update_pool_management_ui():
        try:
            items_str, remove_items = format_pool_management_display()
            if ui_refs.get('pool_mgmt_text'):
                ui_refs['pool_mgmt_text'].content = items_str
            if ui_refs.get('pool_remove_select'):
                ui_refs['pool_remove_select'].items = remove_items
                ui_refs['pool_remove_select'].selected_items = ["none"]
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error updating pool management UI: {e}", type_="ERROR")

    def update_telemetry_ui():
        try:
            watched_count = len(settings.get("watched_channels", []))
            is_enabled = bool(settings.get("enabled", True))

            if ui_refs.get('status_badge'):
                if not is_enabled:
                    ui_refs['status_badge'].content = "Status: Disabled"
                    ui_refs['status_badge'].color = "#ef4444"
                elif watched_count == 0:
                    ui_refs['status_badge'].content = "Status: Active (No Channels in Pool)"
                    ui_refs['status_badge'].color = "#eab308"
                else:
                    ui_refs['status_badge'].content = f"Status: Monitoring {watched_count} Channel(s)"
                    ui_refs['status_badge'].color = "#22c55e"

            stats = settings.get("stats", {})
            if ui_refs.get('stat_triggers'):
                ui_refs['stat_triggers'].content = f"Triggers: {stats.get('total_triggers', 0):,}"
            if ui_refs.get('stat_deleted'):
                ui_refs['stat_deleted'].content = f"Deleted: {stats.get('messages_deleted', 0):,}"
            if ui_refs.get('stat_kicked'):
                ui_refs['stat_kicked'].content = f"Kicked: {stats.get('users_kicked', 0):,}"
            if ui_refs.get('stat_banned'):
                ui_refs['stat_banned'].content = f"Banned: {stats.get('users_banned', 0):,}"
            if ui_refs.get('stat_timed_out'):
                ui_refs['stat_timed_out'].content = f"Timed Out: {stats.get('users_timed_out', 0):,}"
            if ui_refs.get('stat_bypasses'):
                ui_refs['stat_bypasses'].content = f"Bypasses: {stats.get('whitelist_bypasses', 0):,}"
            if ui_refs.get('stat_last_time'):
                ui_refs['stat_last_time'].content = f"Last: {stats.get('last_trigger_time', 'Never')}"
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error updating telemetry UI: {e}", type_="ERROR")

    def update_incidents_table():
        try:
            if not ui_refs.get('incidents_table'):
                return

            rows = []
            default_avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            incidents_list = settings.get("incidents", [])

            for inc in incidents_list:
                actions_str = inc.get("actions_taken", "Detected & Logged")
                tag_color = "gray"
                if "Banned" in actions_str:
                    tag_color = "red"
                elif "Kicked" in actions_str:
                    tag_color = "orange"
                elif "Timed Out" in actions_str:
                    tag_color = "yellow"
                elif "Deleted Msg" in actions_str:
                    tag_color = "green"

                raw_content = inc.get("message_content", "")
                preview = (raw_content[:45] + "...") if len(raw_content) > 45 else (raw_content or "[Empty]")

                rows.append({
                    "id": str(inc.get("id", "")),
                    "cells": [
                        {
                            "text": inc.get("user_name", "Unknown User"),
                            "subtext": inc.get("user_tag", ""),
                            "imageUrl": inc.get("avatar_url") or default_avatar
                        },
                        {"text": str(inc.get("user_id", "-"))},
                        {"text": f"#{inc.get('channel_name', 'channel')} ({inc.get('guild_name', 'Server')})"},
                        {"text": preview},
                        {"text": actions_str, "color": tag_color},
                        {"text": str(inc.get("timestamp", "-"))},
                        {}  # Actions column (Inspect / Copy ID)
                    ]
                })

            if not rows:
                rows = [{
                    "id": "none",
                    "cells": [
                        {"text": "No honeypot triggers recorded yet", "imageUrl": default_avatar},
                        {"text": "-"},
                        {"text": "-"},
                        {"text": "-"},
                        {"text": "None", "color": "gray"},
                        {"text": "-"},
                        {}
                    ]
                }]

            ui_refs['incidents_table'].rows = rows
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error updating incidents table: {e}", type_="ERROR")

    def display_incident_inspector(inc_data):
        try:
            if not inc_data or inc_data.get("id") == "none":
                if ui_refs.get('detail_name'):
                    ui_refs['detail_name'].content = "Select an incident from the table above to view details."
                if ui_refs.get('detail_user_id'):
                    ui_refs['detail_user_id'].content = "User ID: -"
                if ui_refs.get('detail_server_channel'):
                    ui_refs['detail_server_channel'].content = "Location: - | Channel: -"
                if ui_refs.get('detail_timestamp'):
                    ui_refs['detail_timestamp'].content = "Timestamp: -"
                if ui_refs.get('detail_actions'):
                    ui_refs['detail_actions'].content = "Actions Executed: None"
                if ui_refs.get('detail_content'):
                    ui_refs['detail_content'].content = "Message Content:\nNone"
                return

            if ui_refs.get('detail_name'):
                ui_refs['detail_name'].content = f"Offender: {inc_data.get('user_name')} ({inc_data.get('user_tag', '')})"
            if ui_refs.get('detail_user_id'):
                ui_refs['detail_user_id'].content = f"User ID: {inc_data.get('user_id', '-')}"
            if ui_refs.get('detail_server_channel'):
                ui_refs['detail_server_channel'].content = f"Server: {inc_data.get('guild_name', '-')} | Channel: #{inc_data.get('channel_name', '-')}"
            if ui_refs.get('detail_timestamp'):
                ui_refs['detail_timestamp'].content = f"Timestamp: {inc_data.get('timestamp', '-')}"
            if ui_refs.get('detail_actions'):
                ui_refs['detail_actions'].content = f"Actions Executed: {inc_data.get('actions_taken', 'None')}"
            if ui_refs.get('detail_content'):
                ui_refs['detail_content'].content = f"Message Content:\n{inc_data.get('message_content', '[Empty]')}"
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error displaying incident inspector: {e}", type_="ERROR")

    # ==================== DISCORD MESSAGE LISTENER ====================
    @bot.listen("on_message")
    async def honeypot_message_listener(message):
        try:
            if not settings.get("enabled", True):
                return

            channel_id_str = str(message.channel.id)
            watched = settings.get("watched_channels", [])
            if channel_id_str not in watched:
                return

            # Selfbot account is permanently immune
            if message.author.id == bot.user.id:
                return

            # Webhook exemption check
            if getattr(message, "webhook_id", None) and settings["whitelist"].get("ignore_webhooks", False):
                return

            # Bot exemption check
            if getattr(message.author, "bot", False) and settings["whitelist"].get("ignore_bots", False):
                return

            # User ID whitelist check
            author_id_str = str(message.author.id)
            if author_id_str in settings["whitelist"].get("users", []):
                settings["stats"]["whitelist_bypasses"] = settings["stats"].get("whitelist_bypasses", 0) + 1
                persist()
                update_telemetry_ui()
                return

            guild = message.guild
            member = message.author if (guild and isinstance(message.author, discord.Member)) else (guild.get_member(message.author.id) if guild else None)

            # Role ID whitelist check
            if member and hasattr(member, 'roles'):
                member_role_ids = [str(r.id) for r in member.roles]
                whitelisted_roles = settings["whitelist"].get("roles", [])
                if any(r_id in whitelisted_roles for r_id in member_role_ids):
                    settings["stats"]["whitelist_bypasses"] = settings["stats"].get("whitelist_bypasses", 0) + 1
                    persist()
                    update_telemetry_ui()
                    return

            # Permission-based exemptions
            if member and hasattr(member, 'guild_permissions'):
                perms = member.guild_permissions
                wl = settings.get("whitelist", {})
                if wl.get("exempt_admin", True) and getattr(perms, 'administrator', False):
                    settings["stats"]["whitelist_bypasses"] = settings["stats"].get("whitelist_bypasses", 0) + 1
                    persist()
                    update_telemetry_ui()
                    return
                if wl.get("exempt_manage_guild", True) and getattr(perms, 'manage_guild', False):
                    settings["stats"]["whitelist_bypasses"] = settings["stats"].get("whitelist_bypasses", 0) + 1
                    persist()
                    update_telemetry_ui()
                    return
                if wl.get("exempt_manage_channels", True) and getattr(perms, 'manage_channels', False):
                    settings["stats"]["whitelist_bypasses"] = settings["stats"].get("whitelist_bypasses", 0) + 1
                    persist()
                    update_telemetry_ui()
                    return
                if wl.get("exempt_manage_messages", True) and getattr(perms, 'manage_messages', False):
                    settings["stats"]["whitelist_bypasses"] = settings["stats"].get("whitelist_bypasses", 0) + 1
                    persist()
                    update_telemetry_ui()
                    return
                if wl.get("exempt_kick_ban", True) and (getattr(perms, 'kick_members', False) or getattr(perms, 'ban_members', False)):
                    settings["stats"]["whitelist_bypasses"] = settings["stats"].get("whitelist_bypasses", 0) + 1
                    persist()
                    update_telemetry_ui()
                    return

            # ════════════════════════════════════════════════════════════════
            # HONEYPOT TRIGGERED! EXECUTE ACTIONS
            # ════════════════════════════════════════════════════════════════
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            settings["stats"]["total_triggers"] = settings["stats"].get("total_triggers", 0) + 1
            settings["stats"]["last_trigger_time"] = now_str

            actions_taken = []
            cfg_actions = settings.get("actions", {})
            guild_name = guild.name if guild else "Unknown Server"
            channel_name = getattr(message.channel, "name", channel_id_str)
            user_name = getattr(message.author, "display_name", None) or getattr(message.author, "name", f"User-{author_id_str}")
            user_tag = f"@{getattr(message.author, 'name', user_name)}"

            # 1. Delete Offending Message
            if cfg_actions.get("delete_message", True):
                try:
                    await message.delete()
                    actions_taken.append("Deleted Msg")
                    settings["stats"]["messages_deleted"] = settings["stats"].get("messages_deleted", 0) + 1
                except Exception:
                    actions_taken.append("Delete Failed")

            # Hierarchy check
            me = guild.me if (guild and hasattr(guild, 'me')) else (guild.get_member(bot.user.id) if guild else None)
            me_perms = getattr(me, 'guild_permissions', None) if me else None
            is_hierarchy_safe = False
            if member and me and hasattr(member, 'top_role') and hasattr(me, 'top_role'):
                is_hierarchy_safe = (member.top_role < me.top_role) and (member.id != guild.owner_id)

            # 2. Timeout User
            if cfg_actions.get("timeout_user", False) and member:
                has_mod_perms = bool(getattr(me_perms, 'moderate_members', False) or getattr(me_perms, 'administrator', False))
                if has_mod_perms and is_hierarchy_safe:
                    try:
                        dur_seconds = int(cfg_actions.get("timeout_duration", 300))
                        until = datetime.now(timezone.utc) + timedelta(seconds=dur_seconds)
                        if hasattr(member, 'timeout'):
                            await member.timeout(until, reason="Honeypot Trigger")
                            actions_taken.append(f"Timed Out ({dur_seconds}s)")
                            settings["stats"]["users_timed_out"] = settings["stats"].get("users_timed_out", 0) + 1
                    except Exception:
                        actions_taken.append("Timeout Failed")
                else:
                    actions_taken.append("Timeout Skipped (Hierarchy/Perms)")

            # 3. Kick User
            if cfg_actions.get("kick_user", False) and member:
                has_kick_perms = bool(getattr(me_perms, 'kick_members', False) or getattr(me_perms, 'administrator', False))
                if has_kick_perms and is_hierarchy_safe:
                    try:
                        await member.kick(reason="Honeypot Trigger")
                        actions_taken.append("Kicked")
                        settings["stats"]["users_kicked"] = settings["stats"].get("users_kicked", 0) + 1
                    except Exception:
                        actions_taken.append("Kick Failed")
                else:
                    actions_taken.append("Kick Skipped (Hierarchy/Perms)")

            # 4. Ban User
            if cfg_actions.get("ban_user", False) and guild:
                has_ban_perms = bool(getattr(me_perms, 'ban_members', False) or getattr(me_perms, 'administrator', False))
                if has_ban_perms and is_hierarchy_safe:
                    try:
                        delete_days = int(cfg_actions.get("ban_delete_days", 1))
                        await guild.ban(message.author, reason="Honeypot Trigger", delete_message_days=delete_days)
                        actions_taken.append("Banned")
                        settings["stats"]["users_banned"] = settings["stats"].get("users_banned", 0) + 1
                    except Exception:
                        actions_taken.append("Ban Failed")
                else:
                    actions_taken.append("Ban Skipped (Hierarchy/Perms)")

            if not actions_taken:
                actions_taken.append("Detected & Logged")

            actions_str = ", ".join(actions_taken)

            avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"
            if hasattr(message.author, 'avatar') and message.author.avatar:
                avatar_url = str(getattr(message.author.avatar, 'url', message.author.avatar))
            elif hasattr(message.author, 'display_avatar') and message.author.display_avatar:
                avatar_url = str(message.author.display_avatar.url)

            raw_msg_content = message.content or ""
            if message.attachments:
                att_names = [a.filename for a in message.attachments if hasattr(a, 'filename')]
                att_str = f" [Attachments: {', '.join(att_names)}]"
                raw_msg_content = (raw_msg_content + att_str).strip()

            incident_entry = {
                "id": f"hp_{int(now.timestamp())}_{author_id_str}",
                "user_id": author_id_str,
                "user_name": user_name,
                "user_tag": user_tag,
                "avatar_url": avatar_url,
                "guild_id": str(guild.id) if guild else "Unknown",
                "guild_name": guild_name,
                "channel_id": channel_id_str,
                "channel_name": channel_name,
                "message_content": raw_msg_content,
                "actions_taken": actions_str,
                "timestamp": now_str
            }

            settings["incidents"] = [incident_entry] + settings.get("incidents", [])[:99]
            persist()

            update_telemetry_ui()
            update_incidents_table()
            display_incident_inspector(incident_entry)

            print(f"[{SCRIPT_NAME}] Honeypot Triggered by {user_name} ({author_id_str}) in #{channel_name} ({guild_name}) -> {actions_str}", type_="WARN")

        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error in message listener: {e}\n{traceback.format_exc()}", type_="ERROR")

    # ==================== CHAT COMMANDS ====================
    @bot.command(
        name="honeypot",
        aliases=["hp", "bait"],
        usage="status | on | off | add <channel_id> | remove <channel_id> | clear",
        description="Honeypot defense controls and statistics"
    )
    async def honeypot_cmd(ctx, *, args: str = ""):
        await ctx.message.delete()
        parts = args.strip().split()
        sub = parts[0].lower() if parts else "help"

        if sub in ("help", ""):
            await ctx.send(
                "**Honeypot Controls**\n"
                "`<p>honeypot status` — View active monitoring state\n"
                "`<p>honeypot on` / `off` — Toggle monitoring\n"
                "`<p>honeypot add <channel_id>` — Add a channel to the pool\n"
                "`<p>honeypot remove <channel_id>` — Remove a channel from the pool\n"
                "`<p>honeypot clear` — Clear all watched channels\n"
                "Configure actions, whitelists, and logs in the **Honeypot** UI tab."
            )
            return

        if sub == "status":
            pool_count = len(settings.get("watched_channels", []))
            stats = settings.get("stats", {})
            state = "Enabled" if settings.get("enabled", True) else "Disabled"
            await ctx.send(
                f"**Honeypot Status: `{state}`**\n"
                f"• Monitored Channels: `{pool_count}`\n"
                f"• Total Triggers: `{stats.get('total_triggers', 0):,}`\n"
                f"• Messages Deleted: `{stats.get('messages_deleted', 0):,}`\n"
                f"• Users Kicked: `{stats.get('users_kicked', 0):,}` | Banned: `{stats.get('users_banned', 0):,}`\n"
                f"• Whitelist Bypasses: `{stats.get('whitelist_bypasses', 0):,}`\n"
                f"• Last Trigger: `{stats.get('last_trigger_time', 'Never')}`"
            )
            return

        if sub == "on":
            settings["enabled"] = True
            persist()
            update_telemetry_ui()
            await ctx.send("> **[Honeypot]** Monitoring **ENABLED**.")
            return

        if sub == "off":
            settings["enabled"] = False
            persist()
            update_telemetry_ui()
            await ctx.send("> **[Honeypot]** Monitoring **DISABLED**.")
            return

        if sub == "add":
            if len(parts) < 2 or not parts[1].isdigit():
                await ctx.send("> [!] Usage: `<p>honeypot add <channel_id>`")
                return
            cid = parts[1]
            if cid not in settings["watched_channels"]:
                ch_obj = bot.get_channel(int(cid))
                c_name = ch_obj.name if ch_obj else "custom-channel"
                g_name = ch_obj.guild.name if (ch_obj and ch_obj.guild) else "Unknown Server"
                settings["watched_channels"].append(cid)
                settings["watched_channel_metadata"][cid] = {
                    "name": c_name,
                    "guild_name": g_name,
                    "guild_id": str(ch_obj.guild.id) if (ch_obj and ch_obj.guild) else ""
                }
                persist()
                update_telemetry_ui()
                update_pool_management_ui()
                await ctx.send(f"> **[Honeypot]** Added channel `#{c_name}` (`{cid}`) to pool.")
            else:
                await ctx.send(f"> **[Honeypot]** Channel `{cid}` is already in the pool.")
            return

        if sub == "remove":
            if len(parts) < 2 or not parts[1].isdigit():
                await ctx.send("> [!] Usage: `<p>honeypot remove <channel_id>`")
                return
            cid = parts[1]
            if cid in settings["watched_channels"]:
                settings["watched_channels"].remove(cid)
                settings["watched_channel_metadata"].pop(cid, None)
                persist()
                update_telemetry_ui()
                update_pool_management_ui()
                await ctx.send(f"> **[Honeypot]** Removed channel `{cid}` from pool.")
            else:
                await ctx.send(f"> **[Honeypot]** Channel `{cid}` was not found in the pool.")
            return

        if sub == "clear":
            settings["watched_channels"] = []
            settings["watched_channel_metadata"] = {}
            persist()
            update_telemetry_ui()
            update_pool_management_ui()
            await ctx.send("> **[Honeypot]** Cleared all channels from pool.")
            return

        await ctx.send("> Unknown honeypot command. Use `<p>honeypot help`.")

    # ==================== UI CONSTRUCTION ====================
    tab = Tab(name="Honeypot", icon="lock", title="Honeypot", gap=4)
    main_container = tab.create_container(type="rows", gap=4, width="full")

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 1: TOP ROW (Full Width Card) - Telemetry & Status (Thin & Compact)
    # ════════════════════════════════════════════════════════════════════════════
    telemetry_card = main_container.create_card(type="rows", gap=2, width="full", height="auto", disallow_shrink=True)

    # Line 1: Header + Master Toggle + Status Badge + Action Buttons
    top_stat_header = telemetry_card.create_group(type="columns", gap=3, vertical_align="center")
    top_stat_header.create_ui_element(UI.Text, content="Telemetry & Status", size="base", weight="bold")

    master_toggle = top_stat_header.create_ui_element(
        UI.Toggle, label="Enabled", checked=bool(settings.get("enabled", True))
    )
    ui_refs['master_toggle'] = master_toggle

    status_badge = top_stat_header.create_ui_element(
        UI.Text,
        content="Status: Initializing...",
        size="sm",
        weight="bold",
        color="#22c55e"
    )
    ui_refs['status_badge'] = status_badge

    reset_stats_btn = top_stat_header.create_ui_element(UI.Button, label="Reset Statistics", variant="ghost", color="danger")

    # Line 2: 7 Stat Metrics in a single sleek horizontal row
    stats_row = telemetry_card.create_group(type="columns", gap=4, vertical_align="center")
    stat_triggers = stats_row.create_ui_element(UI.Text, content="Triggers: 0", size="sm", color="#d4d4d8")
    stat_deleted = stats_row.create_ui_element(UI.Text, content="Deleted: 0", size="sm", color="#a1a1aa")
    stat_kicked = stats_row.create_ui_element(UI.Text, content="Kicked: 0", size="sm", color="#a1a1aa")
    stat_banned = stats_row.create_ui_element(UI.Text, content="Banned: 0", size="sm", color="#a1a1aa")
    stat_timed_out = stats_row.create_ui_element(UI.Text, content="Timed Out: 0", size="sm", color="#a1a1aa")
    stat_bypasses = stats_row.create_ui_element(UI.Text, content="Bypasses: 0", size="sm", color="#a1a1aa")
    stat_last_time = stats_row.create_ui_element(UI.Text, content="Last: Never", size="sm", color="#71717a")

    ui_refs['stat_triggers'] = stat_triggers
    ui_refs['stat_deleted'] = stat_deleted
    ui_refs['stat_kicked'] = stat_kicked
    ui_refs['stat_banned'] = stat_banned
    ui_refs['stat_timed_out'] = stat_timed_out
    ui_refs['stat_bypasses'] = stat_bypasses
    ui_refs['stat_last_time'] = stat_last_time

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 2: MIDDLE ROW (2 Half-Width Cards 50% / 50%)
    # Channel Pool (Left) & Actions (Right)
    # ════════════════════════════════════════════════════════════════════════════
    mid_cols = main_container.create_container(type="columns", gap=4, width="full")

    # ── Card 2 (50% Width Left): Channel Pool ──
    pool_card = mid_cols.create_card(type="rows", gap=3)
    pool_card.create_ui_element(UI.Text, content="Channel Pool", size="lg", weight="bold")
    pool_card.create_ui_element(
        UI.Text,
        content="Select a server and manage channels in your honeypot pool.",
        size="sm",
        color="#888888"
    )

    server_select = pool_card.create_ui_element(
        UI.Select,
        label="Target Server",
        items=[{"id": "none", "title": "Select a server..."}],
        mode="single",
        full_width=True
    )
    ui_refs['server_select'] = server_select

    channel_select = pool_card.create_ui_element(
        UI.Select,
        label="Server Channel Picker",
        items=[{"id": "none", "title": "Select a server first..."}],
        mode="single",
        full_width=True
    )
    ui_refs['channel_select'] = channel_select

    channel_id_input = pool_card.create_ui_element(
        UI.Input,
        label="Manual Channel ID",
        placeholder="Enter or paste channel ID...",
        description="Add by dropdown above or direct Channel ID here.",
        full_width=True
    )
    ui_refs['channel_id_input'] = channel_id_input

    btn_row = pool_card.create_group(type="columns", gap=2)
    add_channel_btn = btn_row.create_ui_element(UI.Button, label="Add Channel", variant="solid", color="primary")
    remove_channel_btn = btn_row.create_ui_element(UI.Button, label="Remove", variant="bordered", color="default")
    clear_pool_btn = btn_row.create_ui_element(UI.Button, label="Clear Pool", variant="ghost", color="danger")

    # ── Card 3 (50% Width Right): Actions ──
    act_card = mid_cols.create_card(type="rows", gap=3)
    act_card.create_ui_element(UI.Text, content="Actions", size="lg", weight="bold")
    act_card.create_ui_element(
        UI.Text,
        content="Configure automated actions when a message is caught.",
        size="sm",
        color="#888888"
    )

    act_toggles_grid = act_card.create_group(type="columns", gap=4)
    act_col_1 = act_toggles_grid.create_group(type="rows", gap=2)
    act_del_tog = act_col_1.create_ui_element(
        UI.Toggle, label="Delete Offending Message", checked=bool(settings["actions"].get("delete_message", True))
    )
    act_kick_tog = act_col_1.create_ui_element(
        UI.Toggle, label="Kick Offender", checked=bool(settings["actions"].get("kick_user", False))
    )

    act_col_2 = act_toggles_grid.create_group(type="rows", gap=2)
    act_ban_tog = act_col_2.create_ui_element(
        UI.Toggle, label="Ban Offender", checked=bool(settings["actions"].get("ban_user", False))
    )
    act_timeout_tog = act_col_2.create_ui_element(
        UI.Toggle, label="Timeout Offender", checked=bool(settings["actions"].get("timeout_user", False))
    )

    ui_refs['act_del_tog'] = act_del_tog
    ui_refs['act_kick_tog'] = act_kick_tog
    ui_refs['act_ban_tog'] = act_ban_tog
    ui_refs['act_timeout_tog'] = act_timeout_tog

    timeout_duration_select = act_card.create_ui_element(
        UI.Select,
        label="Timeout Duration",
        items=[
            {"id": "60", "title": "60 Seconds"},
            {"id": "300", "title": "5 Minutes (Default)"},
            {"id": "600", "title": "10 Minutes"},
            {"id": "3600", "title": "1 Hour"},
            {"id": "86400", "title": "1 Day"},
            {"id": "604800", "title": "1 Week"}
        ],
        selected_items=[str(settings["actions"].get("timeout_duration", 300))],
        mode="single",
        full_width=True
    )
    ui_refs['timeout_duration_select'] = timeout_duration_select

    ban_days_select = act_card.create_ui_element(
        UI.Select,
        label="Delete Message History",
        items=[
            {"id": "0", "title": "Do not delete message history"},
            {"id": "1", "title": "Previous 24 Hours (1 Day - Default)"},
            {"id": "7", "title": "Previous 7 Days"}
        ],
        selected_items=[str(settings["actions"].get("ban_delete_days", 1))],
        mode="single",
        full_width=True
    )
    ui_refs['ban_days_select'] = ban_days_select

    save_actions_btn = act_card.create_ui_element(
        UI.Button, label="Save Actions", variant="cta", color="primary", full_width=True
    )

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 3: THIRD ROW (2 Half-Width Cards 50% / 50%)
    # Permissions & Whitelist Picker (Left) & Active Pools & Whitelists (Right)
    # ════════════════════════════════════════════════════════════════════════════
    bot_cols = main_container.create_container(type="columns", gap=4, width="full")

    # ── Card 4 (50% Width Left): Permissions & Whitelist ──
    wl_card = bot_cols.create_card(type="rows", gap=3)
    wl_card.create_ui_element(UI.Text, content="Permissions & Whitelist", size="lg", weight="bold")
    wl_card.create_ui_element(
        UI.Text,
        content="Ignore trusted server permissions or add users & roles to whitelist.",
        size="sm",
        color="#888888"
    )

    wl_perms_grid = wl_card.create_group(type="columns", gap=4)
    wl_col_1 = wl_perms_grid.create_group(type="rows", gap=2)
    imm_admin_tog = wl_col_1.create_ui_element(
        UI.Toggle, label="Ignore Administrator", checked=bool(settings["whitelist"].get("exempt_admin", True))
    )
    imm_manage_guild_tog = wl_col_1.create_ui_element(
        UI.Toggle, label="Ignore Manage Server", checked=bool(settings["whitelist"].get("exempt_manage_guild", True))
    )
    imm_manage_ch_tog = wl_col_1.create_ui_element(
        UI.Toggle, label="Ignore Manage Channels", checked=bool(settings["whitelist"].get("exempt_manage_channels", True))
    )

    wl_col_2 = wl_perms_grid.create_group(type="rows", gap=2)
    imm_manage_msg_tog = wl_col_2.create_ui_element(
        UI.Toggle, label="Ignore Manage Messages", checked=bool(settings["whitelist"].get("exempt_manage_messages", True))
    )
    imm_kick_ban_tog = wl_col_2.create_ui_element(
        UI.Toggle, label="Ignore Kick / Ban Perms", checked=bool(settings["whitelist"].get("exempt_kick_ban", True))
    )
    imm_bots_tog = wl_col_2.create_ui_element(
        UI.Toggle, label="Ignore Bots", checked=bool(settings["whitelist"].get("ignore_bots", False))
    )

    ui_refs['imm_admin_tog'] = imm_admin_tog
    ui_refs['imm_manage_guild_tog'] = imm_manage_guild_tog
    ui_refs['imm_manage_ch_tog'] = imm_manage_ch_tog
    ui_refs['imm_manage_msg_tog'] = imm_manage_msg_tog
    ui_refs['imm_kick_ban_tog'] = imm_kick_ban_tog
    ui_refs['imm_bots_tog'] = imm_bots_tog

    add_user_input = wl_card.create_ui_element(
        UI.Input,
        label="Add User ID",
        placeholder="Enter user ID (e.g. 123456789012345678)...",
        full_width=True
    )
    ui_refs['add_user_input'] = add_user_input

    add_role_input = wl_card.create_ui_element(
        UI.Input,
        label="Add Role ID",
        placeholder="Enter role ID (e.g. 987654321098765432)...",
        full_width=True
    )
    ui_refs['add_role_input'] = add_role_input

    wl_action_btn_row = wl_card.create_group(type="columns", gap=2)
    add_user_btn = wl_action_btn_row.create_ui_element(UI.Button, label="Add User", variant="solid", color="primary")
    add_role_btn = wl_action_btn_row.create_ui_element(UI.Button, label="Add Role", variant="bordered", color="default")
    save_perms_btn = wl_action_btn_row.create_ui_element(UI.Button, label="Save Permissions", variant="cta", color="primary")

    # ── Card 5 (50% Width Right): Active Pools & Whitelists ──
    pool_mgmt_card = bot_cols.create_card(type="rows", gap=3)
    pool_mgmt_card.create_ui_element(UI.Text, content="Active Pools & Whitelists", size="lg", weight="bold")
    pool_mgmt_card.create_ui_element(
        UI.Text,
        content="Active watched channels and whitelisted users & roles.",
        size="sm",
        color="#888888"
    )

    pool_mgmt_text = pool_mgmt_card.create_ui_element(
        UI.Text,
        content="Loading active entries...",
        size="sm",
        color="#d4d4d8"
    )
    ui_refs['pool_mgmt_text'] = pool_mgmt_text

    pool_remove_select = pool_mgmt_card.create_ui_element(
        UI.Select,
        label="Remove Entry",
        items=[{"id": "none", "title": "Select an entry to remove..."}],
        mode="single",
        full_width=True
    )
    ui_refs['pool_remove_select'] = pool_remove_select

    pool_mgmt_btn_row = pool_mgmt_card.create_group(type="columns", gap=2)
    pool_remove_btn = pool_mgmt_btn_row.create_ui_element(UI.Button, label="Remove", variant="solid", color="danger")
    clear_all_wl_btn = pool_mgmt_btn_row.create_ui_element(UI.Button, label="Clear Whitelist", variant="ghost", color="danger")
    clear_all_ch_btn = pool_mgmt_btn_row.create_ui_element(UI.Button, label="Clear Channels", variant="ghost", color="danger")

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 4: INCIDENT LOGS TABLE (Full Width)
    # ════════════════════════════════════════════════════════════════════════════
    table_card = main_container.create_card(type="rows", gap=3, width="full", height="auto", disallow_shrink=True)

    table_header = table_card.create_group(type="columns", gap=4, vertical_align="center")
    table_header.create_ui_element(UI.Text, content="Incident Logs", size="lg", weight="bold")
    clear_logs_btn = table_header.create_ui_element(UI.Button, label="Clear Logs", variant="ghost", color="danger")

    def handle_copy_user_id(row_id):
        if not row_id or row_id == "none":
            return
        inc = next((i for i in settings.get("incidents", []) if str(i.get("id")) == str(row_id)), None)
        uid = inc.get("user_id") if inc else str(row_id)
        if copy_to_clipboard(str(uid)):
            tab.toast(type="SUCCESS", title="Copied", description=f"User ID {uid} copied to clipboard.")
        else:
            tab.toast(type="INFO", title="User ID", description=f"User ID: {uid}")

    def handle_inspect_incident(row_id):
        if not row_id or row_id == "none":
            return
        inc = next((i for i in settings.get("incidents", []) if str(i.get("id")) == str(row_id)), None)
        if inc:
            display_incident_inspector(inc)
            tab.toast(type="INFO", title="Incident Selected", description=f"Inspecting {inc.get('user_name')} event.")
        else:
            tab.toast(type="ERROR", title="Not Found", description="Incident data not found.")

    incidents_table = table_card.create_ui_element(
        UI.Table,
        search=True,
        items_per_page=10,
        selectable=False,
        columns=[
            {"type": "text", "label": "Offender"},
            {"type": "text", "label": "User ID"},
            {"type": "text", "label": "Location"},
            {"type": "text", "label": "Message Content"},
            {"type": "tag",  "label": "Actions Taken"},
            {"type": "text", "label": "Timestamp"},
            {
                "type": "button",
                "label": "Actions",
                "buttons": [
                    {"label": "Inspect", "color": "default", "onClick": handle_inspect_incident},
                    {"label": "Copy ID", "color": "default", "onClick": handle_copy_user_id}
                ]
            }
        ],
        rows=[]
    )
    ui_refs['incidents_table'] = incidents_table

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 5: INCIDENT DETAILS (Full Width, Compact & Slim)
    # ════════════════════════════════════════════════════════════════════════════
    inspector_card = main_container.create_card(type="rows", gap=2, width="full", height="auto", disallow_shrink=True)
    inspector_card.create_ui_element(UI.Text, content="Incident Details", size="lg", weight="bold")

    detail_name = inspector_card.create_ui_element(
        UI.Text, content="Select an incident from the table above to view details.", size="base", weight="medium", color="#ffffff"
    )
    ui_refs['detail_name'] = detail_name

    detail_deck = inspector_card.create_group(type="columns", gap=4)
    deck_left = detail_deck.create_group(type="rows", gap=2)
    detail_user_id = deck_left.create_ui_element(UI.Text, content="User ID: -", size="sm", color="#d4d4d8")
    detail_server_channel = deck_left.create_ui_element(UI.Text, content="Location: - | Channel: -", size="sm", color="#d4d4d8")
    ui_refs['detail_user_id'] = detail_user_id
    ui_refs['detail_server_channel'] = detail_server_channel

    deck_right = detail_deck.create_group(type="rows", gap=2)
    detail_timestamp = deck_right.create_ui_element(UI.Text, content="Timestamp: -", size="sm", color="#d4d4d8")
    detail_actions = deck_right.create_ui_element(UI.Text, content="Actions Executed: None", size="sm", color="#22c55e")
    ui_refs['detail_timestamp'] = detail_timestamp
    ui_refs['detail_actions'] = detail_actions

    detail_content = inspector_card.create_ui_element(
        UI.Text, content="Message Content:\nNone", size="sm", color="#aaaaaa"
    )
    ui_refs['detail_content'] = detail_content

    # ==================== UI EVENT CALLBACKS ====================
    def on_server_select(selected_items):
        try:
            if not selected_items or selected_items[0] in ("loading", "none"):
                channel_select.items = [{"id": "none", "title": "Select a server first..."}]
                channel_select.selected_items = ["none"]
                channel_id_input.value = ""
                return

            guild_id = int(selected_items[0])
            guild = bot.get_guild(guild_id)
            if not guild:
                channel_select.items = [{"id": "none", "title": "Server not available"}]
                channel_select.selected_items = ["none"]
                channel_id_input.value = ""
                return

            settings["target_guild_id"] = str(guild_id)

            ch_items = [{"id": "none", "title": "Select a channel..."}]
            text_channels = list(getattr(guild, "text_channels", []))
            for ch in text_channels:
                ch_items.append({
                    "id": str(ch.id),
                    "title": f"#{ch.name}"
                })

            if len(ch_items) > 1:
                channel_select.items = ch_items
                channel_select.selected_items = ["none"]
                channel_id_input.value = ""
            else:
                channel_select.items = [{"id": "none", "title": "No text channels found"}]
                channel_select.selected_items = ["none"]
                channel_id_input.value = ""
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error handling server selection: {e}", type_="ERROR")

    server_select.onChange = on_server_select

    def on_channel_select(selected_items):
        try:
            if selected_items and selected_items[0] not in ("none", "loading"):
                channel_id_input.value = str(selected_items[0])
            else:
                channel_id_input.value = ""
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error on channel select: {e}", type_="ERROR")

    channel_select.onChange = on_channel_select

    def on_master_toggle(checked):
        settings["enabled"] = bool(checked)
        persist()
        update_telemetry_ui()
        tab.toast(title="Honeypot", description=f"Monitoring {'Enabled' if checked else 'Disabled'}.", type="INFO")

    master_toggle.onChange = on_master_toggle

    async def on_add_channel():
        raw = (channel_id_input.value or "").strip()
        if not raw or not raw.isdigit() or raw == "none":
            tab.toast(title="Invalid Channel ID", description="Please select a channel or enter a numeric channel ID.", type="ERROR")
            return

        if raw in settings["watched_channels"]:
            tab.toast(title="Already Monitored", description="Channel is already in the honeypot pool.", type="INFO")
            return

        ch_obj = bot.get_channel(int(raw))
        c_name = ch_obj.name if ch_obj else "custom-channel"
        g_name = ch_obj.guild.name if (ch_obj and ch_obj.guild) else "Unknown Server"
        g_id = str(ch_obj.guild.id) if (ch_obj and ch_obj.guild) else ""

        settings["watched_channels"].append(raw)
        settings["watched_channel_metadata"][raw] = {
            "name": c_name,
            "guild_name": g_name,
            "guild_id": g_id
        }
        persist()
        update_telemetry_ui()
        update_pool_management_ui()
        channel_id_input.value = ""
        channel_select.selected_items = ["none"]
        tab.toast(title="Channel Added", description=f"Added #{c_name} ({raw}) to pool.", type="SUCCESS")

    async def on_remove_channel():
        raw = (channel_id_input.value or "").strip()
        if raw in settings["watched_channels"]:
            settings["watched_channels"].remove(raw)
            settings["watched_channel_metadata"].pop(raw, None)
            persist()
            update_telemetry_ui()
            update_pool_management_ui()
            channel_id_input.value = ""
            channel_select.selected_items = ["none"]
            tab.toast(title="Channel Removed", description=f"Removed channel {raw} from pool.", type="SUCCESS")
        else:
            tab.toast(title="Not Found", description="Channel ID is not currently in the pool.", type="ERROR")

    async def on_clear_pool():
        settings["watched_channels"] = []
        settings["watched_channel_metadata"] = {}
        persist()
        update_telemetry_ui()
        update_pool_management_ui()
        tab.toast(title="Pool Cleared", description="All watched honeypot channels have been removed.", type="SUCCESS")

    add_channel_btn.onClick = on_add_channel
    remove_channel_btn.onClick = on_remove_channel
    clear_pool_btn.onClick = on_clear_pool

    async def on_save_actions():
        settings["actions"]["delete_message"] = bool(act_del_tog.checked)
        settings["actions"]["kick_user"] = bool(act_kick_tog.checked)
        settings["actions"]["ban_user"] = bool(act_ban_tog.checked)
        settings["actions"]["timeout_user"] = bool(act_timeout_tog.checked)

        if timeout_duration_select.selected_items:
            try:
                settings["actions"]["timeout_duration"] = int(timeout_duration_select.selected_items[0])
            except ValueError:
                pass

        if ban_days_select.selected_items:
            try:
                settings["actions"]["ban_delete_days"] = int(ban_days_select.selected_items[0])
            except ValueError:
                pass

        persist()
        tab.toast(title="Actions Saved", description="Enforcement actions updated.", type="SUCCESS")

    save_actions_btn.onClick = on_save_actions

    async def on_save_permissions():
        settings["whitelist"]["exempt_admin"] = bool(imm_admin_tog.checked)
        settings["whitelist"]["exempt_manage_guild"] = bool(imm_manage_guild_tog.checked)
        settings["whitelist"]["exempt_manage_channels"] = bool(imm_manage_ch_tog.checked)
        settings["whitelist"]["exempt_manage_messages"] = bool(imm_manage_msg_tog.checked)
        settings["whitelist"]["exempt_kick_ban"] = bool(imm_kick_ban_tog.checked)
        settings["whitelist"]["ignore_bots"] = bool(imm_bots_tog.checked)

        persist()
        tab.toast(title="Permissions Saved", description="Permission immunity settings updated.", type="SUCCESS")

    save_perms_btn.onClick = on_save_permissions

    async def on_add_user():
        raw = (add_user_input.value or "").strip()
        parts = [u.strip() for u in raw.split(",") if u.strip().isdigit()]
        if not parts:
            tab.toast(title="Invalid User ID", description="Please enter a valid numeric User ID.", type="ERROR")
            return

        added = 0
        if "whitelist_metadata" not in settings:
            settings["whitelist_metadata"] = {}

        for uid in parts:
            if uid not in settings["whitelist"]["users"]:
                settings["whitelist"]["users"].append(uid)
                u_obj = bot.get_user(int(uid))
                u_name = getattr(u_obj, "display_name", None) or getattr(u_obj, "name", f"User-{uid}") if u_obj else f"User-{uid}"
                settings["whitelist_metadata"][f"user:{uid}"] = {
                    "type": "user",
                    "name": u_name,
                    "tag": str(u_obj) if u_obj else uid
                }
                added += 1

        if added > 0:
            persist()
            update_pool_management_ui()
            add_user_input.value = ""
            tab.toast(title="User Added", description=f"Added {added} user(s) to whitelist.", type="SUCCESS")
        else:
            tab.toast(title="Already Added", description="User is already whitelisted.", type="INFO")

    async def on_add_role():
        raw = (add_role_input.value or "").strip()
        parts = [r.strip() for r in raw.split(",") if r.strip().isdigit()]
        if not parts:
            tab.toast(title="Invalid Role ID", description="Please enter a valid numeric Role ID.", type="ERROR")
            return

        added = 0
        if "whitelist_metadata" not in settings:
            settings["whitelist_metadata"] = {}

        for rid in parts:
            if rid not in settings["whitelist"]["roles"]:
                settings["whitelist"]["roles"].append(rid)
                r_name = f"Role-{rid}"
                g_name = ""
                for guild in getattr(bot, "guilds", []):
                    r_obj = guild.get_role(int(rid))
                    if r_obj:
                        r_name = r_obj.name
                        g_name = guild.name
                        break
                settings["whitelist_metadata"][f"role:{rid}"] = {
                    "type": "role",
                    "name": r_name,
                    "guild_name": g_name
                }
                added += 1

        if added > 0:
            persist()
            update_pool_management_ui()
            add_role_input.value = ""
            tab.toast(title="Role Added", description=f"Added {added} role(s) to whitelist.", type="SUCCESS")
        else:
            tab.toast(title="Already Added", description="Role is already whitelisted.", type="INFO")

    add_user_btn.onClick = on_add_user
    add_role_btn.onClick = on_add_role

    async def on_remove_selected_entry():
        sel = pool_remove_select.selected_items
        if not sel or sel[0] in ("none", "__none__"):
            tab.toast(title="No Selection", description="Please select an entry to remove.", type="ERROR")
            return

        entry_key = sel[0]
        if entry_key.startswith("user:"):
            uid = entry_key.split("user:")[1]
            if uid in settings["whitelist"].get("users", []):
                settings["whitelist"]["users"].remove(uid)
                settings.get("whitelist_metadata", {}).pop(f"user:{uid}", None)
                persist()
                update_pool_management_ui()
                tab.toast(title="Removed", description=f"Removed user {uid} from whitelist.", type="SUCCESS")
        elif entry_key.startswith("role:"):
            rid = entry_key.split("role:")[1]
            if rid in settings["whitelist"].get("roles", []):
                settings["whitelist"]["roles"].remove(rid)
                settings.get("whitelist_metadata", {}).pop(f"role:{rid}", None)
                persist()
                update_pool_management_ui()
                tab.toast(title="Removed", description=f"Removed role {rid} from whitelist.", type="SUCCESS")
        elif entry_key.startswith("channel:"):
            cid = entry_key.split("channel:")[1]
            if cid in settings.get("watched_channels", []):
                settings["watched_channels"].remove(cid)
                settings.get("watched_channel_metadata", {}).pop(cid, None)
                persist()
                update_telemetry_ui()
                update_pool_management_ui()
                tab.toast(title="Removed", description=f"Removed channel {cid} from pool.", type="SUCCESS")

    async def on_clear_all_whitelist():
        settings["whitelist"]["users"] = []
        settings["whitelist"]["roles"] = []
        settings["whitelist_metadata"] = {}
        persist()
        update_pool_management_ui()
        tab.toast(title="Whitelist Cleared", description="All whitelisted users and roles have been removed.", type="SUCCESS")

    async def on_clear_all_channels():
        settings["watched_channels"] = []
        settings["watched_channel_metadata"] = {}
        persist()
        update_telemetry_ui()
        update_pool_management_ui()
        tab.toast(title="Channels Cleared", description="All watched channels have been removed.", type="SUCCESS")

    pool_remove_btn.onClick = on_remove_selected_entry
    clear_all_wl_btn.onClick = on_clear_all_whitelist
    clear_all_ch_btn.onClick = on_clear_all_channels

    async def on_reset_stats():
        settings["stats"] = {
            "total_triggers": 0,
            "messages_deleted": 0,
            "users_kicked": 0,
            "users_banned": 0,
            "users_timed_out": 0,
            "whitelist_bypasses": 0,
            "last_trigger_time": "Never"
        }
        persist()
        update_telemetry_ui()
        tab.toast(title="Stats Reset", description="Honeypot telemetry counters have been cleared.", type="SUCCESS")

    reset_stats_btn.onClick = on_reset_stats

    async def on_clear_logs():
        settings["incidents"] = []
        persist()
        update_incidents_table()
        display_incident_inspector(None)
        tab.toast(title="Logs Cleared", description="Incident history table has been cleared.", type="SUCCESS")

    clear_logs_btn.onClick = on_clear_logs

    # ==================== INITIAL POPULATION ====================
    servers_list = [{"id": "none", "title": "Select a server..."}]
    for guild in getattr(bot, 'guilds', []):
        try:
            icon_url = guild.icon.url if (hasattr(guild, 'icon') and guild.icon) else "https://cdn.discordapp.com/embed/avatars/0.png"
            servers_list.append({
                "id": str(guild.id),
                "title": guild.name,
                "iconUrl": icon_url
            })
        except Exception:
            pass

    if len(servers_list) > 1:
        server_select.items = servers_list
        server_select.selected_items = ["none"]
    else:
        server_select.items = [{"id": "none", "title": "No servers available"}]
        server_select.selected_items = ["none"]

    channel_select.items = [{"id": "none", "title": "Select a server first..."}]
    channel_select.selected_items = ["none"]
    channel_id_input.value = ""

    update_telemetry_ui()
    update_pool_management_ui()
    update_incidents_table()
    if settings.get("incidents"):
        display_incident_inspector(settings["incidents"][0])

    tab.render()

honeypot_script()
