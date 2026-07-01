#!/usr/bin/env python3
"""
QuickLink Admin - CLI Version
Firebase-powered URL Shortener
GitHub pe upload karke NetHunter mein chalao
"""

import json
import random
import string
import sys
import os
import time
from datetime import datetime

# Firebase REST API use karte hain (browser SDK nahi, CLI ke liye)
try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    print("urllib not found!")
    sys.exit(1)

# ============================================
# 🔥 FIREBASE CONFIG
# ============================================
FIREBASE_DB_URL = "https://url-shoterner-b7f00-default-rtdb.firebaseio.com"
DEFAULT_DOMAIN   = "shot-woad.vercel.app"

# Local history file
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".quicklink_history.json")


# ─────────────────────────────────────────
# Colors (ANSI)
# ─────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"


def cprint(color, text):
    print(f"{color}{text}{C.RESET}")


def banner():
    os.system("clear" if os.name != "nt" else "cls")
    print(f"""
{C.CYAN}{C.BOLD}
  ██████╗ ██╗   ██╗██╗ ██████╗██╗  ██╗██╗     ██╗███╗   ██╗██╗  ██╗
 ██╔═══██╗██║   ██║██║██╔════╝██║ ██╔╝██║     ██║████╗  ██║██║ ██╔╝
 ██║   ██║██║   ██║██║██║     █████╔╝ ██║     ██║██╔██╗ ██║█████╔╝
 ██║▄▄ ██║██║   ██║██║██║     ██╔═██╗ ██║     ██║██║╚██╗██║██╔═██╗
 ╚██████╔╝╚██████╔╝██║╚██████╗██║  ██╗███████╗██║██║ ╚████║██║  ██╗
  ╚══▀▀═╝  ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
{C.RESET}
{C.DIM}           Admin Panel · Firebase Powered · CLI Edition{C.RESET}
""")


# ─────────────────────────────────────────
# Firebase REST helpers
# ─────────────────────────────────────────
def firebase_get(path: str):
    """GET data from Firebase Realtime DB"""
    url = f"{FIREBASE_DB_URL}/{path}.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode()
            return json.loads(data)
    except urllib.error.HTTPError as e:
        raise Exception(f"HTTP {e.code}: {e.reason}")
    except Exception as e:
        raise Exception(str(e))


def firebase_set(path: str, data: dict):
    """PUT data to Firebase Realtime DB"""
    url = f"{FIREBASE_DB_URL}/{path}.json"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="PUT")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise Exception(f"HTTP {e.code}: {e.reason}")
    except Exception as e:
        raise Exception(str(e))


# ─────────────────────────────────────────
# Local History
# ─────────────────────────────────────────
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[:50], f, indent=2)
    except Exception as e:
        cprint(C.RED, f"  History save error: {e}")


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def gen_code(n=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def is_valid_url(url: str) -> bool:
    try:
        result = urllib.parse.urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


def clean_alias(alias: str) -> str:
    return "".join(c for c in alias if c.isalnum() or c in "-_")


# ─────────────────────────────────────────
# Core actions
# ─────────────────────────────────────────
def shorten_url():
    cprint(C.CYAN, "\n  ── Shorten URL ──────────────────────────────")

    long_url = input(f"  {C.YELLOW}Long URL{C.RESET}: ").strip()
    if not long_url:
        cprint(C.RED, "  ⚠ URL daalna zaroori hai!")
        return
    if not is_valid_url(long_url):
        cprint(C.RED, "  ⚠ Invalid URL — https:// se shuru karo")
        return

    alias_raw = input(f"  {C.YELLOW}Custom Alias{C.RESET} (Enter = random): ").strip()
    alias = clean_alias(alias_raw)

    domain_in = input(f"  {C.YELLOW}Domain{C.RESET} (Enter = {DEFAULT_DOMAIN}): ").strip()
    domain = domain_in if domain_in else DEFAULT_DOMAIN

    code = alias if alias else gen_code()
    short_url = f"https://{domain}/?url={code}"

    cprint(C.DIM, "\n  ⏳ Firebase se connect ho raha hoon...")

    # Check duplicate alias
    if alias:
        try:
            existing = firebase_get(f"links/{code}")
            if existing:
                cprint(C.RED, f"  ⚠ Alias \"{alias}\" already exists. Doosra try karo.")
                return
        except Exception as e:
            cprint(C.RED, f"  ⚠ Firebase check error: {e}")
            return

    # Save to Firebase
    entry = {
        "longUrl": long_url,
        "shortUrl": short_url,
        "code": code,
        "domain": domain,
        "createdAt": int(time.time() * 1000)
    }

    try:
        firebase_set(f"links/{code}", entry)
    except Exception as e:
        cprint(C.RED, f"  ⚠ Firebase save failed: {e}")
        return

    # Save locally
    history = load_history()
    history.insert(0, {
        "code": code,
        "shortUrl": short_url,
        "longUrl": long_url,
        "domain": domain,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M")
    })
    save_history(history)

    print(f"""
  {C.GREEN}✓ Saved to Firebase!{C.RESET}
  {C.BOLD}{C.CYAN}{short_url}{C.RESET}
  {C.DIM}→ {long_url[:60]}{"..." if len(long_url)>60 else ""}{C.RESET}
""")


def show_history():
    history = load_history()
    cprint(C.CYAN, "\n  ── Saved Links ──────────────────────────────")
    if not history:
        cprint(C.DIM, "  No links saved yet.")
        return
    for i, h in enumerate(history[:20], 1):
        print(f"  {C.BOLD}{i:02}.{C.RESET} {C.CYAN}{h['shortUrl']}{C.RESET}")
        long_preview = h['longUrl'][:55] + ("..." if len(h['longUrl']) > 55 else "")
        print(f"      {C.DIM}{long_preview}{C.RESET}")
        print(f"      {C.DIM}{h.get('date','')}{C.RESET}\n")


def clear_history():
    confirm = input("  Pura local history delete karna chahte ho? (y/N): ").strip().lower()
    if confirm == "y":
        save_history([])
        cprint(C.GREEN, "  ✓ History cleared.")
    else:
        cprint(C.DIM, "  Cancelled.")


def fetch_link():
    cprint(C.CYAN, "\n  ── Fetch Link from Firebase ──────────────────")
    code = input("  Code/Alias daalo: ").strip()
    if not code:
        cprint(C.RED, "  ⚠ Code daalna zaroori hai!")
        return
    try:
        data = firebase_get(f"links/{code}")
        if not data:
            cprint(C.RED, f"  ⚠ Code \"{code}\" Firebase mein nahi mila.")
            return
        print(f"""
  {C.GREEN}✓ Found!{C.RESET}
  Short  : {C.CYAN}{data.get('shortUrl')}{C.RESET}
  Long   : {C.DIM}{data.get('longUrl')}{C.RESET}
  Domain : {data.get('domain')}
  Created: {datetime.fromtimestamp(data.get('createdAt',0)/1000).strftime('%d/%m/%Y %H:%M')}
""")
    except Exception as e:
        cprint(C.RED, f"  ⚠ Firebase error: {e}")


# ─────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────
def main():
    banner()
    cprint(C.GREEN, f"  ● Firebase DB : {FIREBASE_DB_URL}")
    cprint(C.GREEN, f"  ● Default Domain : {DEFAULT_DOMAIN}\n")

    while True:
        print(f"  {C.BOLD}MENU{C.RESET}")
        print(f"  {C.CYAN}1.{C.RESET} Shorten & Save URL")
        print(f"  {C.CYAN}2.{C.RESET} View History (local)")
        print(f"  {C.CYAN}3.{C.RESET} Fetch Link from Firebase")
        print(f"  {C.CYAN}4.{C.RESET} Clear Local History")
        print(f"  {C.CYAN}0.{C.RESET} Exit")
        print()

        choice = input("  Choice: ").strip()

        if choice == "1":
            shorten_url()
        elif choice == "2":
            show_history()
        elif choice == "3":
            fetch_link()
        elif choice == "4":
            clear_history()
        elif choice == "0":
            cprint(C.DIM, "\n  Bye! 👋\n")
            break
        else:
            cprint(C.RED, "  ⚠ Invalid choice, dobara try karo.")

        input(f"\n  {C.DIM}[Enter dabao menu pe wapas jaane ke liye]{C.RESET}")
        banner()
        cprint(C.GREEN, f"  ● Firebase DB : {FIREBASE_DB_URL}")
        cprint(C.GREEN, f"  ● Default Domain : {DEFAULT_DOMAIN}\n")


if __name__ == "__main__":
    main()
