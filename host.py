# -*- coding: utf-8 -*-
"""
Single-file Telegram script hosting bot.

Supported uploads: .py, .js and .zip
Button colors: Telegram Bot API styles "primary" (blue) and "danger" (red)

Required packages:
    pip install -U pyTelegramBotAPI Flask psutil requests pymongo

Bot credentials:
    BOT_TOKEN, OWNER_ID and ADMIN_ID are configured in this file.

Optional environment overrides:
    Replace the placeholder values for BOT_TOKEN, OWNER_ID, ADMIN_ID and
    MONGODB_URI below before running.

Security note:
    Uploaded programs are executable code. Run this bot only inside a dedicated,
    disposable container/VM that contains no personal files or unrelated secrets.
"""

from __future__ import annotations

import atexit
import ast
import hashlib
import html
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import psutil
import requests
import telebot
from flask import Flask
from gridfs import GridFS
from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError
from telebot import types


# ---------------------------------------------------------------------------
# UTF-8 and logging
# ---------------------------------------------------------------------------

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("single_file_hosting_bot")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOKEN = "8910247637:AAGgHYQgKXNo6Sh0FZCP2caCu51vacUgtgY"
OWNER_ID = 8147129409
ADMIN_ID = 123456789
MONGODB_URI = "mongodb+srv://ariyanahamed6281_db_user:AyL27CocVhjq29xt@facebookbot.yr3mjzj.mongodb.net/?appName=FacebookBot"
YOUR_USERNAME = "@Ariyan_Ahamed_Ari"

DEVELOPER_NAME = "Ariyan Ahamed Ari"
DEVELOPER_USERNAME = "@Ariyan_Ahamed_Ari"
DEVELOPER_CHANNEL = "@Ariyan_Earning_Shop"
DEVELOPER_PROFILE_URL = "https://t.me/Ariyan_Ahamed_Ari"
DEVELOPER_CHANNEL_URL = "https://t.me/Ariyan_Earning_Shop"
DEVELOPER_FACEBOOK_URL = "https://www.facebook.com/valobashi.puttul"
DEVELOPER_DEFAULTS: Dict[str, str] = {
    "name": DEVELOPER_NAME,
    "username": DEVELOPER_USERNAME,
    "channel": DEVELOPER_CHANNEL,
    "facebook": DEVELOPER_FACEBOOK_URL,
}

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, "upload_bots")
MONGODB_DB_NAME = "telegram_hosting_bot"

FREE_USER_LIMIT = int(os.environ.get("FREE_USER_LIMIT", "150"))
SUBSCRIBED_USER_LIMIT = int(os.environ.get("SUBSCRIBED_USER_LIMIT", "350"))
ADMIN_LIMIT = int(os.environ.get("ADMIN_LIMIT", "500"))
OWNER_LIMIT = float("inf")

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_ZIP_FILES = int(os.environ.get("MAX_ZIP_FILES", "500"))
MAX_ZIP_EXTRACTED_MB = int(os.environ.get("MAX_ZIP_EXTRACTED_MB", "100"))
MAX_ZIP_EXTRACTED_BYTES = MAX_ZIP_EXTRACTED_MB * 1024 * 1024
MAX_LOG_BYTES = int(os.environ.get("MAX_LOG_MB", "10")) * 1024 * 1024
AUTO_INSTALL_DEPENDENCIES = os.environ.get("AUTO_INSTALL_DEPS", "1") == "1"
SUBSCRIPTION_CHECK_SECONDS = max(
    15, int(os.environ.get("SUBSCRIPTION_CHECK_SECONDS", "30"))
)

os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)

if not TOKEN or TOKEN == "REPLACE_WITH_YOUR_BOT_TOKEN":
    raise RuntimeError(
        "Replace BOT_TOKEN in the Configuration section before running the bot."
    )
if not MONGODB_URI or MONGODB_URI == "REPLACE_WITH_YOUR_MONGODB_URI":
    raise RuntimeError(
        "Replace MONGODB_URI in the Configuration section before running the bot."
    )

bot = telebot.TeleBot(TOKEN, threaded=True)


# ---------------------------------------------------------------------------
# Flask keep-alive endpoint
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.get("/")
def home() -> str:
    return "bot is running...."


def run_flask() -> None:
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


def keep_alive() -> None:
    thread = threading.Thread(target=run_flask, name="keep-alive", daemon=True)
    thread.start()
    logger.info("Flask keep-alive server started.")


# ---------------------------------------------------------------------------
# Telegram colored-button compatibility layer
# ---------------------------------------------------------------------------

PRIMARY = "primary"
DANGER = "danger"


class StyledInlineKeyboardButton(types.InlineKeyboardButton):
    """Adds Bot API `style` even if an older telebot class lacks the argument."""

    def __init__(self, text: str, *, style: str = PRIMARY, **kwargs: Any) -> None:
        if style not in {PRIMARY, DANGER}:
            raise ValueError("Only primary and danger button styles are allowed")
        super().__init__(text=text, **kwargs)
        self._color_style = style

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["style"] = self._color_style
        return data


class StyledKeyboardButton(types.KeyboardButton):
    """Reply-keyboard equivalent of StyledInlineKeyboardButton."""

    def __init__(self, text: str, *, style: str = PRIMARY, **kwargs: Any) -> None:
        if style not in {PRIMARY, DANGER}:
            raise ValueError("Only primary and danger button styles are allowed")
        super().__init__(text=text, **kwargs)
        self._color_style = style

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["style"] = self._color_style
        return data


def ibutton(
    text: str,
    *,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
    style: str = PRIMARY,
) -> StyledInlineKeyboardButton:
    """Create one inline button. Every button must use primary or danger."""
    kwargs: Dict[str, Any] = {}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    return StyledInlineKeyboardButton(text, style=style, **kwargs)


def kbutton(text: str, *, style: str = PRIMARY) -> StyledKeyboardButton:
    return StyledKeyboardButton(text, style=style)


PREMIUM_EMOJI = {
    "menu": "5801171696316583596",       # 📝
    "upload": "5787641625916215347",     # ⬆️
    "files": "5789626613771537810",      # 📌
    "stats": "5787384838411522455",      # 📊
    "settings": "5807614228864962198",   # 👑
    "success": "5787428694322581130",    # ✅
    "warning": "5800696552674561810",    # ⚠️
    "cancel": "5854929766146118183",     # ❌
}


def send_premium_message(chat_id: int, text: str, emoji_key: str, **kwargs: Any) -> Any:
    """Send a message whose leading emoji is rendered from the supplied premium pack."""
    emoji = {
        "menu": "📝",
        "upload": "⬆️",
        "files": "📌",
        "stats": "📊",
        "settings": "👑",
        "success": "✅",
        "warning": "⚠️",
        "cancel": "❌",
    }.get(emoji_key, "✨")
    message_text = text if text.startswith(emoji) else f"{emoji} {text}"
    emoji_length = len(emoji.encode("utf-16-le")) // 2
    kwargs["entities"] = [
        types.MessageEntity(
            type="custom_emoji",
            offset=0,
            length=emoji_length,
            custom_emoji_id=PREMIUM_EMOJI.get(emoji_key, PREMIUM_EMOJI["menu"]),
        )
    ]
    return bot.send_message(chat_id, message_text, **kwargs)


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

ProcessInfo = Dict[str, Any]
bot_scripts: Dict[Tuple[int, str], ProcessInfo] = {}
user_subscriptions: Dict[int, Dict[str, datetime]] = {}
user_files: Dict[int, List[Tuple[str, str]]] = {}
active_users: set[int] = set()
admin_ids: set[int] = {OWNER_ID, ADMIN_ID}
pending_broadcasts: Dict[int, Tuple[int, int]] = {}
pending_scripts: set[Tuple[int, str]] = set()
pending_upload_prompts: Dict[int, Tuple[int, int]] = {}
developer_settings: Dict[str, str] = dict(DEVELOPER_DEFAULTS)
force_join_settings: List[Dict[str, str]] = []
force_join_enabled = False

STATE_LOCK = threading.RLock()
DB_LOCK = threading.RLock()
SHUTDOWN_EVENT = threading.Event()
bot_locked = False


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10_000)
mongo_db = mongo_client[MONGODB_DB_NAME]
mongo_fs = GridFS(mongo_db)
subscriptions_collection = mongo_db["subscriptions"]
files_collection = mongo_db["user_files"]
active_users_collection = mongo_db["active_users"]
admins_collection = mongo_db["admins"]
settings_collection = mongo_db["settings"]


def mongo_check() -> None:
    """Fail early instead of silently running with non-persistent local state."""
    mongo_client.admin.command("ping")


def init_db() -> None:
    with DB_LOCK:
        mongo_check()
        subscriptions_collection.create_index("user_id", unique=True)
        files_collection.create_index(
            [("user_id", ASCENDING), ("file_name", ASCENDING)], unique=True
        )
        active_users_collection.create_index("user_id", unique=True)
        admins_collection.create_index("user_id", unique=True)
        settings_collection.create_index("key", unique=True)
        admins_collection.update_one(
            {"user_id": OWNER_ID}, {"$set": {"user_id": OWNER_ID}}, upsert=True
        )
        if ADMIN_ID != OWNER_ID:
            admins_collection.update_one(
                {"user_id": ADMIN_ID}, {"$set": {"user_id": ADMIN_ID}}, upsert=True
            )


def load_data() -> None:
    global bot_locked, force_join_enabled
    with DB_LOCK, STATE_LOCK:
        mongo_check()
        user_subscriptions.clear()
        user_files.clear()
        active_users.clear()
        developer_settings.clear()
        developer_settings.update(DEVELOPER_DEFAULTS)
        force_join_settings.clear()
        force_join_enabled = False

        for record in subscriptions_collection.find({}):
            try:
                user_subscriptions[int(record["user_id"])] = {
                    "expiry": datetime.fromisoformat(record["expiry"]),
                    "started_at": datetime.fromisoformat(
                        record.get("started_at", record["expiry"])
                    ),
                    "granted_days": int(record.get("granted_days", 0)),
                    "file_limit": max(1, int(record.get("file_limit", SUBSCRIBED_USER_LIMIT))),
                }
            except (TypeError, ValueError):
                logger.warning("Skipping invalid subscription record: %s", record)

        for record in files_collection.find({}, {"user_id": 1, "file_name": 1, "file_type": 1}):
            user_files.setdefault(int(record["user_id"]), []).append(
                (record["file_name"], record["file_type"])
            )

        active_users.update(int(record["user_id"]) for record in active_users_collection.find({}))
        admin_ids.update(int(record["user_id"]) for record in admins_collection.find({}))
        setting = settings_collection.find_one({"key": "bot_locked"})
        bot_locked = bool(setting and setting.get("value") == "1")
        force_join_setting = settings_collection.find_one({"key": "force_join"})
        if force_join_setting and isinstance(force_join_setting.get("value"), str):
            try:
                loaded_force_join = json.loads(force_join_setting["value"])
                # Accept the previous single-button format and migrate it.
                if isinstance(loaded_force_join, dict):
                    loaded_force_join = [loaded_force_join]
                if isinstance(loaded_force_join, list):
                    for item in loaded_force_join:
                        if (
                            isinstance(item, dict)
                            and item.get("name")
                            and item.get("url")
                            and item.get("chat")
                        ):
                            force_join_settings.append(
                                {
                                    "name": str(item["name"]),
                                    "url": str(item["url"]),
                                    "chat": str(item["chat"]),
                                }
                            )
                enabled_setting = settings_collection.find_one(
                    {"key": "force_join_enabled"}
                )
                force_join_enabled = bool(
                    enabled_setting is None
                    or enabled_setting.get("value") == "1"
                )
            except (TypeError, ValueError, json.JSONDecodeError):
                logger.warning("Ignoring invalid force-join setting")
        for field in DEVELOPER_DEFAULTS:
            setting = settings_collection.find_one({"key": f"developer_{field}"})
            if setting and str(setting.get("value", "")).strip():
                developer_settings[field] = str(setting["value"]).strip()
    logger.info(
        "Loaded %s users, %s subscriptions, %s admins and %s file records.",
        len(active_users),
        len(user_subscriptions),
        len(admin_ids),
        sum(len(items) for items in user_files.values()),
    )


def save_setting(key: str, value: str) -> None:
    with DB_LOCK:
        settings_collection.update_one(
            {"key": key}, {"$set": {"key": key, "value": value}}, upsert=True
        )


def save_developer_setting(field: str, value: str) -> None:
    if field not in DEVELOPER_DEFAULTS:
        raise ValueError("Unknown developer setting")
    save_setting(f"developer_{field}", value)
    with STATE_LOCK:
        developer_settings[field] = value


def reset_developer_settings() -> None:
    with DB_LOCK:
        for field, value in DEVELOPER_DEFAULTS.items():
            settings_collection.update_one(
                {"key": f"developer_{field}"},
                {"$set": {"key": f"developer_{field}", "value": value}},
                upsert=True,
            )
    with STATE_LOCK:
        developer_settings.clear()
        developer_settings.update(DEVELOPER_DEFAULTS)


def add_active_user(user_id: int) -> None:
    with STATE_LOCK:
        active_users.add(user_id)
    with DB_LOCK:
        active_users_collection.update_one(
            {"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
        )


def save_user_file(user_id: int, file_name: str, file_type: str) -> None:
    with DB_LOCK:
        files_collection.update_one(
            {"user_id": user_id, "file_name": file_name},
            {"$set": {"user_id": user_id, "file_name": file_name, "file_type": file_type}},
            upsert=True,
        )
    with STATE_LOCK:
        items = [item for item in user_files.get(user_id, []) if item[0] != file_name]
        items.append((file_name, file_type))
        user_files[user_id] = items


def remove_user_file_db(user_id: int, file_name: str) -> None:
    with DB_LOCK:
        files_collection.delete_one({"user_id": user_id, "file_name": file_name})
    with STATE_LOCK:
        remaining = [item for item in user_files.get(user_id, []) if item[0] != file_name]
        if remaining:
            user_files[user_id] = remaining
        else:
            user_files.pop(user_id, None)


def save_subscription(
    user_id: int,
    expiry: datetime,
    started_at: Optional[datetime] = None,
    granted_days: int = 0,
    file_limit: int = SUBSCRIBED_USER_LIMIT,
) -> None:
    started_at = started_at or datetime.now()
    with DB_LOCK:
        subscriptions_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "expiry": expiry.isoformat(),
                    "started_at": started_at.isoformat(),
                    "granted_days": granted_days,
                    "file_limit": file_limit,
                }
            },
            upsert=True,
        )
    with STATE_LOCK:
        user_subscriptions[user_id] = {
            "expiry": expiry,
            "started_at": started_at,
            "granted_days": granted_days,
            "file_limit": file_limit,
        }


def remove_subscription_db(user_id: int) -> None:
    with DB_LOCK:
        subscriptions_collection.delete_one({"user_id": user_id})
    with STATE_LOCK:
        user_subscriptions.pop(user_id, None)


def add_admin_db(user_id: int) -> None:
    with DB_LOCK:
        admins_collection.update_one(
            {"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
        )
    with STATE_LOCK:
        admin_ids.add(user_id)


def remove_admin_db(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return False
    with DB_LOCK:
        removed = admins_collection.delete_one({"user_id": user_id}).deleted_count > 0
    if removed:
        with STATE_LOCK:
            admin_ids.discard(user_id)
    return removed


def persist_local_file(user_id: int, path: str) -> None:
    """Store uploaded files and runtime logs in MongoDB GridFS."""
    if not os.path.isfile(path):
        return
    folder = Path(get_user_folder(user_id)).resolve()
    file_path = Path(path).resolve()
    try:
        relative_path = file_path.relative_to(folder).as_posix()
    except ValueError:
        return
    if relative_path.startswith(".pydeps/"):
        return
    with open(file_path, "rb") as source:
        payload = source.read()
    metadata = {"owner_id": user_id, "logical_path": relative_path}
    with DB_LOCK:
        for old_file in mongo_fs.find({"owner_id": user_id, "logical_path": relative_path}):
            mongo_fs.delete(old_file._id)
        mongo_fs.put(
            payload,
            filename=relative_path,
            owner_id=user_id,
            logical_path=relative_path,
            content_type="text/plain" if relative_path.endswith((".py", ".js", ".log", ".txt")) else "application/octet-stream",
        )


def persist_user_folder(user_id: int) -> None:
    folder = Path(get_user_folder(user_id))
    for path in folder.rglob("*"):
        if path.is_file():
            persist_local_file(user_id, str(path))


def remove_persisted_file(user_id: int, relative_path: str) -> None:
    with DB_LOCK:
        for stored_file in mongo_fs.find(
            {"owner_id": user_id, "logical_path": relative_path}
        ):
            mongo_fs.delete(stored_file._id)


def restore_files_from_mongodb() -> None:
    """Recreate the local execution folders from GridFS after a restart."""
    restored = 0
    for stored_file in mongo_fs.find({}):
        try:
            owner_id = int(stored_file.owner_id)
            relative_path = str(stored_file.logical_path)
            if relative_path.startswith("/") or ".." in Path(relative_path).parts:
                logger.warning("Skipping unsafe stored path: %s", relative_path)
                continue
            destination_root = Path(get_user_folder(owner_id)).resolve()
            destination = (destination_root / relative_path).resolve()
            destination.relative_to(destination_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "wb") as output:
                output.write(stored_file.read())
            restored += 1
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.warning("Could not restore a GridFS file: %s", exc)
    logger.info("Restored %s file(s) from MongoDB GridFS.", restored)


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------


def get_user_folder(user_id: int) -> str:
    folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder


init_db()
restore_files_from_mongodb()
load_data()


def get_user_file_limit(user_id: int) -> float:
    if user_id == OWNER_ID:
        return OWNER_LIMIT
    if user_id in admin_ids:
        return float(ADMIN_LIMIT)
    subscription = user_subscriptions.get(user_id)
    if subscription and subscription.get("expiry", datetime.min) > datetime.now():
        return float(subscription.get("file_limit", SUBSCRIBED_USER_LIMIT))
    return float(FREE_USER_LIMIT)


def get_user_file_count(user_id: int) -> int:
    return len(user_files.get(user_id, []))


def has_active_subscription(user_id: int) -> bool:
    """Return whether this account may run hosted scripts."""
    if user_id == OWNER_ID or user_id in admin_ids:
        return True
    with STATE_LOCK:
        expiry = user_subscriptions.get(user_id, {}).get("expiry")
    return bool(expiry and expiry > datetime.now())


def subscription_summary(user_id: int) -> str:
    if user_id == OWNER_ID or user_id in admin_ids:
        return "Administrator access"
    with STATE_LOCK:
        expiry = user_subscriptions.get(user_id, {}).get("expiry")
    if expiry and expiry > datetime.now():
        return f"Active until {expiry:%Y-%m-%d %H:%M}"
    if expiry:
        return f"Expired on {expiry:%Y-%m-%d %H:%M}"
    return "Not active"


def user_subscription_details(user_id: int) -> str:
    """Return the complete permission status shown to a regular user."""
    with STATE_LOCK:
        subscription = dict(user_subscriptions.get(user_id, {}))
    expiry = subscription.get("expiry")
    if not expiry:
        return (
            "🔒 <b>No hosting permission</b>\n\n"
            "Bot host করতে হলে Admin-এর কাছ থেকে permission নিতে হবে.\n\n"
            f"👤 Admin: <b>{DEVELOPER_USERNAME}</b>"
        )

    started_at = subscription.get("started_at")
    granted_days = int(subscription.get("granted_days", 0) or 0)
    file_limit = int(subscription.get("file_limit", SUBSCRIBED_USER_LIMIT) or SUBSCRIBED_USER_LIMIT)
    now = datetime.now()
    if expiry > now:
        seconds_left = max(0, int((expiry - now).total_seconds()))
        days_left = seconds_left // 86400
        hours_left = (seconds_left % 86400) // 3600
        started_text = (
            started_at.strftime("%Y-%m-%d %H:%M") if started_at else "Unknown"
        )
        return (
            "✅ <b>Hosting permission active</b>\n\n"
            f"📅 Permission নেওয়া হয়েছে: {started_text}\n"
            f"⏳ মোট সময়: {granted_days or 'Unknown'} দিন\n"
            f"⌛ বাকি আছে: {days_left} দিন {hours_left} ঘণ্টা\n"
            f"⏰ শেষ হবে: {expiry:%Y-%m-%d %H:%M}\n\n"
            f"📁 File limit: {file_limit}\n\n"
            f"👤 Admin: <b>{DEVELOPER_USERNAME}</b>"
        )
    return (
        "❌ <b>Hosting permission expired</b>\n\n"
        f"⏰ Expired: {expiry:%Y-%m-%d %H:%M}\n"
        f"📅 মোট permission: {granted_days or 'Unknown'} দিন\n\n"
        f"📁 File limit: {file_limit}\n\n"
        f"👤 Admin: <b>{DEVELOPER_USERNAME}</b>"
    )


def subscription_required_text() -> str:
    return (
        "🔒 Hosting permission is required.\n"
        "Please get permission from an administrator before hosting a bot.\n"
        "Your uploaded file will remain saved."
    )


def safe_filename(raw_name: str) -> str:
    """Return a traversal-safe, Telegram-friendly filename."""
    normalized = str(raw_name or "").replace("\\", "/")
    name = os.path.basename(normalized).strip().replace("\x00", "")
    name = re.sub(r"[\r\n\t]", "_", name)
    if not name or name in {".", ".."}:
        raise ValueError("Invalid filename")
    if len(name.encode("utf-8")) > 180:
        stem, extension = os.path.splitext(name)
        name = stem[:100] + extension[:20]
    return name


def file_ref(file_name: str) -> str:
    return hashlib.sha256(file_name.encode("utf-8")).hexdigest()[:16]


def dynamic_file_callback(action: str, user_id: int, file_name: str) -> str:
    return f"f|{action}|{user_id}|{file_ref(file_name)}"


def resolve_user_file(user_id: int, reference: str) -> Optional[Tuple[str, str]]:
    for file_name, file_type in user_files.get(user_id, []):
        if file_ref(file_name) == reference:
            return file_name, file_type
    return None


def resolve_log_file(user_id: int, reference: str) -> Optional[str]:
    folder = get_user_folder(user_id)
    try:
        for name in os.listdir(folder):
            if name.endswith(".log") and file_ref(name) == reference:
                return name
    except OSError:
        return None
    return None


def normalize_channel_url(channel: str) -> str:
    value = channel.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://t.me/{value.lstrip('@')}"


def current_developer_settings() -> Dict[str, str]:
    with STATE_LOCK:
        return dict(developer_settings)


def telegram_handle_url(handle: str) -> str:
    return f"https://t.me/{handle.strip().lstrip('@')}"


def force_join_target_from_url(url: str) -> Optional[str]:
    """Extract a public username for Telegram's membership API."""
    parsed = urlparse(url)
    if parsed.netloc.lower() not in {"t.me", "www.t.me", "telegram.me"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if not parts or parts[0].startswith(("+", "joinchat")):
        return None
    username = parts[0].split("?", 1)[0]
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
        return None
    return f"@{username}"


def force_join_markup() -> Optional[types.InlineKeyboardMarkup]:
    if not force_join_settings or not force_join_enabled:
        return None
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in force_join_settings:
        markup.add(
            ibutton(
                item["name"],
                url=item["url"],
                style=PRIMARY,
            )
        )
    markup.add(ibutton("✅ I Joined", callback_data="force_join_check", style=PRIMARY))
    return markup


def user_has_joined_force_channel(user_id: int) -> bool:
    if not force_join_settings or not force_join_enabled:
        return True
    for item in force_join_settings:
        try:
            member = bot.get_chat_member(item["chat"], user_id)
            if member.status in {"left", "kicked"}:
                return False
        except Exception as exc:
            logger.warning("Force-join membership check failed: %s", exc)
            # Fail closed if the bot cannot check a configured channel.
            return False
    return True


def require_force_join(chat_id: int, user_id: int) -> bool:
    if user_id in admin_ids or not force_join_settings:
        return True
    if user_has_joined_force_channel(user_id):
        return True
    bot.send_message(
        chat_id,
        "🔒 আগে নিচের channel/group-এ join করুন, তারপর ✅ I Joined চাপুন।",
        reply_markup=force_join_markup(),
    )
    return False


def normalize_telegram_handle(raw_value: str, label: str) -> str:
    value = raw_value.strip()
    value = re.sub(
        r"^https?://(?:www\.)?t\.me/",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = value.split("?", 1)[0].strip().strip("/@")
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", value):
        raise ValueError(
            f"{label} must be a valid Telegram @username (5-32 letters, numbers or _)."
        )
    return f"@{value}"


def normalize_developer_setting(field: str, raw_value: str) -> str:
    value = raw_value.strip()
    if field == "name":
        value = " ".join(value.split())
        if not 2 <= len(value) <= 80:
            raise ValueError("Name must contain 2-80 characters.")
        return value
    if field == "username":
        return normalize_telegram_handle(value, "Username")
    if field == "channel":
        return normalize_telegram_handle(value, "Channel")
    if field == "facebook":
        if not value.lower().startswith(("http://", "https://")):
            value = "https://" + value.lstrip("/")
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"} or not host:
            raise ValueError("Send a valid Facebook profile/page URL.")
        if not (
            host == "facebook.com"
            or host.endswith(".facebook.com")
            or host == "fb.com"
            or host.endswith(".fb.com")
        ):
            raise ValueError("Only a Facebook URL is accepted here.")
        if len(value) > 500 or any(character.isspace() for character in value):
            raise ValueError("Facebook URL is too long or contains spaces.")
        return value
    raise ValueError("Unknown developer setting.")


def limit_text(text: str, maximum: int = 3900) -> str:
    if len(text) <= maximum:
        return text
    return text[: maximum - 30] + "\n... (truncated)"


def notify_chat(message_or_call: Any, text: str, **kwargs: Any) -> Any:
    if isinstance(message_or_call, telebot.types.CallbackQuery):
        chat_id = message_or_call.message.chat.id
    else:
        chat_id = message_or_call.chat.id
    return bot.send_message(chat_id, text, **kwargs)


def user_status(user_id: int) -> Tuple[str, str]:
    if user_id == OWNER_ID:
        return "🤍 Owner", ""
    if user_id in admin_ids:
        return "🌙 Admin", ""
    subscription = user_subscriptions.get(user_id)
    if subscription:
        expiry = subscription.get("expiry")
        if expiry and expiry > datetime.now():
            seconds_left = max(0, int((expiry - datetime.now()).total_seconds()))
            days_left = (seconds_left + 86399) // 86400
            return "⭐ Premium", f"\n⏳ Subscription: {days_left} day(s) left"
        if expiry:
            return "🔒 No Subscription", f"\n⌛ Expired: {expiry:%Y-%m-%d %H:%M}"
    return "🔒 No Subscription", "\nℹ️ Admin permission is required to run scripts"


def display_limit(limit: float) -> str:
    return "Unlimited" if limit == float("inf") else str(int(limit))


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


def ensure_access(user_id: int, chat_id: int) -> bool:
    if not require_force_join(chat_id, user_id):
        return False
    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ Bot is locked by an administrator. Try later.")
        return False
    return True


# ---------------------------------------------------------------------------
# File checks and safe ZIP extraction
# ---------------------------------------------------------------------------

EXECUTABLE_SIGNATURES: Sequence[Tuple[bytes, str]] = (
    (b"MZ", "Windows executable"),
    (b"\x7fELF", "Linux executable"),
    (b"\xfe\xed\xfa", "Mach-O executable"),
    (b"\xce\xfa\xed\xfe", "Mach-O executable"),
)

BLOCKED_EXTENSIONS = {
    ".exe", ".dll", ".bat", ".cmd", ".scr", ".com", ".pif", ".msi",
    ".msp", ".hta", ".cpl", ".jar", ".bin", ".deb", ".rpm", ".apk",
    ".app", ".dmg", ".iso", ".img", ".so", ".dylib",
}


def scan_regular_file(content: bytes, file_name: str) -> Tuple[bool, str]:
    extension = os.path.splitext(file_name)[1].lower()
    if extension in BLOCKED_EXTENSIONS:
        return False, f"Blocked executable extension: {extension}"
    for signature, label in EXECUTABLE_SIGNATURES:
        if content.startswith(signature):
            return False, f"Blocked binary content: {label}"
    if b"\x00" in content[:4096] and extension in {".py", ".js", ".json", ".txt"}:
        return False, "The source file appears to contain binary data"
    return True, "File passed basic checks"


def safe_extract_zip(zip_path: str, destination: str) -> List[str]:
    """Extract a ZIP without traversal, symlinks, encryption or zip bombs."""
    destination_path = Path(destination).resolve()
    extracted: List[str] = []
    total_size = 0

    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.infolist()
        if len(members) > MAX_ZIP_FILES:
            raise ValueError(f"ZIP has more than {MAX_ZIP_FILES} entries")

        for member in members:
            if member.flag_bits & 0x1:
                raise ValueError(f"Encrypted ZIP entry is not allowed: {member.filename}")

            normalized = member.filename.replace("\\", "/")
            if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
                raise ValueError(f"Unsafe absolute ZIP path: {member.filename}")

            target = (destination_path / normalized).resolve()
            try:
                target.relative_to(destination_path)
            except ValueError as exc:
                raise ValueError(f"Unsafe ZIP path: {member.filename}") from exc

            # Unix symlink bit inside external_attr.
            mode = (member.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"ZIP symlink is not allowed: {member.filename}")

            extension = os.path.splitext(normalized)[1].lower()
            if extension in BLOCKED_EXTENSIONS:
                raise ValueError(f"ZIP contains blocked file: {member.filename}")

            total_size += max(0, member.file_size)
            if total_size > MAX_ZIP_EXTRACTED_BYTES:
                raise ValueError(
                    f"Extracted ZIP is larger than {MAX_ZIP_EXTRACTED_MB} MB"
                )

        for member in members:
            normalized = member.filename.replace("\\", "/")
            target = (destination_path / normalized).resolve()
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, open(target, "wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            extracted.append(str(target))

    return extracted


def find_project_root_and_main(temp_dir: str) -> Tuple[str, str, str]:
    ignored = {"__MACOSX", ".git", "node_modules", "__pycache__"}
    candidates: List[Tuple[int, str, str]] = []
    preferred = {
        "main.py": 0,
        "bot.py": 1,
        "app.py": 2,
        "index.js": 3,
        "main.js": 4,
        "bot.js": 5,
        "app.js": 6,
    }

    for root, directories, files in os.walk(temp_dir):
        directories[:] = [
            name
            for name in directories
            if name not in ignored and not name.startswith(".")
        ]
        for name in files:
            extension = os.path.splitext(name)[1].lower()
            if extension not in {".py", ".js"}:
                continue
            rank = preferred.get(name.lower(), 100)
            candidates.append((rank, root, name))

    if not candidates:
        raise ValueError("No .py or .js script was found in the ZIP")
    _, project_root, main_name = sorted(candidates, key=lambda item: (item[0], item[2]))[0]
    file_type = "py" if main_name.lower().endswith(".py") else "js"
    return project_root, main_name, file_type


# ---------------------------------------------------------------------------
# Dependency installation
# ---------------------------------------------------------------------------

PYTHON_PACKAGE_MAP: Dict[str, Optional[str]] = {
    "telebot": "pyTelegramBotAPI",
    "telegram": "python-telegram-bot",
    "aiogram": "aiogram",
    "pyrogram": "pyrogram",
    "telethon": "telethon",
    "telepot": "telepot",
    "tgcrypto": "tgcrypto",
    "bs4": "beautifulsoup4",
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "yaml": "PyYAML",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
    "pandas": "pandas",
    "numpy": "numpy",
    "flask": "Flask",
    "django": "Django",
    "sqlalchemy": "SQLAlchemy",
    "psutil": "psutil",
    "requests": "requests",
}

NODE_CORE_MODULES = {
    "assert", "buffer", "child_process", "cluster", "console", "crypto", "dgram",
    "dns", "events", "fs", "http", "http2", "https", "module", "net", "os",
    "path", "perf_hooks", "process", "querystring", "readline", "stream",
    "string_decoder", "timers", "tls", "tty", "url", "util", "v8", "vm",
    "worker_threads", "zlib",
}


def run_install_command(
    command: Sequence[str],
    cwd: str,
    message: Any,
    description: str,
) -> bool:
    notify_chat(message, f"⏳ Installing {description}...")
    try:
        result = subprocess.run(
            list(command),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            check=False,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except FileNotFoundError:
        notify_chat(message, f"❌ Installer command was not found for {description}.")
        return False
    except subprocess.TimeoutExpired:
        notify_chat(message, f"❌ Installation timed out for {description}.")
        return False
    except Exception as exc:
        logger.exception("Dependency installation failed")
        notify_chat(message, f"❌ Installation error: {exc}")
        return False

    if result.returncode == 0:
        notify_chat(message, f"✅ Installed {description}.")
        return True

    error = limit_text(result.stderr or result.stdout or "Unknown installer error", 3000)
    notify_chat(message, f"❌ Could not install {description}:\n{error}")
    return False


def python_dependency_dir(user_folder: str) -> str:
    directory = os.path.join(user_folder, ".pydeps")
    os.makedirs(directory, exist_ok=True)
    return directory


def import_exists(module_name: str, user_folder: str) -> bool:
    local_module = os.path.join(user_folder, module_name + ".py")
    local_package = os.path.join(user_folder, module_name, "__init__.py")
    dependency_module = os.path.join(python_dependency_dir(user_folder), module_name)
    if os.path.exists(local_module) or os.path.exists(local_package) or os.path.exists(dependency_module):
        return True
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def discover_python_imports(script_path: str) -> List[str]:
    try:
        source = Path(script_path).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=script_path)
    except (OSError, SyntaxError):
        return []
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".", 1)[0])
    return sorted(modules)


def install_python_dependencies(script_path: str, user_folder: str, message: Any) -> bool:
    if not AUTO_INSTALL_DEPENDENCIES:
        return True
    dependency_dir = python_dependency_dir(user_folder)
    requirements = os.path.join(user_folder, "requirements.txt")
    if os.path.isfile(requirements):
        if not run_install_command(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--target",
                dependency_dir,
                "-r",
                requirements,
            ],
            user_folder,
            message,
            "requirements.txt packages",
        ):
            return False
    for module_name in discover_python_imports(script_path):
        if module_name in getattr(sys, "stdlib_module_names", set()):
            continue
        if import_exists(module_name, user_folder):
            continue
        package = PYTHON_PACKAGE_MAP.get(module_name, module_name)
        if package is None:
            continue
        ok = run_install_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--target", dependency_dir, package],
            user_folder,
            message,
            f"Python package {package}",
        )
        if not ok:
            return False
    return True


def discover_node_modules(script_path: str) -> List[str]:
    try:
        source = Path(script_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    found = re.findall(
        r"(?:require\s*\(\s*|from\s+|import\s*\(\s*)['\"]([^'\"]+)['\"]",
        source,
    )
    modules: set[str] = set()
    for name in found:
        if name.startswith((".", "/", "node:")):
            continue
        if name.startswith("@"):
            parts = name.split("/")
            package = "/".join(parts[:2])
        else:
            package = name.split("/", 1)[0]
        if package not in NODE_CORE_MODULES:
            modules.add(package)
    return sorted(modules)


def install_node_dependencies(script_path: str, user_folder: str, message: Any) -> bool:
    if not AUTO_INSTALL_DEPENDENCIES:
        return True
    package_json = os.path.join(user_folder, "package.json")
    if os.path.exists(package_json):
        return run_install_command(
            ["npm", "install", "--no-audit", "--no-fund"],
            user_folder,
            message,
            "Node.js dependencies",
        )
    for module_name in discover_node_modules(script_path):
        module_path = os.path.join(user_folder, "node_modules", *module_name.split("/"))
        if os.path.exists(module_path):
            continue
        if not run_install_command(
            ["npm", "install", "--no-audit", "--no-fund", module_name],
            user_folder,
            message,
            f"Node package {module_name}",
        ):
            return False
    return True


def install_project_manifest_dependencies(project_root: str, message: Any) -> bool:
    if not AUTO_INSTALL_DEPENDENCIES:
        return True
    requirements = os.path.join(project_root, "requirements.txt")
    if os.path.exists(requirements):
        dependency_dir = python_dependency_dir(project_root)
        if not run_install_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--target", dependency_dir, "-r", requirements],
            project_root,
            message,
            "requirements.txt packages",
        ):
            return False
    package_json = os.path.join(project_root, "package.json")
    if os.path.exists(package_json):
        if not run_install_command(
            ["npm", "install", "--no-audit", "--no-fund"],
            project_root,
            message,
            "package.json dependencies",
        ):
            return False
    return True


# ---------------------------------------------------------------------------
# Managed process runner
# ---------------------------------------------------------------------------


def process_key(user_id: int, file_name: str) -> Tuple[int, str]:
    return user_id, file_name


def is_bot_running(user_id: int, file_name: str) -> bool:
    key = process_key(user_id, file_name)
    with STATE_LOCK:
        info = bot_scripts.get(key)
    if not info:
        return False
    process = info.get("process")
    if not process or process.poll() is not None:
        with STATE_LOCK:
            current = bot_scripts.get(key)
            if current is info:
                bot_scripts.pop(key, None)
        log_handle = info.get("log_file")
        if log_handle and not log_handle.closed:
            try:
                log_handle.close()
            except OSError:
                pass
        return False
    try:
        ps_process = psutil.Process(process.pid)
        return ps_process.is_running() and ps_process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False
    except Exception as exc:
        logger.warning("Could not inspect process %s: %s", process.pid, exc)
        return process.poll() is None


def rotate_log_if_needed(log_path: str) -> None:
    try:
        if not os.path.exists(log_path) or os.path.getsize(log_path) <= MAX_LOG_BYTES:
            return
        keep_bytes = max(1024, MAX_LOG_BYTES // 2)
        with open(log_path, "rb") as source:
            source.seek(-keep_bytes, os.SEEK_END)
            tail = source.read()
        with open(log_path, "wb") as output:
            output.write(b"[Older log content was trimmed]\n")
            output.write(tail)
    except OSError as exc:
        logger.warning("Could not rotate log %s: %s", log_path, exc)


def child_environment(user_folder: str) -> Dict[str, str]:
    environment = dict(os.environ)
    # Never expose this hosting bot's Telegram token to an uploaded child process.
    environment.pop("BOT_TOKEN", None)
    # Child web apps must not steal the keep-alive server's assigned port.
    environment.pop("PORT", None)
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUNBUFFERED"] = "1"
    environment["HOSTED_BY_TELEGRAM_BOT"] = "1"
    dependency_dir = python_dependency_dir(user_folder)
    python_path_parts = [user_folder, dependency_dir]
    existing_python_path = environment.get("PYTHONPATH")
    if existing_python_path:
        python_path_parts.append(existing_python_path)
    environment["PYTHONPATH"] = os.pathsep.join(python_path_parts)
    return environment


def kill_process_tree(info: ProcessInfo) -> None:
    process = info.get("process")
    if not process:
        return
    pid = getattr(process, "pid", None)
    if pid:
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(children, timeout=2)
            for child in alive:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except psutil.TimeoutExpired:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
        except psutil.NoSuchProcess:
            pass
        except Exception as exc:
            logger.exception("Could not stop process tree %s: %s", pid, exc)
            try:
                process.kill()
            except Exception:
                pass

    log_handle = info.get("log_file")
    if log_handle and not log_handle.closed:
        try:
            log_handle.close()
        except OSError:
            pass


def monitor_managed_process(key: Tuple[int, str], info: ProcessInfo) -> None:
    process = info["process"]
    try:
        return_code = process.wait()
    except Exception as exc:
        logger.warning("Process monitor failed for %s: %s", key, exc)
        return_code = None

    log_handle = info.get("log_file")
    if log_handle and not log_handle.closed:
        try:
            log_handle.flush()
            log_handle.close()
        except OSError:
            pass

    try:
        persist_user_folder(int(info["script_owner_id"]))
    except Exception:
        logger.exception("Could not persist runtime data for %s", key)

    with STATE_LOCK:
        if bot_scripts.get(key) is info:
            bot_scripts.pop(key, None)
    logger.info("Managed script %s exited with code %s", key, return_code)


def validate_python_syntax(script_path: str) -> Optional[str]:
    try:
        source = Path(script_path).read_text(encoding="utf-8", errors="replace")
        compile(source, script_path, "exec")
        return None
    except SyntaxError as exc:
        return f"Line {exc.lineno}: {exc.msg}"
    except OSError as exc:
        return str(exc)


def validate_javascript_syntax(script_path: str, cwd: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["node", "--check", script_path],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        return "Node.js is not installed on this server"
    except subprocess.TimeoutExpired:
        return "JavaScript syntax check timed out"
    if result.returncode != 0:
        return limit_text(result.stderr or result.stdout or "JavaScript syntax error", 1500)
    return None


def start_managed_script(
    script_path: str,
    user_id: int,
    user_folder: str,
    file_name: str,
    file_type: str,
    message: Any,
) -> bool:
    key = process_key(user_id, file_name)
    if not has_active_subscription(user_id):
        notify_chat(message, subscription_required_text())
        return False
    if is_bot_running(user_id, file_name):
        notify_chat(message, f"⚠️ {file_name} is already running.")
        return False
    run_limit = get_user_file_limit(user_id)
    with STATE_LOCK:
        running_count = sum(1 for owner_id, _ in bot_scripts if owner_id == user_id)
    if running_count >= run_limit:
        notify_chat(
            message,
            f"⚠️ Running file limit reached "
            f"({running_count}/{display_limit(run_limit)}). Stop a file first.",
        )
        return False
    if not os.path.isfile(script_path):
        remove_user_file_db(user_id, file_name)
        notify_chat(message, f"❌ Script not found: {file_name}")
        return False

    if file_type == "py":
        syntax_error = validate_python_syntax(script_path)
        if syntax_error:
            notify_chat(message, f"❌ Python syntax error in {file_name}:\n{syntax_error}")
            return False
        if not install_python_dependencies(script_path, user_folder, message):
            return False
        command = [sys.executable, script_path]
    elif file_type == "js":
        syntax_error = validate_javascript_syntax(script_path, user_folder)
        if syntax_error:
            notify_chat(message, f"❌ JavaScript check failed for {file_name}:\n{syntax_error}")
            return False
        if not install_node_dependencies(script_path, user_folder, message):
            return False
        command = ["node", script_path]
    else:
        notify_chat(message, f"❌ Unsupported script type: {file_type}")
        return False

    # Recheck after dependency installation. An admin may have removed or allowed
    # the subscription while the installer was working.
    if not has_active_subscription(user_id):
        notify_chat(message, "🔒 Subscription is no longer active. Script was not started.")
        return False

    log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
    rotate_log_if_needed(log_path)
    log_handle = None
    try:
        log_handle = open(log_path, "a", encoding="utf-8", errors="replace")
        log_handle.write(
            f"\n\n===== Started {datetime.now().isoformat(timespec='seconds')} =====\n"
        )
        log_handle.flush()

        startupinfo = None
        creationflags = 0
        popen_kwargs: Dict[str, Any] = {}
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            popen_kwargs["start_new_session"] = True

        process = subprocess.Popen(
            command,
            cwd=user_folder,
            stdout=log_handle,
            stderr=log_handle,
            stdin=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_environment(user_folder),
            startupinfo=startupinfo,
            creationflags=creationflags,
            **popen_kwargs,
        )
        info: ProcessInfo = {
            "process": process,
            "log_file": log_handle,
            "log_path": log_path,
            "file_name": file_name,
            "file_type": file_type,
            "script_owner_id": user_id,
            "user_folder": user_folder,
            "start_time": datetime.now(),
        }
        with STATE_LOCK:
            bot_scripts[key] = info
        threading.Thread(
            target=monitor_managed_process,
            args=(key, info),
            name=f"monitor-{user_id}-{file_ref(file_name)}",
            daemon=True,
        ).start()
        notify_chat(message, f"✅ {file_name} started.\n🆔 PID: {process.pid}")
        return True
    except FileNotFoundError as exc:
        if log_handle and not log_handle.closed:
            log_handle.close()
        notify_chat(message, f"❌ Runtime not installed: {exc}")
        return False
    except Exception as exc:
        if log_handle and not log_handle.closed:
            log_handle.close()
        logger.exception("Could not start %s", key)
        notify_chat(message, f"❌ Could not start {file_name}: {exc}")
        return False


def run_script(
    script_path: str,
    script_owner_id: int,
    user_folder: str,
    file_name: str,
    message: Any,
) -> None:
    start_managed_script(
        script_path, script_owner_id, user_folder, file_name, "py", message
    )


def run_js_script(
    script_path: str,
    script_owner_id: int,
    user_folder: str,
    file_name: str,
    message: Any,
) -> None:
    start_managed_script(
        script_path, script_owner_id, user_folder, file_name, "js", message
    )


def queue_script_start(
    script_path: str,
    user_id: int,
    user_folder: str,
    file_name: str,
    file_type: str,
    message: Any,
) -> bool:
    key = process_key(user_id, file_name)
    if not has_active_subscription(user_id):
        notify_chat(message, subscription_required_text())
        return False
    if is_bot_running(user_id, file_name):
        notify_chat(message, f"⚠️ {file_name} is already running.")
        return False
    with STATE_LOCK:
        if key in pending_scripts:
            notify_chat(message, f"⏳ {file_name} is already pending.")
            return False
        pending_scripts.add(key)

    def start_worker() -> None:
        try:
            start_managed_script(
                script_path,
                user_id,
                user_folder,
                file_name,
                file_type,
                message,
            )
        finally:
            with STATE_LOCK:
                pending_scripts.discard(key)

    try:
        threading.Thread(
            target=start_worker,
            name=f"start-{user_id}-{file_ref(file_name)}",
            daemon=True,
        ).start()
        return True
    except Exception:
        with STATE_LOCK:
            pending_scripts.discard(key)
        raise


def script_runtime_state(user_id: int, file_name: str) -> str:
    key = process_key(user_id, file_name)
    with STATE_LOCK:
        if key in pending_scripts:
            return "pending"
    return "running" if is_bot_running(user_id, file_name) else "stopped"


def stop_managed_script(user_id: int, file_name: str) -> bool:
    key = process_key(user_id, file_name)
    with STATE_LOCK:
        info = bot_scripts.pop(key, None)
    if not info:
        return False
    kill_process_tree(info)
    try:
        persist_user_folder(user_id)
    except Exception:
        logger.exception("Could not persist stopped script data for %s", (user_id, file_name))
    return True


def stop_all_managed_scripts_for_user(user_id: int) -> int:
    with STATE_LOCK:
        matches = [
            (key, info)
            for key, info in bot_scripts.items()
            if key[0] == user_id
        ]
        for key, _ in matches:
            bot_scripts.pop(key, None)
    for _, info in matches:
        kill_process_tree(info)
    return len(matches)


def enforce_subscription_permissions() -> None:
    """Stop running user scripts when their subscription is missing or expired."""
    with STATE_LOCK:
        owners = {owner_id for owner_id, _ in bot_scripts}
    for owner_id in owners:
        if has_active_subscription(owner_id):
            continue
        stopped = stop_all_managed_scripts_for_user(owner_id)
        if not stopped:
            continue
        logger.warning(
            "Stopped %s script(s) for user %s because subscription is inactive",
            stopped,
            owner_id,
        )
        try:
            bot.send_message(
                owner_id,
                f"🔒 Subscription inactive. {stopped} running script(s) were stopped.",
            )
        except Exception as exc:
            logger.warning("Could not notify user %s about stopped scripts: %s", owner_id, exc)


def subscription_watchdog() -> None:
    while not SHUTDOWN_EVENT.wait(SUBSCRIPTION_CHECK_SECONDS):
        try:
            enforce_subscription_permissions()
        except Exception:
            logger.exception("Subscription watchdog failed")


# ---------------------------------------------------------------------------
# Menus: every button uses only PRIMARY or DANGER
# ---------------------------------------------------------------------------

USER_REPLY_LAYOUT: Sequence[Sequence[Tuple[str, str]]] = (
    (("Upload File", PRIMARY), ("Check Files", PRIMARY)),
    (("Bot Speed", PRIMARY), ("Statistics", PRIMARY)),
    (("Subscriptions", PRIMARY),),
    (("Send Command", PRIMARY), ("Developer", PRIMARY)),
)

ADMIN_REPLY_LAYOUT: Sequence[Sequence[Tuple[str, str]]] = (
    (("Upload File", PRIMARY), ("Check Files", PRIMARY)),
    (("Bot Speed", PRIMARY), ("Statistics", PRIMARY)),
    (("Subscriptions", PRIMARY), ("Broadcast", PRIMARY)),
    (("Lock Bot", DANGER), ("Run All Scripts", PRIMARY)),
    (("Send Command", PRIMARY), ("Admin Panel", PRIMARY)),
    (("Developer", PRIMARY),),
)


def create_reply_keyboard_main_menu(user_id: int) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    layout = ADMIN_REPLY_LAYOUT if user_id in admin_ids else USER_REPLY_LAYOUT
    for row in layout:
        buttons = []
        for text, style in row:
            if text == "Lock Bot" and bot_locked:
                text, style = "Unlock Bot", PRIMARY
            buttons.append(kbutton(text, style=style))
        markup.row(*buttons)
    return markup


def create_main_menu_inline(user_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton("Upload File", callback_data="upload", style=PRIMARY),
        ibutton("Check Files", callback_data="check_files", style=PRIMARY),
    )
    markup.row(
        ibutton("Bot Speed", callback_data="speed", style=PRIMARY),
        ibutton("Statistics", callback_data="stats", style=PRIMARY),
    )
    if user_id in admin_ids:
        markup.row(
            ibutton("Subscriptions", callback_data="subscription", style=PRIMARY),
            ibutton("Broadcast", callback_data="broadcast", style=PRIMARY),
        )
        markup.row(
            ibutton(
                "Unlock Bot" if bot_locked else "Lock Bot",
                callback_data="unlock_bot" if bot_locked else "lock_bot",
                style=PRIMARY if bot_locked else DANGER,
            ),
            ibutton("Run All Scripts", callback_data="run_all_scripts", style=PRIMARY),
        )
        markup.row(
            ibutton("Send Command", callback_data="send_command", style=PRIMARY),
            ibutton("Admin Panel", callback_data="admin_panel", style=PRIMARY),
        )
    else:
        markup.row(
            ibutton("Send Command", callback_data="send_command", style=PRIMARY)
        )
    markup.row(
            ibutton(
                "Developer",
            callback_data="developer",
            style=PRIMARY,
        )
    )
    return markup


def create_control_buttons(
    script_owner_id: int, file_name: str, running: bool
) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    if running:
        markup.row(
            ibutton(
                "Stop",
                callback_data=dynamic_file_callback("stop", script_owner_id, file_name),
                style=DANGER,
            ),
            ibutton(
                "Restart",
                callback_data=dynamic_file_callback("restart", script_owner_id, file_name),
                style=PRIMARY,
            ),
        )
        markup.row(
            ibutton(
                "Delete",
                callback_data=dynamic_file_callback("delete", script_owner_id, file_name),
                style=DANGER,
            ),
            ibutton(
                "Logs",
                callback_data=dynamic_file_callback("logs", script_owner_id, file_name),
                style=PRIMARY,
            ),
        )
    else:
        markup.row(
            ibutton(
                "Start",
                callback_data=dynamic_file_callback("start", script_owner_id, file_name),
                style=PRIMARY,
            ),
            ibutton(
                "Delete",
                callback_data=dynamic_file_callback("delete", script_owner_id, file_name),
                style=DANGER,
            ),
        )
        markup.row(
            ibutton(
                "View Logs",
                callback_data=dynamic_file_callback("logs", script_owner_id, file_name),
                style=PRIMARY,
            )
        )
    markup.row(
        ibutton("Back to Files", callback_data="check_files", style=DANGER)
    )
    return markup


def create_admin_panel() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton("Add Admin", callback_data="add_admin", style=PRIMARY),
        ibutton("Remove Admin", callback_data="remove_admin", style=DANGER),
    )
    markup.row(
        ibutton("List Admins", callback_data="list_admins", style=PRIMARY)
    )
    markup.row(
        ibutton("Add Force Join", callback_data="force_join_add", style=PRIMARY),
        ibutton("Remove Force Join", callback_data="force_join_remove", style=DANGER),
    )
    markup.row(
        ibutton(
            "Force Join: ON" if force_join_enabled else "Force Join: OFF",
            callback_data="force_join_toggle",
            style=PRIMARY if force_join_enabled else DANGER,
        )
    )
    markup.row(
        ibutton(
            "Developer Settings",
            callback_data="developer_settings",
            style=PRIMARY,
        )
    )
    markup.row(
        ibutton("Back to Main", callback_data="back_to_main", style=DANGER)
    )
    return markup


def create_subscription_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton("Add Subscription", callback_data="add_subscription", style=PRIMARY),
        ibutton("Replace Permission", callback_data="replace_subscription", style=PRIMARY),
    )
    markup.row(
        ibutton("Remove Subscription", callback_data="remove_subscription", style=DANGER),
    )
    markup.row(
        ibutton("Check Subscription", callback_data="check_subscription", style=PRIMARY)
    )
    markup.row(
        ibutton("Back to Main", callback_data="back_to_main", style=DANGER)
    )
    return markup


def create_user_subscription_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        ibutton(
            f"নিন: {DEVELOPER_USERNAME}",
            url=DEVELOPER_PROFILE_URL,
            style=PRIMARY,
        )
    )
    markup.add(ibutton("Back to Main", callback_data="back_to_main", style=DANGER))
    return markup


def create_send_command_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton("Send to Process", callback_data="send_to_process", style=PRIMARY),
        ibutton("View All Logs", callback_data="view_all_logs", style=PRIMARY),
    )
    markup.row(
        ibutton("Back to Main", callback_data="back_to_main", style=DANGER)
    )
    return markup


def create_back_to_main() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(ibutton("Back to Main", callback_data="back_to_main", style=DANGER))
    return markup


def create_developer_menu(
    back_callback: str = "back_to_main",
) -> types.InlineKeyboardMarkup:
    settings = current_developer_settings()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton(
            "👤 Profile",
            url=telegram_handle_url(settings["username"]),
            style=PRIMARY,
        ),
        ibutton(
            "📣 Channel",
            url=telegram_handle_url(settings["channel"]),
            style=PRIMARY,
        ),
    )
    markup.row(
        ibutton("Facebook", url=settings["facebook"], style=PRIMARY)
    )
    markup.row(
        ibutton("Back", callback_data=back_callback, style=DANGER)
    )
    return markup


def create_developer_settings_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton("Change Name", callback_data="developer_change_name", style=PRIMARY),
        ibutton(
            "Change Username",
            callback_data="developer_change_username",
            style=PRIMARY,
        ),
    )
    markup.row(
        ibutton(
            "Change Channel",
            callback_data="developer_change_channel",
            style=PRIMARY,
        ),
        ibutton(
            "Change Facebook",
            callback_data="developer_change_facebook",
            style=PRIMARY,
        ),
    )
    markup.row(
        ibutton("Preview", callback_data="developer_preview", style=PRIMARY),
        ibutton(
            "♻️ Reset Defaults",
            callback_data="developer_reset_confirm",
            style=DANGER,
        ),
    )
    markup.row(
        ibutton("Back to Admin", callback_data="admin_panel", style=DANGER)
    )
    return markup


def create_developer_reset_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton("Confirm Reset", callback_data="developer_reset", style=DANGER),
        ibutton(
            "🔙 Cancel",
            callback_data="developer_settings",
            style=PRIMARY,
        ),
    )
    return markup


# ---------------------------------------------------------------------------
# Welcome and ordinary user actions
# ---------------------------------------------------------------------------


def send_welcome_for_user(chat_id: int, telegram_user: Any) -> None:
    user_id = telegram_user.id
    if not ensure_access(user_id, chat_id):
        return

    is_new = user_id not in active_users
    if is_new:
        add_active_user(user_id)
        try:
            chat = bot.get_chat(user_id)
            bio = getattr(chat, "bio", None) or "No bio"
            username = telegram_user.username or "N/A"
            owner_text = (
                "🎉 <b>New user</b>\n"
                f"👤 Name: {html.escape(telegram_user.first_name or 'User')}\n"
                f"✳️ Username: @{html.escape(username)}\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"📝 Bio: {html.escape(bio)}"
            )
            bot.send_message(OWNER_ID, owner_text, parse_mode="HTML")
            photos = bot.get_user_profile_photos(user_id, limit=1)
            if photos.photos:
                bot.send_photo(
                    OWNER_ID,
                    photos.photos[0][-1].file_id,
                    caption=f"Profile photo of user {user_id}",
                )
        except Exception as exc:
            logger.warning("Could not notify owner about new user %s: %s", user_id, exc)

    status, expiry_info = user_status(user_id)
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    username = telegram_user.username or "Not set"
    name = html.escape(telegram_user.first_name or "User")
    text = (
        f"📝 Welcome, {telegram_user.first_name or 'User'}! 👋\n\n"
        f"🆔 ID: \"{user_id}\"\n"
        f"✳️ User: \"@{username}\"\n"
        f"🔰 Status: {status}{expiry_info}\n\n"
        f"📁 Files: \"{current_files}/{display_limit(file_limit)}\"\n"
        "🚀 আপনার \".py\" ও \".js\" file upload করে সহজেই Host & Run করুন\n"
        "📦 ZIP project ও support করে\n\n"
        "⚡ দ্রুত ও নিরাপদে আপনার bot/script চালান।\n\n"
        "👇 নিচের button ব্যবহার করুন\n"
        "অথবা \"/menu\" দিয়ে options দেখুন।"
    )
    send_premium_message(
        chat_id,
        text,
        "menu",
        reply_markup=create_reply_keyboard_main_menu(user_id),
    )


def send_inline_main_menu(chat_id: int, user_id: int, text: str = "〽️ Main Menu") -> None:
    send_premium_message(
        chat_id,
        text,
        "menu",
        reply_markup=create_main_menu_inline(user_id),
    )


def logic_upload_file(message: Any) -> None:
    user_id = message.from_user.id
    if not ensure_access(user_id, message.chat.id):
        return
    if user_id not in admin_ids and not has_active_subscription(user_id):
        bot.send_message(
            message.chat.id,
            "🔒 Hosting permission প্রয়োজন।\n\n"
            "Bot host করার আগে একজন Admin-এর কাছ থেকে permission নিন।",
            reply_markup=create_user_subscription_menu(),
        )
        return
    limit = get_user_file_limit(user_id)
    current = get_user_file_count(user_id)
    if current >= limit:
        bot.reply_to(
            message,
            f"⚠️ File limit reached ({current}/{display_limit(limit)}). Delete a file first.",
        )
        return
    prompt = bot.reply_to(
        message,
        "📤 File Upload করুন 🚀\n\n"
        "✅ শুধুমাত্র \".py\", \".js\" অথবা \".zip\" file গ্রহণ করা হবে।\n"
        "📦 আপনার script/project পাঠান এবং সহজেই Host & Run করুন।\n\n"
        "❌ Unsupported file format পাঠালে তা গ্রহণ করা হবে না।",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton("Cancel Upload")
        ),
    )
    with STATE_LOCK:
        pending_upload_prompts[message.from_user.id] = (
            message.chat.id,
            prompt.message_id,
        )


def build_file_list_markup(user_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files.get(user_id, [])):
        state = script_runtime_state(user_id, file_name)
        status = {
            "running": "🟢 Running",
            "pending": "🟡 Pending",
            "stopped": "🔴 Stopped",
        }[state]
        label = f"{file_name} ({file_type}) — {status}"
        markup.add(
            ibutton(
                label[:60],
                callback_data=dynamic_file_callback("open", user_id, file_name),
                style=PRIMARY,
            )
        )
    markup.add(ibutton("Back to Main", callback_data="back_to_main", style=DANGER))
    return markup


def show_file_list(chat_id: int, user_id: int, message_id: Optional[int] = None) -> None:
    items = user_files.get(user_id, [])
    text = "📂 Your files:\nSelect a file to manage." if items else "📂 No files uploaded yet."
    markup = build_file_list_markup(user_id)
    if message_id is None:
        bot.send_message(chat_id, text, reply_markup=markup)
        return
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException as exc:
        if "message is not modified" not in str(exc).lower():
            raise


def logic_check_files(message: Any) -> None:
    user_id = message.from_user.id
    if not ensure_access(user_id, message.chat.id):
        return
    show_file_list(message.chat.id, user_id)


def speed_text(user_id: int, started_at: float) -> str:
    latency = round((time.time() - started_at) * 1000, 2)
    status, _ = user_status(user_id)
    lock_status = "🔒 Locked" if bot_locked else "🔓 Unlocked"
    return (
        "⚡ Bot Speed & Status\n\n"
        f"⏱ API response: {latency} ms\n"
        f"🚦 Bot: {lock_status}\n"
        f"👤 Level: {status}"
    )


def logic_bot_speed(message: Any) -> None:
    started = time.time()
    wait_message = bot.reply_to(message, "🏃 Testing speed...")
    bot.send_chat_action(message.chat.id, "typing")
    bot.edit_message_text(
        speed_text(message.from_user.id, started),
        message.chat.id,
        wait_message.message_id,
    )


def developer_text() -> str:
    settings = current_developer_settings()
    profile_url = telegram_handle_url(settings["username"])
    channel_url = telegram_handle_url(settings["channel"])
    return (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 <b>MAIN DEVELOPER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Name:</b> {html.escape(settings['name'])}\n"
        f"👤 <b>Username:</b> <a href=\"{html.escape(profile_url, quote=True)}\">"
        f"{html.escape(settings['username'])}</a>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📣 <b>Channel:</b> <a href=\"{html.escape(channel_url, quote=True)}\">"
        f"{html.escape(settings['channel'])}</a>\n"
        f"🌐 <b>Facebook:</b> <a href=\""
        f"{html.escape(settings['facebook'], quote=True)}\">Click Here</a>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>This bot is developed &amp; maintained by "
        f"{html.escape(settings['name'])}</i>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


def developer_settings_text() -> str:
    settings = current_developer_settings()
    return (
        "👨‍💻 <b>Developer Settings</b>\n\n"
        f"🆔 <b>Name:</b> {html.escape(settings['name'])}\n"
        f"👤 <b>Username:</b> {html.escape(settings['username'])}\n"
        f"📣 <b>Channel:</b> {html.escape(settings['channel'])}\n"
        f"🌐 <b>Facebook:</b> "
        f"<a href=\"{html.escape(settings['facebook'], quote=True)}\">Open Link</a>\n\n"
        "Select the information you want to change."
    )


def logic_developer(message: Any) -> None:
    bot.send_message(
        message.chat.id,
        developer_text(),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=create_developer_menu(),
    )


def logic_contact_owner(message: Any) -> None:
    """Backward-compatible command alias for /contactowner."""
    logic_developer(message)


def logic_send_command(message: Any) -> None:
    if not ensure_access(message.from_user.id, message.chat.id):
        return
    bot.send_message(
        message.chat.id,
        "📤 Send Command Options",
        reply_markup=create_send_command_menu(),
    )


def logic_statistics(message: Any, actual_user_id: Optional[int] = None) -> None:
    user_id = actual_user_id if actual_user_id is not None else message.from_user.id
    own_files = sorted(user_files.get(user_id, []))
    own_states = [
        (file_name, script_runtime_state(user_id, file_name))
        for file_name, _ in own_files
    ]
    own_running = sum(state == "running" for _, state in own_states)
    own_pending = sum(state == "pending" for _, state in own_states)
    own_stopped = sum(state == "stopped" for _, state in own_states)

    if user_id not in admin_ids:
        text = (
            "📊 Your Bot Statistics\n\n"
            f"📂 Total bots: {len(own_files)}\n"
            f"🟢 Running: {own_running}\n"
            f"🟡 Pending: {own_pending}\n"
            f"🔴 Stopped: {own_stopped}\n"
            f"💳 Subscription: {subscription_summary(user_id)}"
        )
        if own_states:
            state_icons = {"running": "🟢", "pending": "🟡", "stopped": "🔴"}
            details = [
                f"{state_icons[state]} {name}"
                for name, state in own_states[:20]
            ]
            text += "\n\n🤖 Your bots:\n" + "\n".join(details)
            if len(own_states) > 20:
                text += f"\n… and {len(own_states) - 20} more"
    else:
        with STATE_LOCK:
            process_items = list(bot_scripts.items())
            total_pending = len(pending_scripts)
            total_users = len(active_users)
            total_files = sum(len(items) for items in user_files.values())
        total_running = sum(
            1 for (owner_id, name), _ in process_items if is_bot_running(owner_id, name)
        )
        text = (
            "📊 Admin Bot Statistics\n\n"
            f"👥 Total users: {total_users}\n"
            f"📂 File records: {total_files}\n"
            f"🟢 Active scripts: {total_running}\n"
            f"🟡 Pending scripts: {total_pending}\n"
            f"🤖 Your running scripts: {own_running}\n"
            f"🔒 Bot status: {'Locked' if bot_locked else 'Unlocked'}"
        )
    bot.send_message(message.chat.id, text)


# ---------------------------------------------------------------------------
# Admin actions
# ---------------------------------------------------------------------------


def require_admin_message(message: Any) -> bool:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return False
    return True


def logic_subscriptions_panel(message: Any) -> None:
    if not require_admin_message(message):
        return
    bot.send_message(
        message.chat.id,
        "💳 Subscription Management",
        reply_markup=create_subscription_menu(),
    )


def logic_broadcast_init(message: Any) -> None:
    if not require_admin_message(message):
        return
    prompt = bot.send_message(
        message.chat.id,
        "📢 Send one message or media item to broadcast.\nSend /cancel to abort.",
    )
    bot.register_next_step_handler(prompt, process_broadcast_message)


def logic_toggle_lock_bot(message: Any) -> None:
    global bot_locked
    if not require_admin_message(message):
        return
    bot_locked = not bot_locked
    save_setting("bot_locked", "1" if bot_locked else "0")
    state = "locked" if bot_locked else "unlocked"
    bot.reply_to(
        message,
        f"🔒 Bot has been {state}.",
        reply_markup=create_reply_keyboard_main_menu(message.from_user.id),
    )


def logic_admin_panel(message: Any) -> None:
    if not require_admin_message(message):
        return
    bot.send_message(message.chat.id, "👑 Admin Panel", reply_markup=create_admin_panel())


def prompt_force_join(chat_id: int) -> None:
    current = "\n\nবর্তমান button:\n" + "\n".join(
        f"{index}. {item['name']} - {item['url']}"
        for index, item in enumerate(force_join_settings, 1)
    ) if force_join_settings else ""
    prompt = bot.send_message(
        chat_id,
        "🔒 Force Join সেট করতে এই format-এ পাঠান:\n"
        "Button Name - https://t.me/public_channel\n\n"
        "Channel-এ bot-কে admin করে রাখুন।"
        + current,
    )
    bot.register_next_step_handler(prompt, process_force_join)


def process_force_join(message: Any) -> None:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    raw = (message.text or "").strip()
    if raw.lower() == "/cancel":
        bot.reply_to(message, "Force Join action cancelled.")
        return
    if " - " not in raw:
        bot.reply_to(message, "⚠️ Format ভুল। উদাহরণ: Join Channel - https://t.me/mychannel")
        return
    name, url = [part.strip() for part in raw.rsplit(" - ", 1)]
    target = force_join_target_from_url(url)
    if not name or not target:
        bot.reply_to(
            message,
            "⚠️ একটি public channel link দিন (যেমন https://t.me/mychannel)। "
            "Private invite link দিয়ে membership check করা যাবে না.",
        )
        return
    try:
        bot.get_chat(target)
    except Exception:
        bot.reply_to(
            message,
            "⚠️ Channel পাওয়া যায়নি। Link ঠিক আছে এবং bot-কে channel-এ admin করা হয়েছে কিনা দেখুন.",
        )
        return
    config = {"name": name[:64], "url": url, "chat": target}
    force_join_settings.append(config)
    save_setting("force_join", json.dumps(force_join_settings, ensure_ascii=False))
    bot.reply_to(
        message,
        f"✅ Force Join button যোগ হয়েছে.\n🔘 Button: {name[:64]}\n🔗 Link: {url}\n"
        "Admin Panel থেকে Force Join ON করলে এটি users-কে দেখানো হবে.",
    )


def prompt_remove_force_join(chat_id: int) -> None:
    if not force_join_settings:
        bot.send_message(chat_id, "ℹ️ কোনো Force Join button সেট করা নেই.")
        return
    buttons = "\n".join(
        f"{index}. {item['name']} - {item['url']}"
        for index, item in enumerate(force_join_settings, 1)
    )
    prompt = bot.send_message(
        chat_id,
        "যে button remove করতে চান তার number পাঠান:\n\n" + buttons,
    )
    bot.register_next_step_handler(prompt, process_remove_force_join)


def process_remove_force_join(message: Any) -> None:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    raw = (message.text or "").strip()
    if raw.lower() == "/cancel":
        bot.reply_to(message, "Remove action cancelled.")
        return
    try:
        index = int(raw) - 1
        removed = force_join_settings.pop(index)
    except (ValueError, IndexError):
        bot.reply_to(message, "⚠️ সঠিক button number পাঠান.")
        return
    save_setting("force_join", json.dumps(force_join_settings, ensure_ascii=False))
    bot.reply_to(message, f"✅ Removed Force Join button: {removed['name']}")


def logic_toggle_force_join(message: Any, actor_id: Optional[int] = None) -> None:
    global force_join_enabled
    if (actor_id if actor_id is not None else message.from_user.id) not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    if not force_join_settings:
        bot.reply_to(message, "ℹ️ আগে অন্তত একটি Force Join button add করুন.")
        return
    force_join_enabled = not force_join_enabled
    save_setting("force_join_enabled", "1" if force_join_enabled else "0")
    state = "ON" if force_join_enabled else "OFF"
    bot.reply_to(message, f"✅ Force Join এখন {state}.")


def logic_run_all_scripts(message_or_call: Any) -> None:
    if isinstance(message_or_call, telebot.types.CallbackQuery):
        admin_id = message_or_call.from_user.id
        chat_id = message_or_call.message.chat.id
        message = message_or_call.message
    else:
        admin_id = message_or_call.from_user.id
        chat_id = message_or_call.chat.id
        message = message_or_call
    if admin_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ Admin permission required.")
        return

    started = 0
    skipped = 0
    no_subscription = 0
    snapshot = {user_id: list(items) for user_id, items in user_files.items()}
    for owner_id, items in snapshot.items():
        if not has_active_subscription(owner_id):
            no_subscription += len(items)
            continue
        folder = get_user_folder(owner_id)
        for file_name, file_type in items:
            if script_runtime_state(owner_id, file_name) != "stopped":
                skipped += 1
                continue
            path = os.path.join(folder, file_name)
            if not os.path.isfile(path):
                skipped += 1
                continue
            if queue_script_start(path, owner_id, folder, file_name, file_type, message):
                started += 1
            else:
                skipped += 1
            time.sleep(0.15)
    bot.send_message(
        chat_id,
        f"✅ Run-all request queued.\n"
        f"▶️ Queued: {started}\n"
        f"⏭ Skipped: {skipped}\n"
        f"🔒 No subscription: {no_subscription}",
    )


# ---------------------------------------------------------------------------
# Process command and logs
# ---------------------------------------------------------------------------


def running_scripts_for(requester_id: int) -> List[Tuple[int, str, ProcessInfo]]:
    results: List[Tuple[int, str, ProcessInfo]] = []
    with STATE_LOCK:
        snapshot = list(bot_scripts.items())
    for (owner_id, file_name), info in snapshot:
        if requester_id != owner_id and requester_id not in admin_ids:
            continue
        if is_bot_running(owner_id, file_name):
            results.append((owner_id, file_name, info))
    return results


def show_running_script_selector(chat_id: int, requester_id: int) -> None:
    scripts = running_scripts_for(requester_id)
    if not scripts:
        bot.send_message(chat_id, "❌ No running scripts found.", reply_markup=create_back_to_main())
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for owner_id, file_name, _ in scripts:
        markup.add(
            ibutton(
                f"📝 {file_name} — User {owner_id}"[:60],
                callback_data=dynamic_file_callback("sendcmd", owner_id, file_name),
                style=PRIMARY,
            )
        )
    markup.add(ibutton("Back", callback_data="send_command", style=DANGER))
    bot.send_message(chat_id, "Select a running script:", reply_markup=markup)


def process_send_command(message: Any, owner_id: int, file_name: str) -> None:
    requester_id = message.from_user.id
    if requester_id != owner_id and requester_id not in admin_ids:
        bot.reply_to(message, "⚠️ Permission denied.")
        return
    if message.text and message.text.lower() == "/cancel":
        bot.reply_to(message, "Command cancelled.")
        return
    command_text = message.text or ""
    if not command_text:
        bot.reply_to(message, "⚠️ Send a text command.")
        return
    with STATE_LOCK:
        info = bot_scripts.get(process_key(owner_id, file_name))
    if not info or not is_bot_running(owner_id, file_name):
        bot.reply_to(message, "❌ Script is no longer running.")
        return
    process = info["process"]
    try:
        if process.stdin is None:
            raise RuntimeError("Process stdin is unavailable")
        process.stdin.write(command_text + "\n")
        process.stdin.flush()
        bot.reply_to(message, f"✅ Command sent to {file_name}.")
    except Exception as exc:
        logger.exception("Could not send command to %s", (owner_id, file_name))
        bot.reply_to(message, f"❌ Command failed: {exc}")


def list_log_files(user_id: int) -> List[Tuple[str, int]]:
    folder = get_user_folder(user_id)
    results: List[Tuple[str, int]] = []
    try:
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if name.endswith(".log") and os.path.isfile(path):
                results.append((name, os.path.getsize(path)))
    except OSError:
        pass
    return sorted(results)


def show_all_logs(chat_id: int, user_id: int) -> None:
    logs = list_log_files(user_id)
    if not logs:
        bot.send_message(chat_id, "📜 No log files found.", reply_markup=create_back_to_main())
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name, size in logs:
        markup.add(
            ibutton(
                f"📜 {name} ({size / 1024:.1f} KB)"[:60],
                callback_data=f"l|view|{user_id}|{file_ref(name)}",
                style=PRIMARY,
            )
        )
    markup.add(ibutton("Back", callback_data="send_command", style=DANGER))
    bot.send_message(chat_id, "📜 Available Log Files", reply_markup=markup)


def send_log_document(chat_id: int, owner_id: int, log_name: str) -> None:
    path = os.path.join(get_user_folder(owner_id), log_name)
    if not os.path.isfile(path):
        bot.send_message(chat_id, "❌ Log file not found.")
        return
    try:
        with open(path, "rb") as log_file:
            bot.send_document(chat_id, log_file, caption=f"📜 {log_name}")
    except Exception as exc:
        logger.exception("Could not send log %s", path)
        bot.send_message(chat_id, f"❌ Could not send log: {exc}")


# ---------------------------------------------------------------------------
# Upload handling
# ---------------------------------------------------------------------------


def replace_path(source: str, destination: str) -> None:
    if os.path.isdir(source) and not os.path.islink(source) and os.path.isdir(destination):
        for child_name in os.listdir(source):
            replace_path(
                os.path.join(source, child_name),
                os.path.join(destination, child_name),
            )
        try:
            os.rmdir(source)
        except OSError:
            pass
        return
    if os.path.isdir(destination) and not os.path.islink(destination):
        shutil.rmtree(destination)
    elif os.path.exists(destination) or os.path.islink(destination):
        os.remove(destination)
    shutil.move(source, destination)


def handle_zip_file(content: bytes, zip_name: str, message: Any) -> None:
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)
    temp_dir = tempfile.mkdtemp(prefix=f"hostbot_{user_id}_")
    try:
        zip_path = os.path.join(temp_dir, safe_filename(zip_name))
        extraction_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extraction_dir, exist_ok=True)
        with open(zip_path, "wb") as output:
            output.write(content)

        safe_extract_zip(zip_path, extraction_dir)
        project_root, main_name, file_type = find_project_root_and_main(extraction_dir)

        for item_name in os.listdir(project_root):
            source = os.path.join(project_root, item_name)
            destination = os.path.join(user_folder, safe_filename(item_name))
            replace_path(source, destination)

        main_name = safe_filename(main_name)
        main_path = os.path.join(user_folder, main_name)
        if not os.path.isfile(main_path):
            raise ValueError("The selected main script could not be moved")

        persist_user_folder(user_id)
        save_user_file(user_id, main_name, file_type)
        if has_active_subscription(user_id):
            bot.reply_to(
                message,
                f"✅ ZIP extracted. Starting main script: {main_name}",
            )
            queue_script_start(
                main_path, user_id, user_folder, main_name, file_type, message
            )
        else:
            bot.reply_to(
                message,
                f"✅ ZIP extracted and {main_name} was saved.\n\n"
                + subscription_required_text(),
            )
    except zipfile.BadZipFile:
        bot.reply_to(message, "❌ Invalid or corrupted ZIP file.")
    except ValueError as exc:
        bot.reply_to(message, f"❌ ZIP rejected: {exc}")
    except Exception as exc:
        logger.exception("ZIP processing failed for user %s", user_id)
        bot.reply_to(message, f"❌ ZIP processing failed: {exc}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def handle_single_script(content: bytes, file_name: str, file_type: str, message: Any) -> None:
    user_id = message.from_user.id
    safe_name = safe_filename(file_name)
    allowed, reason = scan_regular_file(content, safe_name)
    if not allowed:
        bot.reply_to(message, f"🚨 Security check failed: {reason}")
        return
    user_folder = get_user_folder(user_id)
    file_path = os.path.join(user_folder, safe_name)
    try:
        with open(file_path, "wb") as output:
            output.write(content)
        persist_local_file(user_id, file_path)
        save_user_file(user_id, safe_name, file_type)
        if has_active_subscription(user_id):
            bot.reply_to(message, f"✅ Saved {safe_name}. Starting it now...")
            queue_script_start(
                file_path, user_id, user_folder, safe_name, file_type, message
            )
        else:
            bot.reply_to(
                message,
                f"✅ Saved {safe_name}.\n\n" + subscription_required_text(),
            )
    except Exception as exc:
        logger.exception("Could not save uploaded script %s", safe_name)
        bot.reply_to(message, f"❌ Could not save file: {exc}")


@bot.message_handler(content_types=["document"])
def handle_document_upload(message: Any) -> None:
    user_id = message.from_user.id
    if not ensure_access(user_id, message.chat.id):
        return
    with STATE_LOCK:
        upload_pending = user_id in pending_upload_prompts
    if not upload_pending:
        return

    limit = get_user_file_limit(user_id)
    current = get_user_file_count(user_id)
    if current >= limit:
        bot.reply_to(
            message,
            f"⚠️ File limit reached ({current}/{display_limit(limit)}).",
        )
        return

    document = message.document
    try:
        file_name = safe_filename(document.file_name or "")
    except ValueError:
        bot.reply_to(message, "⚠️ This document has an invalid filename.")
        return
    extension = os.path.splitext(file_name)[1].lower()
    if extension not in {".py", ".js", ".zip"}:
        bot.reply_to(message, "⚠️ Only .py, .js and .zip files are supported.")
        return
    if document.file_size and document.file_size > MAX_UPLOAD_BYTES:
        bot.reply_to(message, f"⚠️ Maximum upload size is {MAX_UPLOAD_MB} MB.")
        return

    try:
        try:
            bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
            bot.send_message(
                OWNER_ID,
                f"⬆️ File {html.escape(file_name)} from user <code>{user_id}</code>",
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning("Could not forward upload to owner: %s", exc)

        wait_message = bot.reply_to(message, f"⏳ Downloading {file_name}...")
        file_info = bot.get_file(document.file_id)
        content = bot.download_file(file_info.file_path)
        if len(content) > MAX_UPLOAD_BYTES:
            bot.edit_message_text(
                f"❌ File is larger than {MAX_UPLOAD_MB} MB.",
                message.chat.id,
                wait_message.message_id,
            )
            return
        bot.edit_message_text(
            f"✅ Downloaded {file_name}. Processing...",
            message.chat.id,
            wait_message.message_id,
        )
        with STATE_LOCK:
            pending_upload_prompts.pop(user_id, None)
        bot.send_message(
            message.chat.id,
            "✅ ফাইল গ্রহণ করা হয়েছে। Processing শুরু হচ্ছে...",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        if extension == ".zip":
            handle_zip_file(content, file_name, message)
        elif extension == ".py":
            handle_single_script(content, file_name, "py", message)
        else:
            handle_single_script(content, file_name, "js", message)
    except telebot.apihelper.ApiTelegramException as exc:
        logger.exception("Telegram API upload error for user %s", user_id)
        bot.reply_to(message, f"❌ Telegram file error: {exc}")
    except Exception as exc:
        logger.exception("Upload processing failed for user %s", user_id)
        bot.reply_to(message, f"❌ Upload failed: {exc}")


def cancel_upload(message: Any) -> None:
    user_id = message.from_user.id
    with STATE_LOCK:
        prompt = pending_upload_prompts.pop(user_id, None)
    if prompt:
        try:
            bot.delete_message(prompt[0], prompt[1])
        except Exception:
            pass
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    bot.send_message(
        message.chat.id,
        "❌ Upload বাতিল করা হয়েছে।",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    send_premium_message(
        message.chat.id,
        "Main Menu",
        "menu",
        reply_markup=create_reply_keyboard_main_menu(user_id),
    )


@bot.message_handler(
    func=lambda message: bool(
        message.text
        and message.text.strip() == "Cancel Upload"
        and message.from_user.id in pending_upload_prompts
    )
)
def handle_cancel_upload(message: Any) -> None:
    cancel_upload(message)


@bot.message_handler(
    func=lambda message: bool(
        message.from_user.id in pending_upload_prompts
        and message.text
    )
)
def handle_invalid_upload(message: Any) -> None:
    bot.reply_to(
        message,
        "⚠️ <b>সঠিক ফাইল দিন</b>\n\n"
        "শুধু <code>.py</code>, <code>.js</code> অথবা <code>.zip</code> "
        "ফাইল পাঠান। বাতিল করতে নিচের <b>Cancel Upload</b> বাটনে চাপুন।",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Commands and reply-keyboard handlers
# ---------------------------------------------------------------------------


@bot.message_handler(commands=["start", "help"])
def command_start(message: Any) -> None:
    send_welcome_for_user(message.chat.id, message.from_user)


@bot.message_handler(commands=["menu"])
def command_menu(message: Any) -> None:
    if ensure_access(message.from_user.id, message.chat.id):
        send_inline_main_menu(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["status", "statistics"])
def command_status(message: Any) -> None:
    logic_statistics(message)


@bot.message_handler(commands=["ping"])
def command_ping(message: Any) -> None:
    started = time.time()
    sent = bot.reply_to(message, "Pong!")
    latency = round((time.time() - started) * 1000, 2)
    bot.edit_message_text(
        f"Pong! Latency: {latency} ms", message.chat.id, sent.message_id
    )


@bot.message_handler(commands=["uploadfile"])
def command_upload(message: Any) -> None:
    logic_upload_file(message)


@bot.message_handler(commands=["checkfiles"])
def command_files(message: Any) -> None:
    logic_check_files(message)


@bot.message_handler(commands=["botspeed"])
def command_speed(message: Any) -> None:
    logic_bot_speed(message)


@bot.message_handler(commands=["sendcommand"])
def command_send_process(message: Any) -> None:
    logic_send_command(message)


@bot.message_handler(commands=["contactowner"])
def command_contact(message: Any) -> None:
    logic_contact_owner(message)


@bot.message_handler(commands=["developer"])
def command_developer(message: Any) -> None:
    logic_developer(message)


@bot.message_handler(commands=["subscriptions"])
def command_subscriptions(message: Any) -> None:
    logic_subscriptions_panel(message)


@bot.message_handler(commands=["broadcast"])
def command_broadcast(message: Any) -> None:
    logic_broadcast_init(message)


@bot.message_handler(commands=["lockbot"])
def command_lock(message: Any) -> None:
    logic_toggle_lock_bot(message)


@bot.message_handler(commands=["adminpanel"])
def command_admin(message: Any) -> None:
    logic_admin_panel(message)


@bot.message_handler(commands=["runningallcode"])
def command_run_all(message: Any) -> None:
    logic_run_all_scripts(message)


def logic_user_subscriptions(message: Any) -> None:
    if message.from_user.id in admin_ids:
        logic_subscriptions_panel(message)
        return
    bot.send_message(
        message.chat.id,
        user_subscription_details(message.from_user.id),
        parse_mode="HTML",
        reply_markup=create_user_subscription_menu(),
    )


BUTTON_TEXT_TO_LOGIC = {
    "Upload File": logic_upload_file,
    "Check Files": logic_check_files,
    "Bot Speed": logic_bot_speed,
    "Statistics": logic_statistics,
    "Send Command": logic_send_command,
    "Developer": logic_developer,
    "Subscriptions": logic_user_subscriptions,
    "Broadcast": logic_broadcast_init,
    "Lock Bot": logic_toggle_lock_bot,
    "Unlock Bot": logic_toggle_lock_bot,
    "Run All Scripts": logic_run_all_scripts,
    "Admin Panel": logic_admin_panel,
}


@bot.message_handler(func=lambda message: bool(message.text in BUTTON_TEXT_TO_LOGIC))
def handle_reply_button(message: Any) -> None:
    if message.text != "Developer" and not ensure_access(
        message.from_user.id, message.chat.id
    ):
        return
    action = BUTTON_TEXT_TO_LOGIC.get(message.text)
    if action:
        action(message)


# ---------------------------------------------------------------------------
# Broadcast implementation
# ---------------------------------------------------------------------------


def process_broadcast_message(message: Any) -> None:
    admin_id = message.from_user.id
    if admin_id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    if message.text and message.text.strip().lower() == "/cancel":
        bot.reply_to(message, "Broadcast cancelled.")
        return

    with STATE_LOCK:
        pending_broadcasts[admin_id] = (message.chat.id, message.message_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        ibutton(
            "✅ Confirm & Send",
            callback_data=f"confirm_broadcast|{admin_id}",
            style=PRIMARY,
        ),
        ibutton("Cancel", callback_data=f"cancel_broadcast|{admin_id}", style=DANGER),
    )
    bot.reply_to(
        message,
        f"⚠️ Send this message to {len(active_users)} user(s)?",
        reply_markup=markup,
    )


def execute_broadcast(source_chat_id: int, source_message_id: int, admin_chat_id: int) -> None:
    sent = 0
    failed = 0
    blocked = 0
    started = time.time()
    recipients = list(active_users)
    for index, recipient in enumerate(recipients):
        try:
            bot.copy_message(recipient, source_chat_id, source_message_id)
            sent += 1
        except telebot.apihelper.ApiTelegramException as exc:
            description = str(exc).lower()
            if any(
                phrase in description
                for phrase in ("blocked", "deactivated", "chat not found", "kicked")
            ):
                blocked += 1
            elif "too many requests" in description or "flood" in description:
                match = re.search(r"retry after (\d+)", description)
                delay = int(match.group(1)) + 1 if match else 5
                time.sleep(min(delay, 60))
                try:
                    bot.copy_message(recipient, source_chat_id, source_message_id)
                    sent += 1
                except Exception:
                    failed += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        if (index + 1) % 25 == 0:
            time.sleep(1.2)

    duration = round(time.time() - started, 2)
    bot.send_message(
        admin_chat_id,
        "📢 Broadcast Complete\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"🚫 Blocked/inactive: {blocked}\n"
        f"👥 Targets: {len(recipients)}\n"
        f"⏱ Duration: {duration}s",
    )


# ---------------------------------------------------------------------------
# Admin next-step handlers
# ---------------------------------------------------------------------------


def cancelled(message: Any) -> bool:
    return bool(message.text and message.text.strip().lower() == "/cancel")


DEVELOPER_SETTING_LABELS = {
    "name": "Name",
    "username": "Username",
    "channel": "Channel",
    "facebook": "Facebook URL",
}

DEVELOPER_SETTING_PROMPTS = {
    "name": "Send the new developer name.",
    "username": "Send the new Telegram username. Example: @username",
    "channel": "Send the new Telegram channel. Example: @channelname",
    "facebook": "Send the full Facebook profile/page URL.",
}


def prompt_developer_setting(chat_id: int, field: str) -> None:
    if field not in DEVELOPER_SETTING_LABELS:
        bot.send_message(chat_id, "❌ Unknown developer setting.")
        return
    current_value = current_developer_settings()[field]
    prompt = bot.send_message(
        chat_id,
        f"👨‍💻 Change Developer {DEVELOPER_SETTING_LABELS[field]}\n\n"
        f"Current: {current_value}\n\n"
        f"{DEVELOPER_SETTING_PROMPTS[field]}\n"
        "/cancel to abort.",
    )
    bot.register_next_step_handler(prompt, process_developer_setting, field)


def process_developer_setting(message: Any, field: str) -> None:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    if cancelled(message):
        bot.reply_to(
            message,
            "Developer update cancelled.",
            reply_markup=create_developer_settings_menu(),
        )
        return
    if not message.text:
        retry = bot.reply_to(message, "⚠️ Send text only, or /cancel.")
        bot.register_next_step_handler(retry, process_developer_setting, field)
        return
    try:
        normalized = normalize_developer_setting(field, message.text)
    except ValueError as exc:
        retry = bot.reply_to(message, f"⚠️ {exc}\nTry again, or /cancel.")
        bot.register_next_step_handler(retry, process_developer_setting, field)
        return

    save_developer_setting(field, normalized)
    bot.reply_to(
        message,
        f"✅ Developer {DEVELOPER_SETTING_LABELS[field]} updated.\n\n"
        + developer_settings_text(),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=create_developer_settings_menu(),
    )


def prompt_add_admin(chat_id: int) -> None:
    prompt = bot.send_message(chat_id, "👑 Send the User ID to promote.\n/cancel to abort.")
    bot.register_next_step_handler(prompt, process_add_admin)


def process_add_admin(message: Any) -> None:
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⚠️ Owner permission required.")
        return
    if cancelled(message):
        bot.reply_to(message, "Admin promotion cancelled.")
        return
    try:
        new_admin = int((message.text or "").strip())
        if new_admin <= 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "⚠️ Send a valid numeric User ID.")
        return
    if new_admin in admin_ids:
        bot.reply_to(message, "⚠️ That user is already an administrator.")
        return
    add_admin_db(new_admin)
    bot.reply_to(message, f"✅ User {new_admin} is now an administrator.")
    try:
        bot.send_message(new_admin, "🎉 You are now an administrator.")
    except Exception:
        pass


def prompt_remove_admin(chat_id: int) -> None:
    prompt = bot.send_message(chat_id, "👑 Send the Admin ID to remove.\n/cancel to abort.")
    bot.register_next_step_handler(prompt, process_remove_admin)


def process_remove_admin(message: Any) -> None:
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⚠️ Owner permission required.")
        return
    if cancelled(message):
        bot.reply_to(message, "Admin removal cancelled.")
        return
    try:
        admin_id = int((message.text or "").strip())
    except ValueError:
        bot.reply_to(message, "⚠️ Send a valid numeric User ID.")
        return
    if admin_id == OWNER_ID:
        bot.reply_to(message, "⚠️ The owner cannot be removed.")
        return
    if remove_admin_db(admin_id):
        bot.reply_to(message, f"✅ Admin {admin_id} removed.")
        try:
            bot.send_message(admin_id, "ℹ️ Your administrator access was removed.")
        except Exception:
            pass
    else:
        bot.reply_to(message, "⚠️ That user is not an administrator.")


def prompt_add_subscription(chat_id: int) -> None:
    prompt = bot.send_message(
        chat_id,
        "💳 Send User ID, days and file limit.\n"
        "Example: 12345678 30 2\n"
        "মানে: ৩০ দিন permission, সর্বোচ্চ ২টি file.\n"
        "/cancel to abort.",
    )
    bot.register_next_step_handler(prompt, process_add_subscription)


def process_add_subscription(message: Any) -> None:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    if cancelled(message):
        bot.reply_to(message, "Subscription action cancelled.")
        return
    try:
        user_id_text, days_text, file_limit_text = (message.text or "").split()
        user_id = int(user_id_text)
        days = int(days_text)
        file_limit = int(file_limit_text)
        if user_id <= 0 or days <= 0 or file_limit <= 0:
            raise ValueError
    except (TypeError, ValueError):
        bot.reply_to(message, "⚠️ Invalid format. Use: UserID days file_limit\nExample: 12345678 30 2")
        return
    now = datetime.now()
    old_expiry = user_subscriptions.get(user_id, {}).get("expiry")
    base = old_expiry if old_expiry and old_expiry > now else now
    expiry = base + timedelta(days=days)
    save_subscription(
        user_id,
        expiry,
        started_at=now,
        granted_days=days,
        file_limit=file_limit,
    )
    bot.reply_to(
        message,
        f"✅ Permission active until {expiry:%Y-%m-%d %H:%M}.\n"
        f"📁 File limit: {file_limit}",
    )
    try:
        bot.send_message(
            user_id,
            f"🎉 Permission activated until {expiry:%Y-%m-%d}.\n"
            f"📁 You can use up to {file_limit} file(s).",
        )
    except Exception:
        pass


def prompt_replace_subscription(chat_id: int) -> None:
    prompt = bot.send_message(
        chat_id,
        "🔁 Send User ID, new days and new file limit.\n"
        "Example: 12345678 30 2\n"
        "এটি পুরোনো permission পুরোপুরি replace করবে।\n"
        "/cancel to abort.",
    )
    bot.register_next_step_handler(prompt, process_replace_subscription)


def process_replace_subscription(message: Any) -> None:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    if cancelled(message):
        bot.reply_to(message, "Permission replacement cancelled.")
        return
    try:
        user_id_text, days_text, file_limit_text = (message.text or "").split()
        user_id = int(user_id_text)
        days = int(days_text)
        file_limit = int(file_limit_text)
        if user_id <= 0 or days <= 0 or file_limit <= 0:
            raise ValueError
    except (TypeError, ValueError):
        bot.reply_to(
            message,
            "⚠️ Invalid format. Use: UserID days file_limit\n"
            "Example: 12345678 30 2",
        )
        return

    now = datetime.now()
    expiry = now + timedelta(days=days)
    save_subscription(
        user_id,
        expiry,
        started_at=now,
        granted_days=days,
        file_limit=file_limit,
    )
    bot.reply_to(
        message,
        f"✅ Permission replaced for {user_id}.\n"
        f"⏳ Days: {days}\n"
        f"📁 File limit: {file_limit}\n"
        f"⏰ Ends: {expiry:%Y-%m-%d %H:%M}.",
    )
    try:
        bot.send_message(
            user_id,
            f"🔁 Your hosting permission was updated.\n"
            f"⏳ Valid for {days} day(s).\n"
            f"📁 File limit: {file_limit}.",
        )
    except Exception:
        pass


def prompt_remove_subscription(chat_id: int) -> None:
    prompt = bot.send_message(chat_id, "💳 Send the User ID to remove.\n/cancel to abort.")
    bot.register_next_step_handler(prompt, process_remove_subscription)


def process_remove_subscription(message: Any) -> None:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    if cancelled(message):
        bot.reply_to(message, "Subscription action cancelled.")
        return
    try:
        user_id = int((message.text or "").strip())
    except ValueError:
        bot.reply_to(message, "⚠️ Send a valid numeric User ID.")
        return
    if user_id not in user_subscriptions:
        bot.reply_to(message, "⚠️ No subscription record found.")
        return
    remove_subscription_db(user_id)
    stopped = stop_all_managed_scripts_for_user(user_id)
    bot.reply_to(
        message,
        f"✅ Subscription removed for {user_id}.\n"
        f"🔴 Stopped scripts: {stopped}",
    )
    try:
        bot.send_message(
            user_id,
            f"ℹ️ Your subscription was removed. {stopped} running script(s) stopped.",
        )
    except Exception:
        pass


def prompt_check_subscription(chat_id: int) -> None:
    prompt = bot.send_message(chat_id, "💳 Send the User ID to check.\n/cancel to abort.")
    bot.register_next_step_handler(prompt, process_check_subscription)


def process_check_subscription(message: Any) -> None:
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permission required.")
        return
    if cancelled(message):
        bot.reply_to(message, "Subscription check cancelled.")
        return
    try:
        user_id = int((message.text or "").strip())
    except ValueError:
        bot.reply_to(message, "⚠️ Send a valid numeric User ID.")
        return
    expiry = user_subscriptions.get(user_id, {}).get("expiry")
    if not expiry:
        bot.reply_to(message, "ℹ️ No subscription record found.")
    elif expiry <= datetime.now():
        remove_subscription_db(user_id)
        stopped = stop_all_managed_scripts_for_user(user_id)
        bot.reply_to(
            message,
            f"⚠️ Subscription expired at {expiry:%Y-%m-%d %H:%M}.\n"
            f"🔴 Stopped scripts: {stopped}",
        )
    else:
        remaining = expiry - datetime.now()
        bot.reply_to(
            message,
            f"✅ Active until {expiry:%Y-%m-%d %H:%M} ({remaining.days} full day(s) left).",
        )


# ---------------------------------------------------------------------------
# Callback handlers
# ---------------------------------------------------------------------------


def answer_callback(call: Any, text: Optional[str] = None, alert: bool = False) -> None:
    try:
        bot.answer_callback_query(call.id, text=text, show_alert=alert)
    except Exception:
        pass


def edit_file_control(call: Any, owner_id: int, file_name: str, file_type: str) -> None:
    state = script_runtime_state(owner_id, file_name)
    running = state == "running"
    status = {
        "running": "🟢 Running",
        "pending": "🟡 Pending",
        "stopped": "🔴 Stopped",
    }[state]
    bot.edit_message_text(
        f"⚙️ Controls for <code>{html.escape(file_name)}</code> ({file_type})\n"
        f"👤 Owner: <code>{owner_id}</code>\n"
        f"Status: {status}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_control_buttons(owner_id, file_name, running),
        parse_mode="HTML",
    )


def send_log_preview(call: Any, owner_id: int, file_name: str) -> None:
    log_path = os.path.join(
        get_user_folder(owner_id), f"{os.path.splitext(file_name)[0]}.log"
    )
    if not os.path.isfile(log_path):
        answer_callback(call, "No log file found.", alert=True)
        return
    try:
        with open(log_path, "rb") as source:
            size = os.path.getsize(log_path)
            if size > 12000:
                source.seek(-12000, os.SEEK_END)
            content = source.read().decode("utf-8", errors="replace")
        content = content[-3400:] or "(Log is empty)"
        answer_callback(call, "📜 Log loaded.")
        markup = types.InlineKeyboardMarkup(row_width=2)
        log_name = f"{os.path.splitext(file_name)[0]}.log"
        markup.row(
            ibutton(
                "📥 Download Log",
                callback_data=f"l|view|{owner_id}|{file_ref(log_name)}",
                style=PRIMARY,
            ),
            ibutton("Back to Files", callback_data="check_files", style=DANGER),
        )
        bot.send_message(
            call.message.chat.id,
            f"📜 <b>Latest log for {html.escape(file_name)}</b>\n"
            f"<pre>{html.escape(content)}</pre>",
            parse_mode="HTML",
            reply_markup=markup,
        )
    except Exception as exc:
        logger.exception("Could not read log preview")
        answer_callback(call, f"Log error: {exc}", alert=True)


def handle_dynamic_file_callback(call: Any) -> None:
    try:
        _, action, owner_text, reference = call.data.split("|", 3)
        owner_id = int(owner_text)
    except (ValueError, AttributeError):
        answer_callback(call, "Invalid file action.", alert=True)
        return

    requester_id = call.from_user.id
    if requester_id != owner_id and requester_id not in admin_ids:
        answer_callback(call, "⚠️ Permission denied.", alert=True)
        return
    resolved = resolve_user_file(owner_id, reference)
    if not resolved:
        answer_callback(call, "This file record no longer exists.", alert=True)
        return
    file_name, file_type = resolved
    folder = get_user_folder(owner_id)
    script_path = os.path.join(folder, file_name)

    if action == "open":
        answer_callback(call)
        edit_file_control(call, owner_id, file_name, file_type)
        return

    if action == "start":
        if not has_active_subscription(owner_id):
            answer_callback(
                call,
                "Active subscription required. Ask an administrator for permission.",
                alert=True,
            )
            return
        if not os.path.isfile(script_path):
            remove_user_file_db(owner_id, file_name)
            answer_callback(call, "File is missing. Please upload it again.", alert=True)
            return
        if is_bot_running(owner_id, file_name):
            answer_callback(call, "Script is already running.", alert=True)
            edit_file_control(call, owner_id, file_name, file_type)
            return
        answer_callback(call, f"Starting {file_name}...")
        bot.edit_message_text(
            f"⏳ Starting <code>{html.escape(file_name)}</code>...",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_control_buttons(owner_id, file_name, False),
            parse_mode="HTML",
        )
        queue_script_start(script_path, owner_id, folder, file_name, file_type, call.message)
        return

    if action == "stop":
        if stop_managed_script(owner_id, file_name):
            answer_callback(call, f"Stopped {file_name}.")
        else:
            answer_callback(call, "Script was already stopped.")
        edit_file_control(call, owner_id, file_name, file_type)
        return

    if action == "restart":
        if not has_active_subscription(owner_id):
            stop_managed_script(owner_id, file_name)
            answer_callback(
                call,
                "Subscription inactive. The script cannot be restarted.",
                alert=True,
            )
            edit_file_control(call, owner_id, file_name, file_type)
            return
        answer_callback(call, f"Restarting {file_name}...")
        stop_managed_script(owner_id, file_name)
        if not os.path.isfile(script_path):
            remove_user_file_db(owner_id, file_name)
            bot.edit_message_text(
                "❌ Script file is missing. Upload it again.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_back_to_main(),
            )
            return
        bot.edit_message_text(
            f"⏳ Restarting <code>{html.escape(file_name)}</code>...",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_control_buttons(owner_id, file_name, False),
            parse_mode="HTML",
        )
        queue_script_start(script_path, owner_id, folder, file_name, file_type, call.message)
        return

    if action == "delete":
        answer_callback(call, f"Deleting {file_name}...")
        stop_managed_script(owner_id, file_name)
        targets = [
            script_path,
            os.path.join(folder, f"{os.path.splitext(file_name)[0]}.log"),
        ]
        errors: List[str] = []
        for target in targets:
            try:
                if os.path.isfile(target) or os.path.islink(target):
                    os.remove(target)
            except OSError as exc:
                errors.append(str(exc))
        remove_persisted_file(owner_id, file_name)
        remove_persisted_file(
            owner_id, f"{os.path.splitext(file_name)[0]}.log"
        )
        remove_user_file_db(owner_id, file_name)
        result = f"🗑 Deleted <code>{html.escape(file_name)}</code>."
        if errors:
            result += "\n⚠️ Some associated data could not be removed."
        bot.edit_message_text(
            result,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=create_back_to_main(),
        )
        return

    if action == "logs":
        send_log_preview(call, owner_id, file_name)
        return

    if action == "sendcmd":
        if not is_bot_running(owner_id, file_name):
            answer_callback(call, "Script is no longer running.", alert=True)
            return
        answer_callback(call, f"Selected {file_name}.")
        prompt = bot.send_message(
            call.message.chat.id,
            f"📝 Send the command for {file_name}.\n/cancel to abort.",
        )
        bot.register_next_step_handler(
            prompt, lambda message: process_send_command(message, owner_id, file_name)
        )
        return

    answer_callback(call, "Unknown file action.", alert=True)


def handle_log_callback(call: Any) -> None:
    try:
        _, action, owner_text, reference = call.data.split("|", 3)
        owner_id = int(owner_text)
    except (ValueError, AttributeError):
        answer_callback(call, "Invalid log action.", alert=True)
        return
    if action != "view":
        answer_callback(call, "Unknown log action.", alert=True)
        return
    if call.from_user.id != owner_id and call.from_user.id not in admin_ids:
        answer_callback(call, "⚠️ Permission denied.", alert=True)
        return
    log_name = resolve_log_file(owner_id, reference)
    if not log_name:
        answer_callback(call, "Log file not found.", alert=True)
        return
    answer_callback(call, "Sending log...")
    send_log_document(call.message.chat.id, owner_id, log_name)


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: Any) -> None:
    global bot_locked
    user_id = call.from_user.id
    data = call.data or ""
    logger.info("Callback from %s: %s", user_id, data)

    if data.startswith("f|"):
        if not ensure_access(user_id, call.message.chat.id):
            answer_callback(call, "Access check failed.", alert=True)
            return
        handle_dynamic_file_callback(call)
        return
    if data.startswith("l|"):
        handle_log_callback(call)
        return
    if data != "force_join_check" and not require_force_join(call.message.chat.id, user_id):
        answer_callback(call, "আগে channel-এ join করুন.", alert=True)
        return

    if bot_locked and user_id not in admin_ids and data not in {
        "speed",
        "stats",
        "developer",
        "back_to_main",
    }:
        answer_callback(call, "⚠️ Bot is locked by an administrator.", alert=True)
        return

    try:
        if data == "upload":
            if not ensure_access(user_id, call.message.chat.id):
                answer_callback(call)
                return
            if user_id not in admin_ids and not has_active_subscription(user_id):
                answer_callback(call)
                bot.send_message(
                    call.message.chat.id,
                    "🔒 Hosting permission প্রয়োজন\n\n"
                    "Bot host করার আগে একজন Admin-এর কাছ থেকে permission নিন।",
                    reply_markup=create_user_subscription_menu(),
                )
                return
            limit = get_user_file_limit(user_id)
            current = get_user_file_count(user_id)
            if current >= limit:
                answer_callback(
                    call,
                    f"File limit reached ({current}/{display_limit(limit)}).",
                    alert=True,
                )
            else:
                answer_callback(call)
                prompt = bot.send_message(
                    call.message.chat.id,
                    "📤 File Upload করুন 🚀\n\n"
                    "✅ শুধুমাত্র \".py\", \".js\" অথবা \".zip\" file গ্রহণ করা হবে।\n"
                    "📦 আপনার script/project পাঠান এবং সহজেই Host & Run করুন।\n\n"
                    "❌ Unsupported file format পাঠালে তা গ্রহণ করা হবে না।",
                    reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                        types.KeyboardButton("Cancel Upload")
                    ),
                )
                with STATE_LOCK:
                    pending_upload_prompts[user_id] = (
                        call.message.chat.id,
                        prompt.message_id,
                    )

        elif data == "check_files":
            answer_callback(call)
            show_file_list(call.message.chat.id, user_id, call.message.message_id)

        elif data == "speed":
            started = time.time()
            answer_callback(call)
            bot.edit_message_text(
                speed_text(user_id, started),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_main_menu_inline(user_id),
            )

        elif data == "stats":
            answer_callback(call)
            logic_statistics(call.message, actual_user_id=user_id)

        elif data == "developer":
            answer_callback(call)
            bot.edit_message_text(
                developer_text(),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=create_developer_menu(),
            )

        elif data == "back_to_main":
            answer_callback(call)
            status, expiry_info = user_status(user_id)
            bot.edit_message_text(
                f"〽️ <b>Main Menu</b>\n\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"🔰 Status: {status}{expiry_info}\n"
                f"📁 Files: {get_user_file_count(user_id)} / "
                f"{display_limit(get_user_file_limit(user_id))}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=create_main_menu_inline(user_id),
            )

        elif data == "send_command":
            answer_callback(call)
            bot.edit_message_text(
                "📤 Send Command Options",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_send_command_menu(),
            )

        elif data == "send_to_process":
            answer_callback(call)
            show_running_script_selector(call.message.chat.id, user_id)

        elif data == "view_all_logs":
            answer_callback(call)
            show_all_logs(call.message.chat.id, user_id)

        elif data == "ask_admin_permission":
            answer_callback(call)
            bot.send_message(
                call.message.chat.id,
                "🔒 Admin permission required.\n"
                "আপনার User ID একজন Admin-কে পাঠান: "
                f"<code>{user_id}</code>",
                parse_mode="HTML",
            )

        elif data == "subscription":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                bot.edit_message_text(
                    "💳 Subscription Management",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=create_subscription_menu(),
                )

        elif data == "lock_bot":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                bot_locked = True
                save_setting("bot_locked", "1")
                answer_callback(call, "🔒 Bot locked.")
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=create_main_menu_inline(user_id),
                )

        elif data == "unlock_bot":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                bot_locked = False
                save_setting("bot_locked", "0")
                answer_callback(call, "🔓 Bot unlocked.")
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=create_main_menu_inline(user_id),
                )

        elif data == "run_all_scripts":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call, "Run-all request accepted.")
                logic_run_all_scripts(call)

        elif data == "broadcast":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                prompt = bot.send_message(
                    call.message.chat.id,
                    "📢 Send one message or media item.\n/cancel to abort.",
                )
                bot.register_next_step_handler(prompt, process_broadcast_message)

        elif data.startswith("confirm_broadcast|"):
            requested_admin = int(data.split("|", 1)[1])
            if user_id != requested_admin or user_id not in admin_ids:
                answer_callback(call, "Not authorized.", alert=True)
            else:
                with STATE_LOCK:
                    source = pending_broadcasts.pop(user_id, None)
                if not source:
                    answer_callback(call, "Broadcast request expired.", alert=True)
                else:
                    answer_callback(call, "🚀 Broadcast started.")
                    bot.edit_message_text(
                        f"📢 Broadcasting to {len(active_users)} user(s)...",
                        call.message.chat.id,
                        call.message.message_id,
                    )
                    threading.Thread(
                        target=execute_broadcast,
                        args=(source[0], source[1], call.message.chat.id),
                        name="broadcast",
                        daemon=True,
                    ).start()

        elif data.startswith("cancel_broadcast|"):
            requested_admin = int(data.split("|", 1)[1])
            if user_id != requested_admin:
                answer_callback(call, "Not authorized.", alert=True)
            else:
                with STATE_LOCK:
                    pending_broadcasts.pop(user_id, None)
                answer_callback(call, "Broadcast cancelled.")
                bot.edit_message_text(
                    "❌ Broadcast cancelled.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=create_back_to_main(),
                )

        elif data == "admin_panel":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                bot.edit_message_text(
                    "👑 Admin Panel",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=create_admin_panel(),
                )

        elif data == "developer_settings":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                bot.edit_message_text(
                    developer_settings_text(),
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=create_developer_settings_menu(),
                )

        elif data.startswith("developer_change_"):
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                field = data.removeprefix("developer_change_")
                if field not in DEVELOPER_SETTING_LABELS:
                    answer_callback(call, "Unknown developer setting.", alert=True)
                else:
                    answer_callback(call)
                    prompt_developer_setting(call.message.chat.id, field)

        elif data == "developer_preview":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                bot.edit_message_text(
                    developer_text(),
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=create_developer_menu("developer_settings"),
                )

        elif data == "developer_reset_confirm":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                bot.edit_message_text(
                    "⚠️ Reset all developer information to its original defaults?",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=create_developer_reset_menu(),
                )

        elif data == "developer_reset":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                reset_developer_settings()
                answer_callback(call, "Developer information reset.")
                bot.edit_message_text(
                    "✅ Developer information restored to defaults.\n\n"
                    + developer_settings_text(),
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=create_developer_settings_menu(),
                )

        elif data == "add_admin":
            if user_id != OWNER_ID:
                answer_callback(call, "Owner permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_add_admin(call.message.chat.id)

        elif data == "remove_admin":
            if user_id != OWNER_ID:
                answer_callback(call, "Owner permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_remove_admin(call.message.chat.id)

        elif data == "list_admins":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                lines = [
                    f"• <code>{admin_id}</code>{' (Owner)' if admin_id == OWNER_ID else ''}"
                    for admin_id in sorted(admin_ids)
                ]
                bot.edit_message_text(
                    "👑 <b>Current Admins</b>\n\n" + "\n".join(lines),
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                    reply_markup=create_admin_panel(),
                )

        elif data == "force_join_add":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_force_join(call.message.chat.id)

        elif data == "force_join_remove":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_remove_force_join(call.message.chat.id)

        elif data == "force_join_toggle":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                logic_toggle_force_join(call.message, actor_id=user_id)
                bot.send_message(
                    call.message.chat.id,
                    "👑 Admin Panel",
                    reply_markup=create_admin_panel(),
                )

        elif data == "force_join_check":
            if user_id in admin_ids or user_has_joined_force_channel(user_id):
                answer_callback(call, "Verified ✅")
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                send_welcome_for_user(call.message.chat.id, call.from_user)
            else:
                answer_callback(call, "আগে channel-এ join করুন.", alert=True)

        elif data == "add_subscription":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_add_subscription(call.message.chat.id)

        elif data == "replace_subscription":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_replace_subscription(call.message.chat.id)

        elif data == "remove_subscription":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_remove_subscription(call.message.chat.id)

        elif data == "check_subscription":
            if user_id not in admin_ids:
                answer_callback(call, "Admin permission required.", alert=True)
            else:
                answer_callback(call)
                prompt_check_subscription(call.message.chat.id)

        else:
            answer_callback(call, "Unknown action.", alert=True)

    except telebot.apihelper.ApiTelegramException as exc:
        if "message is not modified" not in str(exc).lower():
            logger.exception("Telegram callback error for %s", data)
            answer_callback(call, "Telegram request failed.", alert=True)
    except Exception as exc:
        logger.exception("Callback error for %s", data)
        answer_callback(call, f"Action failed: {exc}", alert=True)


# ---------------------------------------------------------------------------
# Shutdown and main loop
# ---------------------------------------------------------------------------


def cleanup() -> None:
    logger.warning("Shutting down; stopping managed scripts...")
    SHUTDOWN_EVENT.set()
    with STATE_LOCK:
        snapshot = list(bot_scripts.items())
        bot_scripts.clear()
        pending_scripts.clear()
    for key, info in snapshot:
        try:
            kill_process_tree(info)
            persist_user_folder(key[0])
            logger.info("Stopped %s", key)
        except Exception:
            logger.exception("Could not stop %s during shutdown", key)


atexit.register(cleanup)


def main() -> None:
    logger.info("=" * 48)
    logger.info("Telegram hosting bot is starting")
    logger.info("Python: %s", sys.version.split()[0])
    logger.info("Base directory: %s", BASE_DIR)
    logger.info("Owner ID: %s", OWNER_ID)
    logger.info("Admins: %s", sorted(admin_ids))
    logger.info("Button styles: primary + danger")
    logger.info("=" * 48)
    keep_alive()
    threading.Thread(
        target=subscription_watchdog,
        name="subscription-watchdog",
        daemon=True,
    ).start()
    enforce_subscription_permissions()

    while True:
        try:
            bot.infinity_polling(
                logger_level=logging.INFO,
                timeout=60,
                long_polling_timeout=30,
                skip_pending=True,
            )
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
            break
        except requests.exceptions.ReadTimeout:
            logger.warning("Polling read timeout; retrying in 5 seconds.")
            time.sleep(5)
        except requests.exceptions.ConnectionError as exc:
            logger.warning("Polling connection error: %s; retrying in 15 seconds.", exc)
            time.sleep(15)
        except Exception:
            logger.exception("Polling stopped unexpectedly; retrying in 20 seconds.")
            time.sleep(20)


if __name__ == "__main__":
    main()