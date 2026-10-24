#!/bin/bash

echo "[+] Checking configuration..."
python3 -c '
import json, os
file = "config.json"
if os.path.exists(file):
    with open(file, "r") as f: cfg = json.load(f)
    updated = False
    
    if not cfg.get("token"):
        cfg["token"] = input("Discord Token is missing. Enter your token: ").strip()
        updated = True
    if not cfg.get("prefix"):
        cfg["prefix"] = input("Prefix is missing. Enter your prefix (e.g. .): ").strip()
        updated = True
    if not cfg.get("dash_username"):
        cfg["dash_username"] = input("Dashboard Username is missing. Enter username: ").strip()
        updated = True
    if not cfg.get("dash_hash"):
        pwd = input("Dashboard Password is missing. Enter password: ").strip()
        # Temporarily tag it. The bot will hash this on boot and delete the plaintext.
        cfg["dash_hash"] = f"raw:{pwd}"
        updated = True
        
    if updated:
        with open(file, "w") as f: json.dump(cfg, f, indent=4)
        print("[+] config.json updated.")
else:
    print("[-] config.json not found. The bot may fail to start.")
'

echo "[+] Stopping old PM2 process..."
pm2 stop selfbot_fnxd 2>/dev/null
pm2 delete selfbot_fnxd 2>/dev/null
pm2 save 2>/dev/null

echo "[+] Checking for Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    sudo apt-get update
    sudo apt-get install docker-compose-plugin -y
fi

echo "[+] Building and starting the secure Docker container..."
docker compose up -d --build

echo "[+] Deployment complete. View live logs with: docker logs -f ballzbot"