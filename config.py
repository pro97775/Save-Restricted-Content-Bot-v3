# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

import os
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv
load_dotenv()

# ════════════════════════════════════════════════════════════════════════════════
# ░ CONFIGURATION SETTINGS
# ════════════════════════════════════════════════════════════════════════════════

# VPS --- FILL COOKIES 🍪 in """ ... """ 
INST_COOKIES = """
# write up here insta cookies
"""

YTUB_COOKIES = """
# write here yt cookies
"""

def _parse_int(val: str, default=0):
    val = (val or "").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        try:
            return int(Decimal(val))
        except (InvalidOperation, ValueError):
            return default

def _int_env(key: str, default: int = 0) -> int:
    return _parse_int(os.getenv(key, ""), default)

def _chat_env(key: str, dummy_defaults=()):
    val = (os.getenv(key, "") or "").strip()
    if not val or val.lower() in ("0", "none", "false", "null") or val in dummy_defaults:
        return 0
    parsed = _parse_int(val, None)
    if parsed is not None:
        return 0 if str(parsed) in dummy_defaults else parsed
    if "t.me/" in val:
        val = val.rstrip("/").split("t.me/")[-1]
    return val

# ─── BOT / DATABASE CONFIG ──────────────────────────────────────────────────────
API_ID       = _int_env("API_ID", 0)
API_HASH     = os.getenv("API_HASH", "").strip()
BOT_TOKEN    = os.getenv("BOT_TOKEN", "").strip()
MONGO_DB     = os.getenv("MONGO_DB", "").strip()
DB_NAME      = os.getenv("DB_NAME", "telegram_downloader").strip()

# ─── OWNER / CONTROL SETTINGS ───────────────────────────────────────────────────
OWNER_ID     = [v for x in os.getenv("OWNER_ID", "").split() if (v := _parse_int(x, None)) is not None]
STRING       = (os.getenv("STRING", None) or "").strip() or None  # optional session string
LOG_GROUP    = _chat_env("LOG_GROUP", ("-1001234456",))
FORCE_SUB    = _chat_env("FORCE_SUB", ("-10012345567",))

# ─── SECURITY KEYS ──────────────────────────────────────────────────────────────
MASTER_KEY   = os.getenv("MASTER_KEY", "gK8HzLfT9QpViJcYeB5wRa3DmN7P2xUq")  # session encryption
IV_KEY       = os.getenv("IV_KEY", "s7Yx5CpVmE3F")  # decryption key

# ─── COOKIES HANDLING ───────────────────────────────────────────────────────────
YT_COOKIES   = os.getenv("YT_COOKIES", YTUB_COOKIES)
INSTA_COOKIES = os.getenv("INSTA_COOKIES", INST_COOKIES)

# ─── USAGE LIMITS ───────────────────────────────────────────────────────────────
FREEMIUM_LIMIT = _int_env("FREEMIUM_LIMIT", 0)
PREMIUM_LIMIT  = _int_env("PREMIUM_LIMIT", 500)

# ─── UI / LINKS ─────────────────────────────────────────────────────────────────
JOIN_LINK     = os.getenv("JOIN_LINK", "https://t.me/team_spy_pro")
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "https://t.me/username_of_admin")

# ════════════════════════════════════════════════════════════════════════════════
# ░ PREMIUM PLANS CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

P0 = {
    "d": {
        "s": _int_env("PLAN_D_S", 1),
        "du": _int_env("PLAN_D_DU", 1),
        "u": os.getenv("PLAN_D_U", "days"),
        "l": os.getenv("PLAN_D_L", "Daily"),
    },
    "w": {
        "s": _int_env("PLAN_W_S", 3),
        "du": _int_env("PLAN_W_DU", 1),
        "u": os.getenv("PLAN_W_U", "weeks"),
        "l": os.getenv("PLAN_W_L", "Weekly"),
    },
    "m": {
        "s": _int_env("PLAN_M_S", 5),
        "du": _int_env("PLAN_M_DU", 1),
        "u": os.getenv("PLAN_M_U", "month"),
        "l": os.getenv("PLAN_M_L", "Monthly"),
    },
}

# ════════════════════════════════════════════════════════════════════════════════
# ░ DEVGAGAN
# ════════════════════════════════════════════════════════════════════════════════
