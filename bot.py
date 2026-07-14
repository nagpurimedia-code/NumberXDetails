# FKS OSINT BOT - PYTHON 3.14 COMPATIBLE
# Telegram: @ColdenMinj

import os
import json
import time
import random
import string
import logging
import asyncio
import requests
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============ CONFIG ============
BOT_TOKEN = "8759960516:AAEWakdCpP7J7sSNXd6PtL34-l78vMF5zL4"
BOT_USERNAME = "SearchPortalBot"
BUY_CREDITS_USERNAME = "ColdenMinj"
ADMIN_IDS = [8523360387]

REFERRAL_BONUS = 2
INITIAL_CREDITS = 2
SEARCH_COST = 1
BACKUP_COOLDOWN = 300
DAILY_BONUS_AMOUNT = 2
DAILY_SECONDS = 86400
GENERATED_CODE_LENGTH = 8

USERS_FILE = "users.json"
CODES_FILE = "redeem_codes.json"
BACKUP_META = "backup_meta.json"

# ============ API ENDPOINTS (REPLACE WITH YOUR ACTUAL APIS) ============
PHONE_IN_API = "https://yourapi.com/phone_in?number={num}"
PHONE_PK_API = "https://yourapi.com/phone_pk?number={num}"
AADHAAR_API = "https://yourapi.com/aadhaar?id={aadhaar}"
CNIC_API = "https://yourapi.com/cnic?id={cnic}"
IFSC_API = "https://yourapi.com/ifsc?ifsc={ifsc}"
VEHICLE_API = "https://yourapi.com/vehicle?rc={rc}"
UPI_API = "https://yourapi.com/upi?id={upi}"

# ============ LOGGING ============
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fks-bot")

# ============ FILE HELPERS ============
def read_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Write error: {e}")

def ensure_files():
    for f in [USERS_FILE, CODES_FILE, BACKUP_META]:
        if not os.path.exists(f):
            write_json(f, {})

# ============ HELPERS ============
def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=GENERATED_CODE_LENGTH))

def http_get(url, timeout=12):
    try:
        r = requests.get(url, headers={"User-Agent": "FKS-BOT"}, timeout=timeout)
        r.raise_for_status()
        return r
    except:
        return None

def ensure_user(uid):
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
    return users

def is_banned(uid):
    users = read_json(USERS_FILE)
    return users.get(uid, {}).get("banned", False)

def is_admin(user):
    if not user:
        return False
    try:
        if user.id in ADMIN_IDS:
            return True
    except:
        pass
    try:
        if user.username and user.username.lower() == BUY_CREDITS_USERNAME.lower():
            return True
    except:
        pass
    return False

def scrub_response(obj):
    block = ["developer", "owner", "author", "creator", "api_by", "dev", "tag", "footer"]
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            if any(b in k.lower() for b in block):
                continue
            if isinstance(v, str) and any(b in v.lower() for b in block):
                continue
            clean[k] = scrub_response(v)
        return clean
    elif isinstance(obj, list):
        return [scrub_response(x) for x in obj]
    return obj

def send_backup():
    meta = read_json(BACKUP_META)
    now = int(time.time())
    if now - meta.get("last", 0) < BACKUP_COOLDOWN:
        return False
    try:
        bot = Bot(token=BOT_TOKEN)
        if os.path.exists(USERS_FILE):
            for admin in ADMIN_IDS:
                try:
                    with open(USERS_FILE, "rb") as f:
                        bot.send_document(chat_id=admin, document=f, filename="users.json", caption="📦 Backup")
                except:
                    pass
        meta["last"] = now
        write_json(BACKUP_META, meta)
        return True
    except:
        return False

# ============ KEYBOARDS ============
def main_menu():
    kb = [
        [InlineKeyboardButton("Phone 🇮🇳", callback_data="phone_in"),
         InlineKeyboardButton("Phone 🇵🇰", callback_data="phone_pk"),
         InlineKeyboardButton("Aadhaar 🆔", callback_data="aadhaar")],
        [InlineKeyboardButton("CNIC 🇵🇰", callback_data="cnic"),
         InlineKeyboardButton("IFSC 🏦", callback_data="ifsc"),
         InlineKeyboardButton("Vehicle/RC 🚗", callback_data="vehicle_rc")],
        [InlineKeyboardButton("UPI 🔗", callback_data="upi"),
         InlineKeyboardButton("🎁 Redeem", callback_data="redeem"),
         InlineKeyboardButton("🎯 Referral", callback_data="referral")],
        [InlineKeyboardButton("💰 Credits", callback_data="credits"),
         InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("💳 Buy Credits", url=f"https://t.me/{BUY_CREDITS_USERNAME}")]
    ]
    return InlineKeyboardMarkup(kb)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="to_menu")]])

def admin_menu():
    kb = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
         InlineKeyboardButton("🎁 Gen Codes", callback_data="admin_gen_codes")],
        [InlineKeyboardButton("📦 Backup", callback_data="admin_backup"),
         InlineKeyboardButton("🚫 Ban", callback_data="admin_ban"),
         InlineKeyboardButton("✅ Unban", callback_data="admin_unban")],
        [InlineKeyboardButton("➖ Deduct", callback_data="admin_deduct"),
         InlineKeyboardButton("➕ Add Credits", callback_data="admin_add_credits")],
        [InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="to_menu")]
    ]
    return InlineKeyboardMarkup(kb)

def admin_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="to_menu")]
    ])

# ============ COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    
    users_before = read_json(USERS_FILE)
    is_new = uid not in users_before
    
    ensure_user(uid)
    
    if is_banned(uid):
        await update.message.reply_text("❌ You are banned.", parse_mode="Markdown")
        return
    
    # Referral
    args = context.args
    if args and is_new:
        try:
            ref = str(int(args[0]))
            if ref != uid:
                users = read_json(USERS_FILE)
                if users[uid].get("referred_by") is None:
                    users[uid]["referred_by"] = ref
                    if ref in users:
                        users[ref]["credits"] = users[ref].get("credits", 0) + REFERRAL_BONUS
                        users[ref]["referrals"] = users[ref].get("referrals", 0) + 1
                        write_json(USERS_FILE, users)
                        try:
                            await context.bot.send_message(int(ref), f"🎉 You earned {REFERRAL_BONUS} credits from referral!")
                        except:
                            pass
        except:
            pass
    
    welcome = f"👋 Hi {user.first_name}! Welcome to FKS OSINT Bot.\n\n🔍 Each search costs 1 credit.\n🎁 Daily bonus: {DAILY_BONUS_AMOUNT} credits\n🎯 Referral: {REFERRAL_BONUS} credits per referral\n\nContact @{BUY_CREDITS_USERNAME} for help."
    await update.message.reply_text(welcome, parse_mode="Markdown")
    await update.message.reply_text("✅ Choose an option:", reply_markup=main_menu())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Choose an option:", reply_markup=main_menu())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user):
        await update.message.reply_text("❌ Unauthorized.", parse_mode="Markdown")
        return
    await update.message.reply_text("⚙️ Admin Panel:", reply_markup=admin_menu())

# ============ CALLBACKS ============
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uid = str(user.id)
    data = query.data
    
    # Admin callbacks
    if data.startswith("admin_"):
        if not is_admin(user):
            await query.message.reply_text("❌ Unauthorized.", parse_mode="Markdown")
            return
        
        # Admin Stats
        if data == "admin_stats":
            users = read_json(USERS_FILE)
            total = len(users)
            banned = sum(1 for u in users.values() if u.get("banned", False))
            credits = sum(u.get("credits", 0) for u in users.values())
            await query.message.reply_text(f"📊 Stats:\nTotal: {total}\nBanned: {banned}\nCredits: {credits}", parse_mode="Markdown", reply_markup=admin_back())
            return
        
        # Generate Codes
        if data == "admin_gen_codes":
            context.user_data["admin_state"] = "gen_codes"
            await query.message.reply_text("🎁 How many codes? (max 50)", parse_mode="Markdown")
            return
        
        # Backup
        if data == "admin_backup":
            if send_backup():
                await query.message.reply_text("✅ Backup sent.", parse_mode="Markdown", reply_markup=admin_back())
            else:
                await query.message.reply_text("⏳ Cooldown active.", parse_mode="Markdown", reply_markup=admin_back())
            return
        
        # Ban
        if data == "admin_ban":
            context.user_data["admin_state"] = "ban"
            await query.message.reply_text("🚫 Send user ID to ban:", parse_mode="Markdown")
            return
        
        # Unban
        if data == "admin_unban":
            context.user_data["admin_state"] = "unban"
            await query.message.reply_text("✅ Send user ID to unban:", parse_mode="Markdown")
            return
        
        # Deduct
        if data == "admin_deduct":
            context.user_data["admin_state"] = "deduct"
            await query.message.reply_text("➖ Send user ID to deduct 1 credit:", parse_mode="Markdown")
            return
        
        # Add Credits
        if data == "admin_add_credits":
            context.user_data["admin_state"] = "add_credits"
            await query.message.reply_text("➕ Send: `user_id amount` (e.g. 123 5)", parse_mode="Markdown")
            return
        
        # Broadcast
        if data == "admin_broadcast":
            context.user_data["admin_state"] = "broadcast"
            await query.message.reply_text("📣 Send broadcast message:", parse_mode="Markdown")
            return
        
        # Admin Panel
        if data == "admin_panel":
            await query.message.reply_text("⚙️ Admin Panel:", reply_markup=admin_menu())
            return
    
    # Public callbacks
    if data == "to_menu":
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text("✅ Choose an option:", reply_markup=main_menu())
        return
    
    if data == "help":
        help_text = "🔍 Available searches:\n• Phone (IN/PK)\n• Aadhaar\n• CNIC\n• IFSC\n• Vehicle/RC\n• UPI\n\n💳 Each search costs 1 credit.\n🎁 Daily bonus available.\n🎯 Referral program active."
        await query.message.reply_text(help_text, parse_mode="Markdown", reply_markup=back_menu())
        return
    
    if data == "referral":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await query.message.reply_text(f"🎯 Your referral link:\n`{link}`\n\nEarn {REFERRAL_BONUS} credits per referral!", parse_mode="Markdown", reply_markup=back_menu())
        return
    
    if data == "daily_bonus":
        users = ensure_user(uid)
        now = int(time.time())
        if now - users[uid].get("last_daily", 0) >= DAILY_SECONDS:
            users[uid]["credits"] = users[uid].get("credits", 0) + DAILY_BONUS_AMOUNT
            users[uid]["last_daily"] = now
            write_json(USERS_FILE, users)
            await query.message.reply_text(f"🎁 +{DAILY_BONUS_AMOUNT} credits claimed!", parse_mode="Markdown")
        else:
            remaining = DAILY_SECONDS - (now - users[uid].get("last_daily", 0))
            hours = int(remaining // 3600)
            await query.message.reply_text(f"⏰ Already claimed. Try again in {hours}h.", parse_mode="Markdown")
        await query.message.reply_text("🔙 Back", reply_markup=back_menu())
        return
    
    if data == "credits":
        users = read_json(USERS_FILE)
        credits = "Unlimited" if is_admin(user) else users.get(uid, {}).get("credits", 0)
        await query.message.reply_text(f"💰 Your credits: {credits}", parse_mode="Markdown")
        return
    
    if data == "redeem":
        context.user_data["mode"] = "redeem"
        await query.message.reply_text("🎁 Send your redeem code:", parse_mode="Markdown")
        return
    
    # Search modes
    if data in ["phone_in", "phone_pk", "aadhaar", "cnic", "ifsc", "vehicle_rc", "upi"]:
        context.user_data["mode"] = data
        label = "RC/Vehicle" if data == "vehicle_rc" else data.upper()
        if data == "upi":
            label = "UPI ID"
        await query.message.reply_text(f"📤 Send {label} to search:", parse_mode="Markdown")
        return
    
    await query.message.reply_text("⚠️ Unknown option.", parse_mode="Markdown")

# ============ MESSAGE HANDLER ============
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    text = update.message.text.strip()
    
    if is_banned(uid):
        await update.message.reply_text("❌ You are banned.", parse_mode="Markdown")
        return
    
    ensure_user(uid)
    
    # Admin states
    admin_state = context.user_data.get("admin_state")
    if admin_state and is_admin(user):
        # Generate Codes
        if admin_state == "gen_codes":
            try:
                count = min(int(text), 50)
                codes = read_json(CODES_FILE)
                generated = []
                for _ in range(count):
                    code = gen_code()
                    codes[code] = {"used": False}
                    generated.append(code)
                write_json(CODES_FILE, codes)
                await update.message.reply_text(f"✅ Generated {count} codes:\n`{' '.join(generated)}`", parse_mode="Markdown", reply_markup=admin_back())
            except:
                await update.message.reply_text("❌ Invalid number.", parse_mode="Markdown", reply_markup=admin_back())
            context.user_data.pop("admin_state", None)
            return
        
        # Ban
        if admin_state == "ban":
            try:
                target = str(int(text))
                users = read_json(USERS_FILE)
                if target in users:
                    users[target]["banned"] = True
                    write_json(USERS_FILE, users)
                    await update.message.reply_text(f"✅ Banned {target}", parse_mode="Markdown", reply_markup=admin_back())
                else:
                    await update.message.reply_text("❌ User not found.", parse_mode="Markdown", reply_markup=admin_back())
            except:
                await update.message.reply_text("❌ Invalid ID.", parse_mode="Markdown", reply_markup=admin_back())
            context.user_data.pop("admin_state", None)
            return
        
        # Unban
        if admin_state == "unban":
            try:
                target = str(int(text))
                users = read_json(USERS_FILE)
                if target in users:
                    users[target]["banned"] = False
                    write_json(USERS_FILE, users)
                    await update.message.reply_text(f"✅ Unbanned {target}", parse_mode="Markdown", reply_markup=admin_back())
                else:
                    await update.message.reply_text("❌ User not found.", parse_mode="Markdown", reply_markup=admin_back())
            except:
                await update.message.reply_text("❌ Invalid ID.", parse_mode="Markdown", reply_markup=admin_back())
            context.user_data.pop("admin_state", None)
            return
        
        # Deduct
        if admin_state == "deduct":
            try:
                target = str(int(text))
                users = read_json(USERS_FILE)
                if target in users:
                    users[target]["credits"] = max(0, users[target].get("credits", 0) - 1)
                    write_json(USERS_FILE, users)
                    await update.message.reply_text(f"➖ Deducted 1 from {target}. New: {users[target]['credits']}", parse_mode="Markdown", reply_markup=admin_back())
                else:
                    await update.message.reply_text("❌ User not found.", parse_mode="Markdown", reply_markup=admin_back())
            except:
                await update.message.reply_text("❌ Invalid ID.", parse_mode="Markdown", reply_markup=admin_back())
            context.user_data.pop("admin_state", None)
            return
        
        # Add Credits
        if admin_state == "add_credits":
            try:
                parts = text.split()
                target = str(int(parts[0]))
                amount = int(parts[1])
                users = read_json(USERS_FILE)
                if target in users:
                    users[target]["credits"] = users[target].get("credits", 0) + amount
                    write_json(USERS_FILE, users)
                    await update.message.reply_text(f"➕ Added {amount} to {target}. New: {users[target]['credits']}", parse_mode="Markdown", reply_markup=admin_back())
                else:
                    await update.message.reply_text("❌ User not found.", parse_mode="Markdown", reply_markup=admin_back())
            except:
                await update.message.reply_text("❌ Use: `user_id amount`", parse_mode="Markdown", reply_markup=admin_back())
            context.user_data.pop("admin_state", None)
            return
        
        # Broadcast
        if admin_state == "broadcast":
            users = read_json(USERS_FILE)
            sent = 0
            for uid in users:
                try:
                    await context.bot.send_message(int(uid), f"📢 Broadcast:\n\n{text}")
                    sent += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
            await update.message.reply_text(f"✅ Sent to {sent} users.", parse_mode="Markdown", reply_markup=admin_back())
            context.user_data.pop("admin_state", None)
            return
    
    # Normal user modes
    mode = context.user_data.get("mode")
    
    # Redeem
    if mode == "redeem":
        code = text.upper()
        codes = read_json(CODES_FILE)
        if code in codes and not codes[code]["used"]:
            codes[code]["used"] = True
            write_json(CODES_FILE, codes)
            users = read_json(USERS_FILE)
            users[uid]["credits"] = users[uid].get("credits", 0) + 1
            write_json(USERS_FILE, users)
            await update.message.reply_text("🎁 Code redeemed! +1 credit!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Invalid/used code.", parse_mode="Markdown")
        context.user_data.pop("mode", None)
        await update.message.reply_text("🔙 Back", reply_markup=back_menu())
        return
    
    # Search
    if mode in ["phone_in", "phone_pk", "aadhaar", "cnic", "ifsc", "vehicle_rc", "upi"]:
        # Check credits (admins free)
        if not is_admin(user):
            users = read_json(USERS_FILE)
            if users[uid].get("credits", 0) < 1:
                await update.message.reply_text("❌ Not enough credits! Use /start for free credits.", parse_mode="Markdown")
                context.user_data.pop("mode", None)
                return
        
        # API mapping
        api_map = {
            "phone_in": PHONE_IN_API.format(num=text),
            "phone_pk": PHONE_PK_API.format(num=text),
            "aadhaar": AADHAAR_API.format(aadhaar=text),
            "cnic": CNIC_API.format(cnic=text),
            "ifsc": IFSC_API.format(ifsc=text),
            "vehicle_rc": VEHICLE_API.format(rc=text),
            "upi": UPI_API.format(id=text)
        }
        url = api_map.get(mode)
        
        # Deduct credit
        if not is_admin(user):
            users = read_json(USERS_FILE)
            users[uid]["credits"] -= 1
            write_json(USERS_FILE, users)
        
        # Search
        try:
            resp = http_get(url)
            if resp and resp.status_code == 200:
                data = resp.json()
                clean = scrub_response(data)
                result = json.dumps(clean, indent=2, ensure_ascii=False)
                if len(result) > 4000:
                    result = result[:4000] + "\n... (truncated)"
                await update.message.reply_text(f"📊 Result:\n```json\n{result}\n```", parse_mode="Markdown")
            else:
                # Refund on error
                if not is_admin(user):
                    users = read_json(USERS_FILE)
                    users[uid]["credits"] += 1
                    write_json(USERS_FILE, users)
                await update.message.reply_text("⚠️ Error fetching data. Credits refunded.", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Search error: {e}")
            if not is_admin(user):
                users = read_json(USERS_FILE)
                users[uid]["credits"] += 1
                write_json(USERS_FILE, users)
            await update.message.reply_text("⚠️ Error fetching data. Credits refunded.", parse_mode="Markdown")
        
        context.user_data.pop("mode", None)
        await update.message.reply_text("🔙 Back", reply_markup=back_menu())
        return
    
    await update.message.reply_text("ℹ️ Use /start for menu.", parse_mode="Markdown")

# ============ MAIN ============
def main():
    ensure_files()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_panel))
    
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("🤖 FKS OSINT Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
