import json
import random
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

@nightyScript(
    name="MrBeast Scam Detector",
    author="factz",
    description="Real-time multi-channel attachment detector for compromised accounts spreading MrBeast / Nitro QR scams.",
    usage="<p>scam | <p>scam toggle | <p>scam stats | <p>scam clear | <p>scam test"
)
def mrbeast_scam_detector_script():
    """
    MRBEAST SCAM DETECTOR
    ---------------------
    Real-time security monitor that tracks cross-channel attachment bursts
    commonly used by compromised tokens blasting fake MrBeast / QR Nitro giveaways.
    Supports auto-block, auto-deletion (with perms check), auto-kick (with perms check),
    auto-ban (with perms check), Notification Center alerts, in-UI simulation testing, and a live UI dashboard.
    """
    import json
    import random
    import asyncio
    import subprocess
    from pathlib import Path
    from datetime import datetime

    # ==================== INITIALIZATION & PERSISTENCE ====================
    SCRIPT_NAME = "MrBeastScamDetector"
    JSON_DIR = Path(getScriptsPath()) / "json"
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PATH = JSON_DIR / "mrbeast_scam_detector.json"

    DEFAULT_CONFIG = {
        "enabled": True,
        "min_channels": 3,
        "time_window_seconds": 15,
        "auto_block": True,
        "auto_delete": True,
        "auto_kick": False,
        "auto_ban": False,
        "ui_alerts": True,
        "whitelisted_users": [],
        "whitelisted_guilds": []
    }

    def load_stored_data():
        if not DATA_PATH.exists():
            initial_data = {
                "config": DEFAULT_CONFIG,
                "stats": {
                    "scanned_messages": 0,
                    "caught_scammers": 0,
                    "deleted_messages": 0,
                    "blocked_users": 0,
                    "kicked_users": 0,
                    "banned_users": 0,
                    "last_incident_time": "Never"
                },
                "incidents": []
            }
            try:
                with open(DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(initial_data, f, indent=4)
            except Exception as e:
                print(f"[{SCRIPT_NAME}] Error creating initial data file: {e}", type_="ERROR")
            return initial_data

        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all default config keys exist
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data.get("config", {}):
                        data.setdefault("config", {})[k] = v
                return data
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error loading data file: {e}", type_="ERROR")
            return {"config": DEFAULT_CONFIG, "stats": {}, "incidents": []}

    stored_data = load_stored_data()
    runtime_config = stored_data.get("config", DEFAULT_CONFIG)
    runtime_stats = stored_data.get("stats", {
        "scanned_messages": 0,
        "caught_scammers": 0,
        "deleted_messages": 0,
        "blocked_users": 0,
        "kicked_users": 0,
        "banned_users": 0,
        "last_incident_time": "Never"
    })
    incident_logs = stored_data.get("incidents", [])

    def save_stored_data():
        try:
            payload = {
                "config": runtime_config,
                "stats": runtime_stats,
                "incidents": incident_logs[:100]  # Keep last 100 incidents
            }
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error saving data file: {e}", type_="ERROR")

    # In-memory tracking structures
    user_activity_window = {}
    handled_cooldowns = {}
    flagged_watch_expiry = {}      # author_id -> timestamp until which any 1 message triggers instant deletion
    active_user_incident = {}      # author_id -> incident_record dict (current open session)
    active_incident_expiry = {}    # author_id -> timestamp when active incident session closes (20s after last message)

    ui_refs = {}

    # ==================== UTILS ====================
    def safe_create_task(coro):
        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(coro)
        except RuntimeError:
            if hasattr(bot, 'loop') and bot.loop and not bot.loop.is_closed():
                return bot.loop.create_task(coro)
        return None

    def copy_to_clipboard(text: str) -> bool:
        """Copies text to Windows clipboard."""
        try:
            p = subprocess.Popen('clip', stdin=subprocess.PIPE, shell=True)
            p.communicate(input=text.encode('utf-16le'))
            return True
        except Exception:
            pass
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            r.destroy()
            return True
        except Exception:
            pass
        return False

    def delete_after():
        return getConfigData().get('deletetimer', 10)

    def get_random_simulation_origin():
        """
        Picks a random guild and its real text channels from bot.guilds
        if available, otherwise falls back to realistic mock defaults.
        """
        guild_name = "Global Test Server"
        guild_id = "999888777666"
        channels = ["general", "announcements", "media", "bot-commands", "lounge"]

        if hasattr(bot, 'guilds') and bot.guilds:
            valid_guilds = [g for g in bot.guilds if hasattr(g, 'text_channels') and g.text_channels]
            if valid_guilds:
                chosen_guild = random.choice(valid_guilds)
                guild_name = getattr(chosen_guild, 'name', guild_name)
                guild_id = str(getattr(chosen_guild, 'id', guild_id))
                ch_names = [getattr(ch, 'name', str(ch.id)) for ch in chosen_guild.text_channels[:20]]
                if len(ch_names) >= 3:
                    channels = random.sample(ch_names, min(4, len(ch_names)))
                elif ch_names:
                    channels = ch_names
        return guild_name, guild_id, channels

    # ==================== UI UPDATE HELPERS ====================
    def update_threat_monitor_ui():
        """Updates the Live Threat Monitor Card metrics."""
        try:
            if not ui_refs.get('monitor_status_text'):
                return

            now_ts = datetime.now().timestamp()
            active_scammers = [uid for uid, exp in active_incident_expiry.items() if now_ts <= exp]

            if not runtime_config.get("enabled", True):
                ui_refs['monitor_status_text'].content = "Status: Disabled"
                ui_refs['monitor_status_text'].color = "#ef4444"
            elif active_scammers:
                ui_refs['monitor_status_text'].content = f"Status: Threat Detected ({len(active_scammers)} Scammer(s) Monitored)"
                ui_refs['monitor_status_text'].color = "#f97316"
            else:
                ui_refs['monitor_status_text'].content = "Status: Live Scanning & Armed"
                ui_refs['monitor_status_text'].color = "#22c55e"

            if ui_refs.get('stat_scanned'):
                ui_refs['stat_scanned'].content = f"Messages Scanned: {runtime_stats.get('scanned_messages', 0):,}"
            if ui_refs.get('stat_caught'):
                ui_refs['stat_caught'].content = f"Scammers Caught: {runtime_stats.get('caught_scammers', 0):,}"
            if ui_refs.get('stat_deleted'):
                ui_refs['stat_deleted'].content = f"Messages Deleted: {runtime_stats.get('deleted_messages', 0):,}"
            if ui_refs.get('stat_blocked'):
                ui_refs['stat_blocked'].content = f"Users Blocked: {runtime_stats.get('blocked_users', 0):,}"
            if ui_refs.get('stat_kicked'):
                ui_refs['stat_kicked'].content = f"Users Kicked: {runtime_stats.get('kicked_users', 0):,}"
            if ui_refs.get('stat_banned'):
                ui_refs['stat_banned'].content = f"Users Banned: {runtime_stats.get('banned_users', 0):,}"
            if ui_refs.get('stat_watchlist'):
                ui_refs['stat_watchlist'].content = f"Active Watchlist: {len(active_scammers)} user(s)"
            if ui_refs.get('stat_last_time'):
                ui_refs['stat_last_time'].content = f"Last Incident: {runtime_stats.get('last_incident_time', 'Never')}"

        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error updating threat monitor UI: {e}", type_="ERROR")

    def update_incidents_table():
        """Populates the incidents UI.Table with caught scam logs."""
        try:
            if not ui_refs.get('incidents_table'):
                return

            rows = []
            default_avatar = "https://cdn.discordapp.com/embed/avatars/0.png"

            for inc in incident_logs:
                rows.append({
                    "id": str(inc.get("id", "")),
                    "cells": [
                        {
                            "text": inc.get("user_name", "Unknown User"),
                            "subtext": f"ID: {inc.get('user_id')}",
                            "imageUrl": inc.get("avatar_url") or default_avatar
                        },
                        {"text": str(inc.get("user_id", "-"))},
                        {"text": str(inc.get("guild_name", "-"))},
                        {"text": f"{len(inc.get('channels', []))} channels", "color": "orange"},
                        {"text": f"{inc.get('attachment_count', 4)} files", "color": "red"},
                        {"text": str(inc.get("actions_taken", "Logged")), "color": "green" if ("Blocked" in inc.get("actions_taken", "") or "Kicked" in inc.get("actions_taken", "") or "Banned" in inc.get("actions_taken", "")) else "gray"},
                        {"text": str(inc.get("timestamp", "-"))},
                        {}  # Actions column (Inspect / Copy ID)
                    ]
                })

            if not rows:
                rows = [{
                    "id": "none",
                    "cells": [
                        {"text": "No scam incidents detected yet", "imageUrl": default_avatar},
                        {"text": "-"},
                        {"text": "-"},
                        {"text": "0 channels", "color": "gray"},
                        {"text": "0 files", "color": "gray"},
                        {"text": "None", "color": "gray"},
                        {"text": "-"},
                        {}
                    ]
                }]

            ui_refs['incidents_table'].rows = rows

        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error updating incidents table: {e}", type_="ERROR")

    def display_incident_inspector(incident_data):
        """Populates the Incident Forensic Inspector card."""
        try:
            if not incident_data:
                ui_refs['insp_name'].content = "Select an incident from the table above to view forensic breakdown."
                ui_refs['insp_user_id'].content = "User ID: -"
                ui_refs['insp_guild_info'].content = "Server: - (Guild ID: -)"
                ui_refs['insp_velocity'].content = "Velocity: - channels in -s"
                ui_refs['insp_files'].content = "Attachments: - per message"
                ui_refs['insp_timestamp'].content = "Timestamp: -"
                ui_refs['insp_actions'].content = "Mitigations: -"
                ui_refs['insp_channels_list'].content = "Channels Spammed: None"
                ui_refs['insp_sample_urls'].content = "Attachment Links: None"
                return

            ui_refs['insp_name'].content = f"{incident_data.get('user_name')} ({incident_data.get('user_tag', 'Unknown')})"
            ui_refs['insp_user_id'].content = f"User ID: {incident_data.get('user_id')}"
            ui_refs['insp_guild_info'].content = f"Server: {incident_data.get('guild_name')} (ID: {incident_data.get('guild_id')})"

            channels = incident_data.get('channels', [])
            duration = incident_data.get('duration_seconds', 0)
            ui_refs['insp_velocity'].content = f"Velocity: {len(channels)} channels within {duration:.1f}s"
            ui_refs['insp_files'].content = f"Attachments: {incident_data.get('attachment_count', 4)} files per message"
            ui_refs['insp_timestamp'].content = f"Timestamp: {incident_data.get('timestamp')}"
            ui_refs['insp_actions'].content = f"Mitigations: {incident_data.get('actions_taken', 'Logged')}"

            channels_str = ", ".join([f"#{c}" for c in channels]) if channels else "None"
            ui_refs['insp_channels_list'].content = f"Channels ({len(channels)}): {channels_str}"

            urls = incident_data.get('attachment_urls', [])
            urls_str = "\n".join(urls[:6]) if urls else "No attachment URLs captured"
            ui_refs['insp_sample_urls'].content = f"Attachment URLs:\n{urls_str}"

        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error displaying incident inspector: {e}", type_="ERROR")

    # ==================== DETECTION ENGINE ====================
    async def process_scam_detection(author_id, guild_id, target_messages, author_user, guild_obj):
        """
        Executes automated mitigations when a user meets the scam threshold:
        1. Waits 3 seconds before executing actions
        2. Auto-blocks user (if enabled)
        3. Auto-deletes raid messages (checks manage_messages permission first)
        4. Auto-kicks user (checks kick_members permission first)
        5. Auto-bans user (checks ban_members permission first)
        6. Updates existing active incident within 20s, or creates a new incident if >20s passed
        7. Sends UI toast alerts and logs to Notification Center
        """
        try:
            # 3 second grace delay before mitigation execution
            await asyncio.sleep(3.0)

            # Dynamically refresh target_messages to capture ALL additional channels and attachments
            # that arrived during the 3-second grace period
            time_window = float(runtime_config.get("time_window_seconds", 15))
            now = datetime.now()
            now_ts = now.timestamp()
            all_user_records = user_activity_window.get(author_id, [])
            latest_records = [r for r in all_user_records if (now_ts - r["time"]) <= (time_window + 5.0) and r["guild_id"] == guild_id]
            if latest_records:
                target_messages = latest_records

            actions_taken_list = []

            # Find our member object in guild to accurately check permissions
            me = None
            if guild_obj:
                me = getattr(guild_obj, 'me', None) or (guild_obj.get_member(bot.user.id) if hasattr(guild_obj, 'get_member') else None)

            # 1. Auto-Block (Does not require captcha)
            if runtime_config.get("auto_block", True) and author_user:
                try:
                    if hasattr(author_user, 'block') and callable(author_user.block):
                        await author_user.block()
                        actions_taken_list.append("Blocked")
                        runtime_stats["blocked_users"] = runtime_stats.get("blocked_users", 0) + 1
                except Exception as e:
                    print(f"[{SCRIPT_NAME}] Failed to block scammer {author_id}: {e}", type_="ERROR")

            # 2. Auto-Delete Messages (Strict permission check: manage_messages or administrator)
            deleted_count = 0
            if runtime_config.get("auto_delete", True) and me:
                for rec in target_messages:
                    msg_obj = rec.get("message_obj")
                    if msg_obj:
                        ch = getattr(msg_obj, 'channel', None)
                        can_delete = False
                        if ch and hasattr(ch, 'permissions_for'):
                            perms = ch.permissions_for(me)
                            can_delete = getattr(perms, 'manage_messages', False) or getattr(perms, 'administrator', False)
                        elif hasattr(me, 'guild_permissions'):
                            perms = me.guild_permissions
                            can_delete = getattr(perms, 'manage_messages', False) or getattr(perms, 'administrator', False)

                        if can_delete:
                            try:
                                await msg_obj.delete()
                                deleted_count += 1
                            except Exception:
                                pass

                if deleted_count > 0:
                    actions_taken_list.append(f"Deleted {deleted_count} msgs")
                    runtime_stats["deleted_messages"] = runtime_stats.get("deleted_messages", 0) + deleted_count

            # 3. Auto-Kick (Strict permission check: kick_members or administrator)
            if runtime_config.get("auto_kick", False) and guild_obj and author_user and me:
                has_kick_perms = getattr(me.guild_permissions, 'kick_members', False) or getattr(me.guild_permissions, 'administrator', False)
                if has_kick_perms and hasattr(guild_obj, 'kick'):
                    try:
                        await guild_obj.kick(author_user, reason="MrBeast Scam Velocity Raid detected by Scam Detector")
                        actions_taken_list.append("Kicked")
                        runtime_stats["kicked_users"] = runtime_stats.get("kicked_users", 0) + 1
                    except Exception as e:
                        print(f"[{SCRIPT_NAME}] Failed to kick scammer {author_id}: {e}", type_="ERROR")

            # 4. Auto-Ban (Strict permission check: ban_members or administrator)
            if runtime_config.get("auto_ban", False) and guild_obj and author_user and me:
                has_ban_perms = getattr(me.guild_permissions, 'ban_members', False) or getattr(me.guild_permissions, 'administrator', False)
                if has_ban_perms and hasattr(guild_obj, 'ban'):
                    try:
                        await guild_obj.ban(author_user, reason="MrBeast Scam Velocity Raid detected by Scam Detector")
                        actions_taken_list.append("Banned")
                        runtime_stats["banned_users"] = runtime_stats.get("banned_users", 0) + 1
                    except Exception as e:
                        print(f"[{SCRIPT_NAME}] Failed to ban scammer {author_id}: {e}", type_="ERROR")

            if not actions_taken_list:
                actions_taken_list.append("Detected & Logged")

            actions_str = ", ".join(actions_taken_list)

            # Extract incident metadata
            user_name = getattr(author_user, 'display_name', None) or getattr(author_user, 'name', f"User-{author_id}")
            user_tag = getattr(author_user, 'name', user_name)

            avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"
            if hasattr(author_user, 'avatar') and author_user.avatar:
                avatar_url = str(getattr(author_user.avatar, 'url', author_user.avatar))
            elif hasattr(author_user, 'display_avatar') and author_user.display_avatar:
                avatar_url = str(author_user.display_avatar.url)

            guild_name = guild_obj.name if guild_obj else "Unknown Server"

            channels_set = list(set([r["channel_name"] for r in target_messages]))
            all_urls = []
            for r in target_messages:
                all_urls.extend(r.get("attachment_urls", []))
            all_urls = list(set(all_urls))

            first_time = target_messages[0]["time"]
            last_time = target_messages[-1]["time"]
            duration = max(0.1, last_time - first_time)

            # Check if user already has an active incident session within 20s
            is_existing_session = (author_id in active_user_incident) and (now_ts <= active_incident_expiry.get(author_id, 0))

            if is_existing_session:
                incident_record = active_user_incident[author_id]
                # Merge channels
                existing_channels = incident_record.get("channels", [])
                for ch_name in channels_set:
                    if ch_name not in existing_channels:
                        existing_channels.append(ch_name)
                incident_record["channels"] = existing_channels

                # Merge attachment URLs
                existing_urls = incident_record.get("attachment_urls", [])
                for u in all_urls:
                    if u not in existing_urls:
                        existing_urls.append(u)
                incident_record["attachment_urls"] = existing_urls

                # Update duration and actions
                incident_record["duration_seconds"] = max(incident_record.get("duration_seconds", 0.1), now_ts - first_time)
                incident_record["actions_taken"] = actions_str
                incident_record["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")

                # Extend active session and watch expiry for 20 seconds
                active_incident_expiry[author_id] = now_ts + 20.0
                flagged_watch_expiry[author_id] = now_ts + 20.0

                # Update persistence & UI in place
                save_stored_data()
                update_threat_monitor_ui()
                update_incidents_table()
                display_incident_inspector(incident_record)

                print(
                    f"Scam Raid Updated: {user_name} (ID: {author_id}) in '{guild_name}' | "
                    f"Total {len(existing_channels)} channels | Actions: {actions_str}",
                    type_="INFO"
                )
                if runtime_config.get("ui_alerts", True):
                    tab.toast(
                        type="INFO",
                        title=f"Scam Raid Updated: {user_name}",
                        description=f"User ID: {author_id} | Total {len(existing_channels)} channels in {guild_name} | {actions_str}"
                    )

            else:
                # Create a brand new incident session
                incident_id = f"inc_{int(now_ts)}_{author_id}"
                incident_record = {
                    "id": incident_id,
                    "user_id": str(author_id),
                    "user_name": user_name,
                    "user_tag": user_tag,
                    "avatar_url": avatar_url,
                    "guild_id": str(guild_id) if guild_id else "Unknown",
                    "guild_name": guild_name,
                    "channels": channels_set,
                    "attachment_count": 4,
                    "duration_seconds": duration,
                    "actions_taken": actions_str,
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "attachment_urls": all_urls
                }

                # Set 20-second active session window
                active_user_incident[author_id] = incident_record
                active_incident_expiry[author_id] = now_ts + 20.0
                flagged_watch_expiry[author_id] = now_ts + 20.0

                # Update stats and persistence
                runtime_stats["caught_scammers"] = runtime_stats.get("caught_scammers", 0) + 1
                runtime_stats["last_incident_time"] = now.strftime("%H:%M:%S")
                incident_logs.insert(0, incident_record)
                save_stored_data()

                # Update UI Tab
                update_threat_monitor_ui()
                update_incidents_table()
                display_incident_inspector(incident_record)

                # 1. Notification Center Notification (Appears under bell icon in Nighty dashboard)
                print(
                    f"Scam Raid Caught: {user_name} (ID: {author_id}) in '{guild_name}' ({guild_id}) | "
                    f"Spammed {len(channels_set)} channels (4 attachments/msg) | "
                    f"Actions: {actions_str}",
                    type_="INFO"
                )

                # 2. Toast Alert in Nighty
                if runtime_config.get("ui_alerts", True):
                    tab.toast(
                        type="INFO",
                        title=f"Scam Raid: {user_name}",
                        description=f"User ID: {author_id} | Server: {guild_name} ({len(channels_set)} channels) | {actions_str}"
                    )
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error in process_scam_detection: {e}", type_="ERROR")

    @bot.listen("on_message")
    async def on_scam_detector_message(message):
        """Listens to all incoming messages and evaluates attachment velocity."""
        try:
            # Real-time counter: increments on all incoming gateway message events
            runtime_stats["scanned_messages"] = runtime_stats.get("scanned_messages", 0) + 1
            if ui_refs.get('stat_scanned'):
                try:
                    ui_refs['stat_scanned'].content = f"Messages Scanned: {runtime_stats.get('scanned_messages', 0):,}"
                except Exception:
                    pass

            if runtime_stats["scanned_messages"] % 25 == 0:
                save_stored_data()

            # 1. Ignore own messages
            if getattr(message.author, 'id', None) == bot.user.id:
                return

            # 2. Check if detector enabled
            if not runtime_config.get("enabled", True):
                return

            # 3. Ignore bots if configured
            if getattr(message.author, 'bot', False):
                return

            # 4. Whitelist checks
            author_id = str(message.author.id)
            if author_id in runtime_config.get("whitelisted_users", []):
                return

            guild = getattr(message, 'guild', None)
            guild_id = str(guild.id) if guild else "DM"
            if guild_id in runtime_config.get("whitelisted_guilds", []):
                return

            now_ts = datetime.now().timestamp()

            # 5. Evaluate attachment / embed count (MrBeast scam raids are 4 attachments in 1 message)
            attachments_list = getattr(message, 'attachments', []) or []
            embeds_list = getattr(message, 'embeds', []) or []
            att_count = len(attachments_list) + len(embeds_list)

            if att_count < 4:
                return

            channel_name = getattr(message.channel, 'name', str(message.channel.id))

            # Check if user is on the Active 20-Second Incident Session & Watchlist
            watch_until = active_incident_expiry.get(author_id, 0)
            if now_ts <= watch_until:
                # Extend their active session & watch timer for 20 seconds from this message
                active_incident_expiry[author_id] = now_ts + 20.0
                flagged_watch_expiry[author_id] = now_ts + 20.0

                # Execute instant follow-up deletion on this single message
                can_delete = False
                deleted_msg = False
                me = None
                if guild:
                    me = getattr(guild, 'me', None) or (guild.get_member(bot.user.id) if hasattr(guild, 'get_member') else None)

                if me and hasattr(message.channel, 'permissions_for'):
                    perms = message.channel.permissions_for(me)
                    can_delete = getattr(perms, 'manage_messages', False) or getattr(perms, 'administrator', False)
                elif me and hasattr(me, 'guild_permissions'):
                    perms = me.guild_permissions
                    can_delete = getattr(perms, 'manage_messages', False) or getattr(perms, 'administrator', False)

                if runtime_config.get("auto_delete", True) and can_delete:
                    try:
                        await message.delete()
                        deleted_msg = True
                        runtime_stats["deleted_messages"] = runtime_stats.get("deleted_messages", 0) + 1
                    except Exception:
                        pass

                # Update the existing incident record in place
                active_inc = active_user_incident.get(author_id)
                if active_inc:
                    if channel_name not in active_inc.get("channels", []):
                        active_inc["channels"].append(channel_name)
                    for a in attachments_list:
                        if hasattr(a, 'url') and a.url and a.url not in active_inc.get("attachment_urls", []):
                            active_inc.setdefault("attachment_urls", []).append(a.url)
                    active_inc["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    display_incident_inspector(active_inc)

                save_stored_data()
                update_threat_monitor_ui()
                update_incidents_table()

                total_ch = len(active_inc["channels"]) if active_inc else 1
                if deleted_msg:
                    print(
                        f"Scam Raid Intercepted: Deleted follow-up message from {message.author.name} (ID: {author_id}) in #{channel_name} (Total: {total_ch} channels)",
                        type_="SUCCESS"
                    )
                    if runtime_config.get("ui_alerts", True):
                        tab.toast(
                            type="SUCCESS",
                            title="Raid Message Deleted",
                            description=f"Deleted message in #{channel_name} ({total_ch} channels total for {message.author.name})"
                        )
                return

            # 6. Sliding window cross-channel tracking
            time_window = float(runtime_config.get("time_window_seconds", 15))

            attachment_urls = []
            for a in attachments_list:
                if hasattr(a, 'url') and a.url:
                    attachment_urls.append(a.url)

            record = {
                "channel_id": message.channel.id,
                "channel_name": channel_name,
                "guild_id": guild_id,
                "message_id": message.id,
                "time": now_ts,
                "attachment_count": att_count,
                "attachment_urls": attachment_urls,
                "message_obj": message
            }

            user_history = user_activity_window.get(author_id, [])
            # Prune older than time window
            valid_records = [r for r in user_history if (now_ts - r["time"]) <= time_window and r["guild_id"] == guild_id]
            valid_records.append(record)
            user_activity_window[author_id] = valid_records

            # Count distinct channels spammed in this guild
            distinct_channels = list(set([r["channel_id"] for r in valid_records]))
            min_channels = int(runtime_config.get("min_channels", 3))

            # Check cooldown to prevent duplicate triggers within 5 seconds
            last_handled = handled_cooldowns.get((author_id, guild_id), 0)
            if (now_ts - last_handled) < 5:
                return

            if len(distinct_channels) >= min_channels:
                handled_cooldowns[(author_id, guild_id)] = now_ts
                # Trigger mitigation asynchronously (includes 3s delay)
                safe_create_task(process_scam_detection(
                    author_id=author_id,
                    guild_id=guild_id,
                    target_messages=list(valid_records),
                    author_user=message.author,
                    guild_obj=guild
                ))
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Error in on_scam_detector_message: {e}", type_="ERROR")

    # ==================== SIMULATION LOGIC ====================
    def run_simulation_incident(author_id: str, user_name: str, guild_name: str, guild_id: str, avatar_url: str = None, sample_channels: list = None):
        """
        Executes a dry-run test simulation incident with 20-second session merging.
        Returns a tuple: (incident_record, is_updated_boolean)
        """
        now_dt = datetime.now()
        now_ts = now_dt.timestamp()
        default_avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
        avatar_url = avatar_url or default_avatar
        sample_channels = sample_channels or ["general", "announcements", "media", "bot-commands"]

        is_active_session = (author_id in active_user_incident) and (now_ts <= active_incident_expiry.get(author_id, 0))

        if is_active_session:
            simulated_incident = active_user_incident[author_id]
            existing_channels = list(simulated_incident.get("channels", []))

            # Add up to 2 new channels per simulation trigger
            added_count = 0
            for ch in sample_channels:
                if ch not in existing_channels:
                    existing_channels.append(ch)
                    added_count += 1
                    if added_count >= 2:
                        break

            # If server text channels are all used up, generate sequential dynamic channels
            while added_count < 2:
                next_ch = f"channel-{len(existing_channels) + 1}"
                if next_ch not in existing_channels:
                    existing_channels.append(next_ch)
                else:
                    existing_channels.append(f"raid-{len(existing_channels) + 1}")
                added_count += 1

            simulated_incident["channels"] = existing_channels
            simulated_incident["timestamp"] = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            simulated_incident["duration_seconds"] = simulated_incident.get("duration_seconds", 2.4) + 1.8

            active_incident_expiry[author_id] = now_ts + 20.0
            flagged_watch_expiry[author_id] = now_ts + 20.0

            save_stored_data()
            update_threat_monitor_ui()
            update_incidents_table()
            display_incident_inspector(simulated_incident)

            print(
                f"Simulated Scam Raid Updated: {user_name} (ID: {author_id}) in '{simulated_incident.get('guild_name', guild_name)}' | "
                f"Now {len(existing_channels)} channels total | Actions: Simulated Alert",
                type_="INFO"
            )
            tab.toast(type="INFO", title="Simulation Updated", description=f"Updated active incident for {user_name} (Now {len(existing_channels)} channels)")
            return simulated_incident, True
        else:
            simulated_incident = {
                "id": f"sim_{int(now_ts)}_{author_id}",
                "user_id": author_id,
                "user_name": user_name,
                "user_tag": f"{user_name}#0000",
                "avatar_url": avatar_url,
                "guild_id": guild_id,
                "guild_name": guild_name,
                "channels": sample_channels[:3],
                "attachment_count": 4,
                "duration_seconds": 2.4,
                "actions_taken": "Simulated Alert",
                "timestamp": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "attachment_urls": ["https://cdn.discordapp.com/embed/avatars/0.png"]
            }
            active_user_incident[author_id] = simulated_incident
            active_incident_expiry[author_id] = now_ts + 20.0
            flagged_watch_expiry[author_id] = now_ts + 20.0

            incident_logs.insert(0, simulated_incident)
            runtime_stats["caught_scammers"] = runtime_stats.get("caught_scammers", 0) + 1
            runtime_stats["last_incident_time"] = now_dt.strftime("%H:%M:%S")
            save_stored_data()
            update_threat_monitor_ui()
            update_incidents_table()
            display_incident_inspector(simulated_incident)

            print(
                f"Simulated Scam Caught: {user_name} (User ID: {author_id}) in '{guild_name}' | "
                f"Spammed {len(simulated_incident['channels'])} channels | Actions: Simulated Alert",
                type_="INFO"
            )
            tab.toast(type="INFO", title="Simulation Started", description=f"Simulated raid in '{guild_name}' ({len(simulated_incident['channels'])} channels)")
            return simulated_incident, False

    # ==================== UI TAB DEFINITION ====================
    tab = Tab(name="Scam Detector", icon="search", gap=4, title="MrBeast Scam Detector")

    main_container = tab.create_container(type="rows", gap=4)

    # ════════════════════════════════════════════════════════
    # TOP SECTION - 2 Equal Half-Width Cards (Settings & Threat Monitor)
    # ════════════════════════════════════════════════════════
    top_container = main_container.create_container(type="columns", gap=4)

    # Card 1: Detection Settings & Triggers (Left Half)
    settings_card = top_container.create_card(type="rows", gap=3, width="full")
    settings_card.create_ui_element(UI.Text, content="Detection Rules & Actions", size="lg", weight="bold")
    settings_card.create_ui_element(
        UI.Text,
        content="Configure cross-channel triggers and automated mitigations (fixed at 4 attachments).",
        size="sm",
        color="#888888"
    )

    enabled_toggle = settings_card.create_ui_element(
        UI.Toggle, label="Enable Scam Detector", checked=runtime_config.get("enabled", True)
    )
    ui_refs['enabled_toggle'] = enabled_toggle

    # Sliders / Inputs for Thresholds (Min Channels & Window)
    thresh_group = settings_card.create_group(type="columns", gap=2)
    chan_thresh_input = thresh_group.create_ui_element(
        UI.Input,
        label="Min Channels",
        value=str(runtime_config.get("min_channels", 3)),
        placeholder="e.g. 3",
        full_width=True
    )
    ui_refs['chan_thresh_input'] = chan_thresh_input

    time_win_input = thresh_group.create_ui_element(
        UI.Input,
        label="Window (Seconds)",
        value=str(runtime_config.get("time_window_seconds", 15)),
        placeholder="e.g. 15",
        full_width=True
    )
    ui_refs['time_win_input'] = time_win_input

    # Actions Toggles Grid (2x2)
    actions_grid = settings_card.create_group(type="columns", gap=2)
    col_act_left = actions_grid.create_group(type="rows", gap=1)
    auto_block_toggle = col_act_left.create_ui_element(
        UI.Toggle, label="Auto-Block User", checked=runtime_config.get("auto_block", True)
    )
    ui_refs['auto_block_toggle'] = auto_block_toggle

    auto_delete_toggle = col_act_left.create_ui_element(
        UI.Toggle, label="Auto-Delete (with perms)", checked=runtime_config.get("auto_delete", True)
    )
    ui_refs['auto_delete_toggle'] = auto_delete_toggle

    col_act_right = actions_grid.create_group(type="rows", gap=1)
    auto_kick_toggle = col_act_right.create_ui_element(
        UI.Toggle, label="Auto-Kick (with perms)", checked=runtime_config.get("auto_kick", False)
    )
    ui_refs['auto_kick_toggle'] = auto_kick_toggle

    auto_ban_toggle = col_act_right.create_ui_element(
        UI.Toggle, label="Auto-Ban (with perms)", checked=runtime_config.get("auto_ban", False)
    )
    ui_refs['auto_ban_toggle'] = auto_ban_toggle

    btn_row = settings_card.create_group(type="columns", gap=2)
    save_config_btn = btn_row.create_ui_element(
        UI.Button, label="Save Settings", variant="cta", color="primary", full_width=True
    )
    reset_config_btn = btn_row.create_ui_element(
        UI.Button, label="Reset Defaults", variant="bordered", color="default"
    )

    # Card 2: Live Threat Monitor (Right Half)
    monitor_card = top_container.create_card(type="rows", gap=3, width="full")
    monitor_card.create_ui_element(UI.Text, content="Live Threat Monitor & Stats", size="lg", weight="bold")
    monitor_card.create_ui_element(
        UI.Text,
        content="Real-time telemetry, mitigations, and live message scanner counters.",
        size="sm",
        color="#888888"
    )

    monitor_status_text = monitor_card.create_ui_element(
        UI.Text, content="Status: Live Scanning & Armed", size="base", color="#22c55e"
    )
    ui_refs['monitor_status_text'] = monitor_status_text

    stats_grid = monitor_card.create_group(type="columns", gap=4)
    stat_col_left = stats_grid.create_group(type="rows", gap=2)
    stat_scanned = stat_col_left.create_ui_element(
        UI.Text, content="Messages Scanned: 0", size="sm", color="#aaaaaa"
    )
    ui_refs['stat_scanned'] = stat_scanned

    stat_caught = stat_col_left.create_ui_element(
        UI.Text, content="Scammers Caught: 0", size="sm", color="#f87171"
    )
    ui_refs['stat_caught'] = stat_caught

    stat_deleted = stat_col_left.create_ui_element(
        UI.Text, content="Messages Deleted: 0", size="sm", color="#888888"
    )
    ui_refs['stat_deleted'] = stat_deleted

    stat_watchlist = stat_col_left.create_ui_element(
        UI.Text, content="Active Watchlist: 0 user(s)", size="sm", color="#60a5fa"
    )
    ui_refs['stat_watchlist'] = stat_watchlist

    stat_col_right = stats_grid.create_group(type="rows", gap=2)
    stat_blocked = stat_col_right.create_ui_element(
        UI.Text, content="Users Blocked: 0", size="sm", color="#888888"
    )
    ui_refs['stat_blocked'] = stat_blocked

    stat_kicked = stat_col_right.create_ui_element(
        UI.Text, content="Users Kicked: 0", size="sm", color="#888888"
    )
    ui_refs['stat_kicked'] = stat_kicked

    stat_banned = stat_col_right.create_ui_element(
        UI.Text, content="Users Banned: 0", size="sm", color="#888888"
    )
    ui_refs['stat_banned'] = stat_banned

    stat_last_time = stat_col_right.create_ui_element(
        UI.Text, content="Last Incident: Never", size="tiny", color="#666666"
    )
    ui_refs['stat_last_time'] = stat_last_time

    clear_stats_btn = monitor_card.create_ui_element(
        UI.Button, label="Clear Statistics", variant="bordered", color="default", full_width=True
    )

    # ════════════════════════════════════════════════════════
    # MIDDLE SECTION - Full Width Detected Scam Incidents Table
    # ════════════════════════════════════════════════════════
    table_card = main_container.create_card(type="rows", gap=3, width="full", disallow_shrink=True)

    table_header = table_card.create_group(type="columns", gap=4)
    table_header.create_ui_element(UI.Text, content="Detected Scam Incidents", size="lg", weight="bold")
    
    table_actions = table_header.create_group(type="columns", gap=2)
    table_sim_btn = table_actions.create_ui_element(
        UI.Button, label="Simulate Scam Incident", variant="bordered", color="primary"
    )
    table_clear_btn = table_actions.create_ui_element(
        UI.Button, label="Clear Table Logs", variant="bordered", color="danger"
    )

    def handle_copy_user_id(row_id):
        if not row_id or row_id == "none":
            return
        target_inc = None
        for inc in incident_logs:
            if inc.get("id") == row_id:
                target_inc = inc
                break
        uid = target_inc.get("user_id", row_id) if target_inc else row_id
        if copy_to_clipboard(str(uid)):
            tab.toast(type="SUCCESS", title="Copied", description=f"User ID {uid} copied to clipboard.")
        else:
            tab.toast(type="INFO", title="User ID", description=f"ID: {uid}")

    def handle_view_incident(row_id):
        if not row_id or row_id == "none":
            return
        target_inc = None
        for inc in incident_logs:
            if inc.get("id") == row_id:
                target_inc = inc
                break
        if target_inc:
            display_incident_inspector(target_inc)
            tab.toast(type="INFO", title="Incident Selected", description=f"Loaded incident for {target_inc.get('user_name')}")
        else:
            tab.toast(type="ERROR", title="Not Found", description="Incident data not found.")

    incidents_table = table_card.create_ui_element(
        UI.Table,
        search=True,
        items_per_page=15,
        selectable=False,
        columns=[
            {"type": "text", "label": "Scammer Account"},
            {"type": "text", "label": "User ID"},
            {"type": "text", "label": "Server"},
            {"type": "tag",  "label": "Velocity"},
            {"type": "tag",  "label": "Attachments"},
            {"type": "tag",  "label": "Mitigation"},
            {"type": "text", "label": "Detected At"},
            {
                "type": "button",
                "label": "Actions",
                "buttons": [
                    {"label": "Inspect", "color": "default", "onClick": handle_view_incident},
                    {"label": "Copy ID", "color": "default", "onClick": handle_copy_user_id}
                ]
            }
        ],
        rows=[]
    )
    ui_refs['incidents_table'] = incidents_table

    # ════════════════════════════════════════════════════════
    # BOTTOM SECTION - Full Width Incident Forensic Inspector
    # ════════════════════════════════════════════════════════
    inspector_card = main_container.create_card(type="rows", gap=4, width="full", disallow_shrink=True)
    inspector_card.create_ui_element(UI.Text, content="Incident Forensic Inspector", size="xl", weight="bold")

    insp_name = inspector_card.create_ui_element(
        UI.Text, content="Select an incident from the table above to view forensic breakdown.", size="base", weight="medium", color="#ffffff"
    )
    ui_refs['insp_name'] = insp_name

    # Top Deck: 3 Columns (Identity, Velocity, Actions)
    top_deck = inspector_card.create_group(type="columns", gap=4)

    deck_identity = top_deck.create_group(type="rows", gap=2)
    deck_identity.create_ui_element(UI.Text, content="IDENTITY & GUILD", size="tiny", weight="bold", color="#71717a")
    insp_user_id = deck_identity.create_ui_element(
        UI.Text, content="User ID: -", size="base", weight="medium", color="#d4d4d8"
    )
    ui_refs['insp_user_id'] = insp_user_id
    insp_guild_info = deck_identity.create_ui_element(
        UI.Text, content="Server: - (Guild ID: -)", size="base", weight="medium", color="#d4d4d8"
    )
    ui_refs['insp_guild_info'] = insp_guild_info

    deck_velocity = top_deck.create_group(type="rows", gap=2)
    deck_velocity.create_ui_element(UI.Text, content="VELOCITY & TIMELINE", size="tiny", weight="bold", color="#71717a")
    insp_velocity = deck_velocity.create_ui_element(
        UI.Text, content="Velocity: - channels in -s", size="base", weight="medium", color="#d4d4d8"
    )
    ui_refs['insp_velocity'] = insp_velocity
    insp_files = deck_velocity.create_ui_element(
        UI.Text, content="Attachments: - per message", size="base", weight="medium", color="#d4d4d8"
    )
    ui_refs['insp_files'] = insp_files

    deck_mitigation = top_deck.create_group(type="rows", gap=2)
    deck_mitigation.create_ui_element(UI.Text, content="MITIGATION & TIME", size="tiny", weight="bold", color="#71717a")
    insp_timestamp = deck_mitigation.create_ui_element(
        UI.Text, content="Timestamp: -", size="base", weight="medium", color="#d4d4d8"
    )
    ui_refs['insp_timestamp'] = insp_timestamp
    insp_actions = deck_mitigation.create_ui_element(
        UI.Text, content="Mitigations: -", size="base", weight="medium", color="#60a5fa"
    )
    ui_refs['insp_actions'] = insp_actions

    # Bottom Deck: 2 Columns (Channels list & Attachment URLs)
    bottom_deck = inspector_card.create_group(type="columns", gap=4)

    deck_channels = bottom_deck.create_group(type="rows", gap=2)
    deck_channels.create_ui_element(UI.Text, content="SPAMMED CHANNELS", size="tiny", weight="bold", color="#71717a")
    insp_channels_list = deck_channels.create_ui_element(
        UI.Text, content="Channels Spammed: None", size="base", color="#e4e4e7"
    )
    ui_refs['insp_channels_list'] = insp_channels_list

    deck_urls = bottom_deck.create_group(type="rows", gap=2)
    deck_urls.create_ui_element(UI.Text, content="ATTACHMENT LINKS & FORENSICS", size="tiny", weight="bold", color="#71717a")
    insp_sample_urls = deck_urls.create_ui_element(
        UI.Text, content="Attachment Links: None", size="base", color="#e4e4e7"
    )
    ui_refs['insp_sample_urls'] = insp_sample_urls

    # ==================== UI EVENT HANDLERS ====================
    def handle_ui_simulation():
        """Handler for UI-triggered simulation using a random guild from bot.guilds."""
        try:
            g_name, g_id, sample_chans = get_random_simulation_origin()
            uid = str(bot.user.id)
            uname = bot.user.name
            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            if hasattr(bot.user, 'avatar') and bot.user.avatar:
                avatar = str(getattr(bot.user.avatar, 'url', bot.user.avatar))
            elif hasattr(bot.user, 'display_avatar') and bot.user.display_avatar:
                avatar = str(bot.user.display_avatar.url)

            run_simulation_incident(
                author_id=uid,
                user_name=uname,
                guild_name=g_name,
                guild_id=g_id,
                avatar_url=avatar,
                sample_channels=sample_chans
            )
        except Exception as e:
            tab.toast(type="ERROR", title="Error", description=f"Simulation failed: {e}")
            print(f"[{SCRIPT_NAME}] Error running simulation: {e}", type_="ERROR")

    def handle_save_config():
        try:
            runtime_config["enabled"] = ui_refs['enabled_toggle'].checked
            runtime_config["auto_block"] = ui_refs['auto_block_toggle'].checked
            runtime_config["auto_delete"] = ui_refs['auto_delete_toggle'].checked
            runtime_config["auto_kick"] = ui_refs['auto_kick_toggle'].checked
            runtime_config["auto_ban"] = ui_refs['auto_ban_toggle'].checked

            try:
                runtime_config["min_channels"] = max(1, int(ui_refs['chan_thresh_input'].value))
            except ValueError:
                runtime_config["min_channels"] = 3

            try:
                runtime_config["time_window_seconds"] = max(1, int(ui_refs['time_win_input'].value))
            except ValueError:
                runtime_config["time_window_seconds"] = 15

            save_stored_data()
            update_threat_monitor_ui()
            tab.toast(type="SUCCESS", title="Settings Saved", description="Scam detector settings updated successfully.")
        except Exception as e:
            tab.toast(type="ERROR", title="Error", description=f"Failed to save settings: {e}")
            print(f"[{SCRIPT_NAME}] Error saving settings: {e}", type_="ERROR")

    def handle_reset_defaults():
        try:
            for k, v in DEFAULT_CONFIG.items():
                runtime_config[k] = v

            ui_refs['enabled_toggle'].checked = DEFAULT_CONFIG["enabled"]
            ui_refs['auto_block_toggle'].checked = DEFAULT_CONFIG["auto_block"]
            ui_refs['auto_delete_toggle'].checked = DEFAULT_CONFIG["auto_delete"]
            ui_refs['auto_kick_toggle'].checked = DEFAULT_CONFIG["auto_kick"]
            ui_refs['auto_ban_toggle'].checked = DEFAULT_CONFIG["auto_ban"]
            ui_refs['chan_thresh_input'].value = str(DEFAULT_CONFIG["min_channels"])
            ui_refs['time_win_input'].value = str(DEFAULT_CONFIG["time_window_seconds"])

            save_stored_data()
            update_threat_monitor_ui()
            tab.toast(type="INFO", title="Defaults Restored", description="Scam detector restored to default values.")
        except Exception as e:
            tab.toast(type="ERROR", title="Error", description=f"Failed to reset defaults: {e}")

    def handle_clear_stats():
        try:
            runtime_stats["scanned_messages"] = 0
            runtime_stats["caught_scammers"] = 0
            runtime_stats["deleted_messages"] = 0
            runtime_stats["blocked_users"] = 0
            runtime_stats["kicked_users"] = 0
            runtime_stats["banned_users"] = 0
            runtime_stats["last_incident_time"] = "Never"
            save_stored_data()
            update_threat_monitor_ui()
            tab.toast(type="SUCCESS", title="Stats Cleared", description="Monitoring statistics reset to zero.")
        except Exception as e:
            tab.toast(type="ERROR", title="Error", description=f"Failed to clear stats: {e}")

    def handle_clear_logs():
        nonlocal incident_logs
        try:
            incident_logs = []
            active_user_incident.clear()
            active_incident_expiry.clear()
            flagged_watch_expiry.clear()
            save_stored_data()
            update_incidents_table()
            display_incident_inspector(None)
            update_threat_monitor_ui()
            tab.toast(type="SUCCESS", title="Logs Cleared", description="Incident history wiped clean.")
        except Exception as e:
            tab.toast(type="ERROR", title="Error", description=f"Failed to clear logs: {e}")

    # Wire up button callbacks
    table_sim_btn.onClick = handle_ui_simulation
    table_clear_btn.onClick = handle_clear_logs
    save_config_btn.onClick = handle_save_config
    reset_config_btn.onClick = handle_reset_defaults
    clear_stats_btn.onClick = handle_clear_stats

    # ==================== CHAT COMMANDS ====================
    @bot.command(
        name="scam",
        aliases=["scamdetector", "mrbeastdetector", "antiscam"],
        usage="[toggle | stats | clear | test]",
        description="MrBeast Scam Velocity Detector control and status"
    )
    async def cmd_scam(ctx, *, args: str = ""):
        await ctx.message.delete()
        sub = args.strip().split()[0].lower() if args.strip() else "status"

        if sub == "toggle":
            new_state = not runtime_config.get("enabled", True)
            runtime_config["enabled"] = new_state
            if ui_refs.get('enabled_toggle'):
                ui_refs['enabled_toggle'].checked = new_state
            save_stored_data()
            update_threat_monitor_ui()
            await ctx.send(f"> **Scam Detector:** `{'Enabled' if new_state else 'Disabled'}`", delete_after=delete_after())

        elif sub == "clear":
            nonlocal incident_logs
            incident_logs = []
            active_user_incident.clear()
            active_incident_expiry.clear()
            flagged_watch_expiry.clear()
            runtime_stats["scanned_messages"] = 0
            runtime_stats["caught_scammers"] = 0
            runtime_stats["deleted_messages"] = 0
            runtime_stats["blocked_users"] = 0
            runtime_stats["kicked_users"] = 0
            runtime_stats["banned_users"] = 0
            runtime_stats["last_incident_time"] = "Never"
            save_stored_data()
            update_threat_monitor_ui()
            update_incidents_table()
            display_incident_inspector(None)
            await ctx.send("> **Scam Detector:** Statistics and logs cleared.", delete_after=delete_after())

        elif sub == "test":
            author_id = str(ctx.author.id)
            guild_name = ctx.guild.name if ctx.guild else "Direct Message"
            guild_id = str(ctx.guild.id) if ctx.guild else "DirectMessage"
            user_name = ctx.author.name
            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            if hasattr(ctx.author, 'avatar') and ctx.author.avatar:
                avatar = str(getattr(ctx.author.avatar, 'url', ctx.author.avatar))
            elif hasattr(ctx.author, 'display_avatar') and ctx.author.display_avatar:
                avatar = str(ctx.author.display_avatar.url)
            
            # Use channels from current guild where command is run
            ch_names = ["general", "bot-commands", "media"]
            if ctx.guild and hasattr(ctx.guild, 'text_channels') and ctx.guild.text_channels:
                ch_names = [getattr(ch, 'name', str(ch.id)) for ch in ctx.guild.text_channels[:15]]

            inc_rec, is_updated = run_simulation_incident(
                author_id=author_id,
                user_name=user_name,
                guild_name=guild_name,
                guild_id=guild_id,
                avatar_url=avatar,
                sample_channels=ch_names
            )

            if is_updated:
                await ctx.send(f"> **Scam Detector:** Updated active incident for `{user_name}` (Now `{len(inc_rec['channels'])}` channels in UI).", delete_after=delete_after())
            else:
                await ctx.send(f"> **Scam Detector:** New test incident started in `{guild_name}` (`{len(inc_rec['channels'])}` channels in UI).", delete_after=delete_after())

        else:
            # Default: Status overview
            is_on = runtime_config.get("enabled", True)
            min_c = runtime_config.get("min_channels", 3)
            win_s = runtime_config.get("time_window_seconds", 15)

            lines = [
                f"> **MrBeast Scam Detector — Status**",
                f"> **Running:** `{'Active' if is_on else 'Disabled'}` | **Min Channels:** `{min_c}` ({win_s}s, 4 attachments)",
                f"> **Auto-Block:** `{'Yes' if runtime_config.get('auto_block') else 'No'}` | **Auto-Delete:** `{'Yes' if runtime_config.get('auto_delete') else 'No'}`",
                f"> **Auto-Kick:** `{'Yes' if runtime_config.get('auto_kick') else 'No'}` | **Auto-Ban:** `{'Yes' if runtime_config.get('auto_ban') else 'No'}`",
                f"> **Scanned:** `{runtime_stats.get('scanned_messages', 0):,}` | **Caught:** `{runtime_stats.get('caught_scammers', 0):,}` | **Deleted:** `{runtime_stats.get('deleted_messages', 0):,}`",
                "> ─────────────────────────",
                f"> `<p>scam toggle` — Enable/Disable monitor",
                f"> `<p>scam test` — Trigger dry-run simulation in UI",
                f"> `<p>scam clear` — Clear all logs and statistics"
            ]
            await ctx.send("\n".join(lines), delete_after=delete_after() * 2)

    # ==================== BOOT & INITIALIZATION ====================
    async def auto_clear_expired_threat_status():
        """Periodically cleans expired sessions and restores Armed status and 0 watchlist count."""
        while True:
            await asyncio.sleep(2.0)
            try:
                now_ts = datetime.now().timestamp()
                expired = [uid for uid, exp in list(active_incident_expiry.items()) if now_ts > exp]
                if expired:
                    for uid in expired:
                        active_incident_expiry.pop(uid, None)
                        active_user_incident.pop(uid, None)
                        flagged_watch_expiry.pop(uid, None)
                    update_threat_monitor_ui()
                elif ui_refs.get('monitor_status_text') and "Threat Detected" in getattr(ui_refs['monitor_status_text'], 'content', ''):
                    update_threat_monitor_ui()
            except Exception:
                pass

    safe_create_task(auto_clear_expired_threat_status())

    update_threat_monitor_ui()
    update_incidents_table()
    if incident_logs:
        display_incident_inspector(incident_logs[0])
    else:
        display_incident_inspector(None)

    tab.render()

mrbeast_scam_detector_script()
