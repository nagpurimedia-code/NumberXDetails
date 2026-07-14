# FKS OSINT BOT FREE SRC ANY PROBLEM CONTACT ME
# Edit Code Carefully Replace Your Bot Name IN FKS
# Must See Readme.txt File In Zip For Complete Bot Instructions 
# Requirements:
# pip install python-telegram-bot==20.7 requests
# Replace BOT_TOKEN with your bot token, then run: python bot.py

import os
import json
import time
import random
import string
import logging
import requests
from typing import Union, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, Message
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# ---------------- CONFIG ----------------
BOT_TOKEN = "8759960516:AAEWakdCpP7J7sSNXd6PtL34-l78vMF5zL4"
BOT_USERNAME = "SearchPortalBot"        # provided by you (no @)
BUY_CREDITS_USERNAME = "ColdenMinj" # contact username (no @)
ADMIN_IDS = [8523360387]               # admin numeric IDs

# core settings
REFERRAL_BONUS = 2
INITIAL_CREDITS = 2
SEARCH_COST = 1
BACKUP_COOLDOWN = 300
DAILY_BONUS_AMOUNT = 2
DAILY_SECONDS = 86400
GENERATED_CODE_LENGTH = 8

# data files
USERS_FILE = "users.json"
CODES_FILE = "redeem_codes.json"
BACKUP_META = "backup_meta.json"

# API endpoints (as provided)
PHONE_IN_API = "https://yourapi.com/phone_in?number={num}"
PHONE_PK_API = "https://yourapi.com/phone_pk?number={num}"
AADHAAR_API = "https://yourapi.com/aadhaar?id={aadhaar}"
FAMILY_AADHAAR_API = "https://yourapi.com/family?id={aadhaar}"
CNIC_API = "https://yourapi.com/cnic?id={cnic}"
RC_API = "https://yourapi.com/rc?rc={rc}"
VEHICLE_API = "https://yourapi.com/vehicle?rc={rc}"
IFSC_API = "https://yourapi.com/ifsc?ifsc={ifsc}"
UPI_API = "https://yourapi.com/upi?id={upi}"

MAINTENANCE_TEXT = "⚙️ This feature is under maintenance. Credits not deducted."

# ---------------- logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fks-osint-bot")

# ---------------- helpers for JSON files ----------------
def read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"read_json error {path}: {e}")
        return {}

def write_json(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"write_json error {path}: {e}")

def ensure_files_exist():
    for fn in [USERS_FILE, CODES_FILE, BACKUP_META]:
        if not os.path.exists(fn):
            write_json(fn, {})

# ---------------- misc helpers ----------------
def gen_code(length: int = GENERATED_CODE_LENGTH) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def http_get(url: str, timeout: int = 12) -> Optional[requests.Response]:
    headers = {"User-Agent": "FKS-OSINT-BOT/8.8.3"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.debug(f"http_get error for {url}: {e}")
        return None

# ---------------- user data helpers ----------------
def ensure_user(uid: str) -> dict:
    users = read_json(USERS_FILE)
    if uid not in users:
        users[uid] = {
            "credits": INITIAL_CREDITS,
            "referrals": 0,
            "banned": False,
            "referred_by": None,
            "last_daily": 0
        }
        write_json(USERS_FILE, users)
    # make sure keys exist
    changed = False
    if "referred_by" not in users[uid]:
        users[uid]["referred_by"] = None; changed = True
    if "last_daily" not in users[uid]:
        users[uid]["last_daily"] = 0; changed = True
    if changed:
        write_json(USERS_FILE, users)
    return users

def is_banned(uid: str) -> bool:
    users = read_json(USERS_FILE)
    return users.get(uid, {}).get("banned", False)

# ---------------- admin check (robust) ----------------
def is_admin_user(tuser) -> bool:
    if tuser is None:
        return False
    try:
        if int(tuser.id) in [int(x) for x in ADMIN_IDS]:
            return True
    except Exception:
        pass
    try:
        if tuser.username and tuser.username.lower() == str(BUY_CREDITS_USERNAME).lower():
            return True
    except Exception:
        pass
    return False

# ---------------- scrub copyright/owner fields ----------------
def scrub_response(obj):
    """Recursively remove developer/copyright/owner fields and values."""
    block_keys = [
        "developer", "developer_message", "developer_tag",
        "api_by", "api_owner", "owner", "source", "author", "dev", "creator", "footer", "tag"
    ]

    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            kl = k.lower().strip()
            # skip keys that contain block words
            if any(b in kl for b in block_keys):
                continue
            # skip short string values that look like developer credits
            if isinstance(v, str):
                lowv = v.lower()
                if any(b in lowv for b in block_keys):
                    continue
            clean[k] = scrub_response(v)
        return clean

    elif isinstance(obj, list):
        return [scrub_response(x) for x in obj]

    else:
        return obj

# ---------------- backup ----------------
def send_backup_to_admins() -> bool:
    meta = read_json(BACKUP_META)
    now = int(time.time())
    if now - meta.get("last", 0) < BACKUP_COOLDOWN:
        logger.info("backup cooldown active")
        return False
    try:
        bot = Bot(token=BOT_TOKEN)
        if os.path.exists(USERS_FILE):
            for admin_id in ADMIN_IDS:
                try:
                    with open(USERS_FILE, "rb") as f:
                        bot.send_document(chat_id=int(admin_id), document=f, filename="users.json", caption="📦 FKS OSINT - users backup")
                except Exception as e:
                    logger.warning(f"send_backup to {admin_id} failed: {e}")
        meta["last"] = now
        write_json(BACKUP_META, meta)
        return True
    except Exception as e:
        logger.warning(f"backup failed: {e}")
        return False

# ---------------- Styled UI text ----------------
WELCOME_TEXT = (
    "👋 *𝗛𝗶 {name} — 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗙𝗞𝗦 𝗢𝗦𝗜𝗡𝗧 𝗕𝗢𝗧 ⚡*\n\n"
    "💡 *Educational & lawful OSINT use only.*\n"
    "📚 Use findings responsibly — do not harass, doxx, or commit illegal acts We Are Not Responsible For Anything Illigal.\n\n"
    "🔐 *Credits:* Each search costs *1 credit*.\n"
    "🎁 *Daily Bonus:* Claim once per 24 hours.\n"
    "🎯 *Referral:* Earn credits when a new user joins using your link.\n\n"
    "Need help? Contact @{owner}\n"
).format(name="{name}", owner=BUY_CREDITS_USERNAME)

HELP_TEXT = (
    "📘 *FKS OSINT Assistant — Help Center*\n\n"
    "🔍 *Available Searches:*\n"
    "• Phone (India / Pakistan)\n"
    "• Aadhaar (family details when available)\n"
    "• CNIC\n"
    "• IFSC\n"
    "• Vehicle / RC\n"
    "• UPI Info\n\n"
    "💳 *Credits:* Each search costs *1 credit*. If no result, credit is refunded.\n"
    "🎁 *Daily Bonus:* Claim once per 24 hours for free credits.\n"
    "🎯 *Referral:* Share your link. You earn credits when a *new* user joins using your link.\n\n"
    "Contact @{owner} for support."
).format(owner=BUY_CREDITS_USERNAME)

CREDIT_DEDUCTED_MSG = (
    "⚠️ *Credits deducted by Admin*\n\n"
    "• Amount: *-{amt}*\n"
    "• New Balance: *{bal}*\n\n"
    "If you think this is an error, contact @{owner}."
)

CREDIT_ADDED_MSG = (
    "💰 *Credits added by Admin*\n\n"
    "• Amount: *+{amt}*\n"
    "• New Balance: *{bal}*\n\n"
    "Enjoy your searches! Contact @{owner} for help."
)

REFERRAL_EARNED_MSG = "🎉 *New user joined with your referral!* You earned *{amt}* credits. Thank you!"

DAILY_CLAIMED_MSG = "🎁 *You claimed your Daily Bonus!* +{amt} credits."

ERROR_REFUND_MSG = "⚠️ *Error fetching data.* Credits refunded."

# ---------------- Keyboards ----------------
def main_menu_keyboard():
    buy_url = f"https://t.me/{BUY_CREDITS_USERNAME}"
    kb = [
        [InlineKeyboardButton("Phone 🇮🇳", callback_data="phone_in"),
         InlineKeyboardButton("Phone 🇵🇰", callback_data="phone_pk"),
         InlineKeyboardButton("Aadhaar 🆔", callback_data="aadhaar")],
        [InlineKeyboardButton("CNIC 🇵🇰", callback_data="cnic"),
         InlineKeyboardButton("IFSC 🏦", callback_data="ifsc"),
         InlineKeyboardButton("Vehicle/RC 🚗", callback_data="vehicle_rc")],
        [InlineKeyboardButton("🔗 UPI Info", callback_data="upi"),
         InlineKeyboardButton("🎁 Redeem", callback_data="redeem"),
         InlineKeyboardButton("🎯 Referral", callback_data="referral")],
        [InlineKeyboardButton("💰 Credits", callback_data="credits"),
         InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("💳 Buy Credits", url=buy_url)]
    ]
    return InlineKeyboardMarkup(kb)

def back_to_menu_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="to_menu")]])

def admin_panel_kb():
    kb = [
        [InlineKeyboardButton("📊 User Stats", callback_data="admin_stats"),
         InlineKeyboardButton("🎁 Generate Codes", callback_data="admin_gen_codes"),
         InlineKeyboardButton("🔎 User Info", callback_data="admin_user_info")],
        [InlineKeyboardButton("📦 Force Backup", callback_data="admin_backup"),
         InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
         InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"),
         InlineKeyboardButton("➖ Deduct -1", callback_data="admin_deduct")],
        [InlineKeyboardButton("➖➖ Custom Deduct", callback_data="admin_deduct_custom"),
         InlineKeyboardButton("➕ Add Credits", callback_data="admin_add_credits"),
         InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="to_menu")]
    ]
    return InlineKeyboardMarkup(kb)

def admin_action_back_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_panel"),
         InlineKeyboardButton("🏠 Back to Main Menu", callback_data="to_menu")]
    ])

# ---------------- Commands ----------------
async def start_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    uid = str(user.id)
    args = context.args or []

    # check if user already existed before calling ensure_user
    users_before = read_json(USERS_FILE)
    user_existed_before = uid in users_before

    ensure_user(uid)
    if is_banned(uid):
        await update.message.reply_text("❌ *You are banned from using this bot.*", parse_mode="Markdown")
        return

    # Referral: only credit referrer once AND only if the user is NEW (joined using the link)
    if args:
        ref = args[0]
        try:
            ref_id = str(int(ref))
        except:
            ref_id = None
        # only process referral if:
        # 1) ref_id is valid and not self
        # 2) this user did NOT exist before (i.e. truly a new join)
        # 3) referred_by is still None (safety)
        if ref_id and ref_id != uid and not user_existed_before:
            users = read_json(USERS_FILE)
            if users.get(uid, {}).get("referred_by") is None:
                users[uid]["referred_by"] = ref_id
                write_json(USERS_FILE, users)
                if ref_id in users:
                    users[ref_id]["credits"] = users[ref_id].get("credits", 0) + REFERRAL_BONUS
                    users[ref_id]["referrals"] = users[ref_id].get("referrals", 0) + 1
                    write_json(USERS_FILE, users)
                    try:
                        await context.bot.send_message(int(ref_id), REFERRAL_EARNED_MSG.format(amt=REFERRAL_BONUS), parse_mode="Markdown")
                    except Exception:
                        logger.debug("could not DM referrer")

    # Welcome (styled)
    wtext = WELCOME_TEXT.format(name=user.first_name)
    await update.message.reply_text(wtext, parse_mode="Markdown")
    await update.message.reply_text("✅ *Select an option below:*", parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def menu_cmd(update: Update, context: CallbackContext):
    await update.message.reply_text("✅ *Select an option below:*", parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def admin_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not is_admin_user(user):
        await update.message.reply_text("❌ *You are not authorized to use admin commands.*", parse_mode="Markdown")
        return
    await update.message.reply_text("⚙️ *Admin Panel*", parse_mode="Markdown", reply_markup=admin_panel_kb())

# ---------------- Callbacks ----------------
async def to_menu_callback(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    try:
        await q.message.delete()
    except:
        pass
    await q.message.reply_text("✅ *Select an option below:*", parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def help_callback(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    await q.message.reply_text(HELP_TEXT, parse_mode="Markdown", reply_markup=back_to_menu_kb())

async def referral_callback(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    uid = str(q.from_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    text = (f"🎯 *Invite & Earn!* \n\nShare this link:\n`{link}`\n\nWhen a *new* user joins with your link, you earn *{REFERRAL_BONUS} credits*.")
    await q.message.reply_text(text, parse_mode="Markdown", reply_markup=back_to_menu_kb())

async def daily_bonus_callback(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    uid = str(q.from_user.id)
    users = ensure_user(uid)
    now = int(time.time())
    if now - users[uid].get("last_daily", 0) >= DAILY_SECONDS:
        users[uid]["credits"] = users[uid].get("credits", 0) + DAILY_BONUS_AMOUNT
        users[uid]["last_daily"] = now
        write_json(USERS_FILE, users)
        await q.message.reply_text(DAILY_CLAIMED_MSG.format(amt=DAILY_BONUS_AMOUNT), parse_mode="Markdown")
    else:
        await q.message.reply_text("⏰ *You already claimed your daily bonus today.* Try again tomorrow.", parse_mode="Markdown")
    await q.message.reply_text("🔙 Back to Menu", reply_markup=back_to_menu_kb())

# ---------------- Generic callback handler ----------------
async def generic_callback(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    data = q.data

    if data in ("phone_in", "phone_pk", "aadhaar", "cnic", "ifsc", "vehicle_rc", "upi"):
        context.user_data["mode"] = data
        label = "RC/Vehicle" if data == "vehicle_rc" else data.upper()
        if data == "upi": label = "UPI ID (e.g. 9693331989@ybl)"
        await q.message.reply_text(f"➡️ *Send the {label} to search now.*", parse_mode="Markdown")
        return

    if data == "redeem":
        context.user_data["mode"] = "redeem_code"
        await q.message.reply_text("🎁 *Send your redeem code now.*", parse_mode="Markdown")
        return

    if data == "credits":
        users = read_json(USERS_FILE)
        cr = users.get(str(q.from_user.id), {}).get("credits", 0)
        if is_admin_user(q.from_user):
            await q.message.reply_text("💳 *Credits:* Unlimited (Admin)", parse_mode="Markdown")
        else:
            await q.message.reply_text(f"💳 *Your Credits:* *{cr}*", parse_mode="Markdown")
        return

    if data == "referral":
        await referral_callback(update, context); return
    if data == "help":
        await help_callback(update, context); return
    if data == "daily_bonus":
        await daily_bonus_callback(update, context); return
    if data == "admin_panel":
        if not is_admin_user(q.from_user):
            await q.message.reply_text("❌ *You are not authorized to use admin commands.*", parse_mode="Markdown")
            return
        await q.message.reply_text("⚙️ *Admin Panel*", parse_mode="Markdown", reply_markup=admin_panel_kb())
        return

    await q.message.reply_text("⚠️ *Unknown action.*", parse_mode="Markdown")

# ---------------- Message handler (search + admin states) ----------------
async def message_handler(update: Update, context: CallbackContext):
    user = update.effective_user; uid = str(user.id)
    ensure_user(uid)

    # admin interactive state machine
    admin_state = context.user_data.get("admin_state")
    if admin_state:
        if not is_admin_user(user):
            await update.message.reply_text("❌ *You are not authorized for admin actions.*", parse_mode="Markdown")
            context.user_data.pop("admin_state", None)
            return
        text = update.message.text.strip()

        # BAN
        if admin_state == "ban_waiting":
            try:
                target = str(int(text)); users = read_json(USERS_FILE)
                if target not in users:
                    await update.message.reply_text("❌ *User not found.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                else:
                    users[target]["banned"] = True; write_json(USERS_FILE, users)
                    await update.message.reply_text(f"🚫 *User `{target}` has been BANNED.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                    try: await context.bot.send_message(int(target), "🚫 You have been banned by the admin.")
                    except: pass
            except:
                await update.message.reply_text("❌ *Invalid user id.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            context.user_data.pop("admin_state", None); return

        # UNBAN
        if admin_state == "unban_waiting":
            try:
                target = str(int(text)); users = read_json(USERS_FILE)
                if target not in users:
                    await update.message.reply_text("❌ *User not found.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                else:
                    users[target]["banned"] = False; write_json(USERS_FILE, users)
                    await update.message.reply_text(f"✅ *User `{target}` has been UNBANNED.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                    try: await context.bot.send_message(int(target), "✅ You have been unbanned by the admin.")
                    except: pass
            except:
                await update.message.reply_text("❌ *Invalid user id.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            context.user_data.pop("admin_state", None); return

        # DEDUCT -1
        if admin_state == "deduct_waiting":
            try:
                target = str(int(text)); users = read_json(USERS_FILE)
                if target not in users:
                    await update.message.reply_text("❌ *User not found.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                else:
                    users[target]["credits"] = max(0, users[target].get("credits", 0) - 1)
                    write_json(USERS_FILE, users)
                    newbal = users[target]["credits"]
                    await update.message.reply_text(f"➖ *Deducted 1 credit* from `{target}`. New balance: *{newbal}*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            except:
                await update.message.reply_text("❌ *Invalid user id.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            context.user_data.pop("admin_state", None); return

        # Custom Deduct
        if admin_state == "deduct_custom_waiting":
            try:
                parts = text.split()
                if len(parts) < 2:
                    await update.message.reply_text("❌ *Please provide user ID and amount. Example:* `123456789 5`", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                    context.user_data.pop("admin_state", None); return
                target = str(int(parts[0]))
                amount = int(parts[1])
                users = read_json(USERS_FILE)
                if target not in users:
                    await update.message.reply_text("❌ *User not found.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                else:
                    users[target]["credits"] = max(0, users[target].get("credits", 0) - amount)
                    write_json(USERS_FILE, users)
                    newbal = users[target]["credits"]
                    await update.message.reply_text(f"➖ *Deducted {amount} credits* from `{target}`. New balance: *{newbal}*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            except:
                await update.message.reply_text("❌ *Invalid input. Use:* `user_id amount`", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            context.user_data.pop("admin_state", None); return

        # Add Credits
        if admin_state == "add_credits_waiting":
            try:
                parts = text.split()
                if len(parts) < 2:
                    await update.message.reply_text("❌ *Please provide user ID and amount. Example:* `123456789 10`", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                    context.user_data.pop("admin_state", None); return
                target = str(int(parts[0]))
                amount = int(parts[1])
                users = read_json(USERS_FILE)
                if target not in users:
                    await update.message.reply_text("❌ *User not found.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                else:
                    users[target]["credits"] = users[target].get("credits", 0) + amount
                    write_json(USERS_FILE, users)
                    newbal = users[target]["credits"]
                    await update.message.reply_text(f"➕ *Added {amount} credits* to `{target}`. New balance: *{newbal}*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            except:
                await update.message.reply_text("❌ *Invalid input. Use:* `user_id amount`", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            context.user_data.pop("admin_state", None); return

        # Broadcast
        if admin_state == "broadcast_waiting":
            users = read_json(USERS_FILE)
            sent = 0
            for uid in users:
                try:
                    await context.bot.send_message(int(uid), f"📢 *Admin Broadcast*\n\n{text}", parse_mode="Markdown")
                    sent += 1
                    time.sleep(0.05)
                except:
                    pass
            await update.message.reply_text(f"✅ *Broadcast sent to {sent} users.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            context.user_data.pop("admin_state", None); return

        # Generate Codes
        if admin_state == "gen_codes_waiting":
            try:
                count = int(text)
                if count < 1 or count > 100:
                    await update.message.reply_text("❌ *Please provide a number between 1 and 100.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
                    context.user_data.pop("admin_state", None); return
                codes = read_json(CODES_FILE)
                generated = []
                for _ in range(count):
                    code = gen_code()
                    codes[code] = {"used": False}
                    generated.append(code)
                write_json(CODES_FILE, codes)
                await update.message.reply_text(f"✅ *Generated {count} redeem codes:*\n`{' '.join(generated)}`", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            except:
                await update.message.reply_text("❌ *Invalid number.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
            context.user_data.pop("admin_state", None); return

        context.user_data.pop("admin_state", None)
        return

    # ---------- Normal user message handling ----------
    mode = context.user_data.get("mode")
    
    # Redeem code
    if mode == "redeem_code":
        code = update.message.text.strip().upper()
        codes = read_json(CODES_FILE)
        if code in codes and not codes[code]["used"]:
            codes[code]["used"] = True
            write_json(CODES_FILE, codes)
            users = read_json(USERS_FILE)
            users[uid]["credits"] = users[uid].get("credits", 0) + 1
            write_json(USERS_FILE, users)
            await update.message.reply_text("🎁 *Code redeemed! You earned 1 credit.*", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *Invalid or already used code.*", parse_mode="Markdown")
        context.user_data.pop("mode", None)
        await update.message.reply_text("🔙 Back to Menu", reply_markup=back_to_menu_kb())
        return

    # Search mode
    if mode in ("phone_in", "phone_pk", "aadhaar", "cnic", "ifsc", "vehicle_rc", "upi"):
        query = update.message.text.strip()
        if not query:
            await update.message.reply_text("❌ *Please provide a valid query.*", parse_mode="Markdown")
            return

        # Check credits (admins unlimited)
        if not is_admin_user(user):
            users = read_json(USERS_FILE)
            if users[uid].get("credits", 0) < SEARCH_COST:
                await update.message.reply_text("❌ *Not enough credits!* Use /start to get free credits or contact @{owner}".format(owner=BUY_CREDITS_USERNAME), parse_mode="Markdown")
                return

        # Map mode to API
        api_map = {
            "phone_in": PHONE_IN_API.format(num=query),
            "phone_pk": PHONE_PK_API.format(num=query),
            "aadhaar": AADHAAR_API.format(aadhaar=query),
            "cnic": CNIC_API.format(cnic=query),
            "ifsc": IFSC_API.format(ifsc=query),
            "vehicle_rc": VEHICLE_API.format(rc=query),
            "upi": UPI_API.format(id=query)
        }
        url = api_map.get(mode)
        if not url:
            await update.message.reply_text("❌ *Invalid search mode.*", parse_mode="Markdown")
            return

        # Deduct credit (unless admin)
        if not is_admin_user(user):
            users = read_json(USERS_FILE)
            users[uid]["credits"] -= 1
            write_json(USERS_FILE, users)

        # Call API
        try:
            resp = http_get(url)
            if resp and resp.status_code == 200:
                data = resp.json()
                # Scrub developer info
                clean = scrub_response(data)
                formatted = json.dumps(clean, indent=2, ensure_ascii=False)
                if len(formatted) > 4000:
                    formatted = formatted[:4000] + "\n... (truncated)"
                await update.message.reply_text(f"📊 *Search Result*\n```json\n{formatted}\n```", parse_mode="Markdown")
            else:
                # Refund credit if error
                if not is_admin_user(user):
                    users = read_json(USERS_FILE)
                    users[uid]["credits"] += 1
                    write_json(USERS_FILE, users)
                await update.message.reply_text(ERROR_REFUND_MSG, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Search error: {e}")
            if not is_admin_user(user):
                users = read_json(USERS_FILE)
                users[uid]["credits"] += 1
                write_json(USERS_FILE, users)
            await update.message.reply_text(ERROR_REFUND_MSG, parse_mode="Markdown")

        context.user_data.pop("mode", None)
        await update.message.reply_text("🔙 Back to Menu", reply_markup=back_to_menu_kb())
        return

    await update.message.reply_text("ℹ️ *Use /start to see the menu.*", parse_mode="Markdown")

# ---------------- Admin callback handlers ----------------
async def admin_callback_handler(update: Update, context: CallbackContext):
    q = update.callback_query; await q.answer()
    user = q.from_user
    if not is_admin_user(user):
        await q.message.reply_text("❌ *You are not authorized to use admin commands.*", parse_mode="Markdown")
        return

    data = q.data
    
    # Admin panel
    if data == "admin_panel":
        await q.message.reply_text("⚙️ *Admin Panel*", parse_mode="Markdown", reply_markup=admin_panel_kb())
        return

    # Admin Stats
    if data == "admin_stats":
        users = read_json(USERS_FILE)
        total = len(users)
        banned = sum(1 for u in users.values() if u.get("banned", False))
        total_credits = sum(u.get("credits", 0) for u in users.values())
        await q.message.reply_text(f"📊 *User Statistics*\n\n• Total Users: *{total}*\n• Banned: *{banned}*\n• Total Credits: *{total_credits}*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
        return

    # Generate Codes
    if data == "admin_gen_codes":
        context.user_data["admin_state"] = "gen_codes_waiting"
        await q.message.reply_text("🎁 *How many redeem codes to generate?* (max 100)", parse_mode="Markdown")
        return

    # User Info
    if data == "admin_user_info":
        context.user_data["admin_state"] = "user_info_waiting"
        await q.message.reply_text("🔎 *Send the user ID to get info.*", parse_mode="Markdown")
        context.user_data["admin_state"] = "user_info_waiting"
        return

    # Force Backup
    if data == "admin_backup":
        if send_backup_to_admins():
            await q.message.reply_text("✅ *Backup sent to all admins.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
        else:
            await q.message.reply_text("⏳ *Backup cooldown active. Wait a few minutes.*", parse_mode="Markdown", reply_markup=admin_action_back_buttons())
        return

    # Ban
    if data == "admin_ban":
        context.user_data["admin_state"] = "ban_waiting"
        await q.message.reply_text("🚫 *Send the user ID to BAN.*", parse_mode="Markdown")
        return

    # Unban
    if data == "admin_unban":
        context.user_data["admin_state"] = "unban_waiting"
        await q.message.reply_text("✅ *Send the user ID to UNBAN.*", parse_mode="Markdown")
        return

    # Deduct
    if data == "admin_deduct":
        context.user_data["admin_state"] = "deduct_waiting"
        await q.message.reply_text("➖ *Send the user ID to deduct 1 credit.*", parse_mode="Markdown")
        return

    # Custom Deduct
    if data == "admin_deduct_custom":
        context.user_data["admin_state"] = "deduct_custom_waiting"
        await q.message.reply_text("➖ *Send user ID and amount. Example:* `123456789 5`", parse_mode="Markdown")
        return

    # Add Credits
    if data == "admin_add_credits":
        context.user_data["admin_state"] = "add_credits_waiting"
        await q.message.reply_text("➕ *Send user ID and amount. Example:* `123456789 10`", parse_mode="Markdown")
        return

    # Broadcast
    if data == "admin_broadcast":
        context.user_data["admin_state"] = "broadcast_waiting"
        await q.message.reply_text("📣 *Send the broadcast message.*", parse_mode="Markdown")
        return

    await q.message.reply_text("⚠️ *Unknown admin action.*", parse_mode="Markdown")

# ---------------- Main function ----------------
def main():
    """Start the bot."""
    # Create app with bot token
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("menu", menu_cmd))
    application.add_handler(CommandHandler("admin", admin_cmd))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(generic_callback, pattern="^(phone_in|phone_pk|aadhaar|cnic|ifsc|vehicle_rc|upi|redeem|credits|referral|help|daily_bonus|admin_panel|to_menu)$"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^(admin_stats|admin_gen_codes|admin_user_info|admin_backup|admin_ban|admin_unban|admin_deduct|admin_deduct_custom|admin_add_credits|admin_broadcast)$"))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Run bot
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    ensure_files_exist()
    main()
