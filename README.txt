📘 FKS OSINT BOT — FULL SETUP GUIDE (Complete Instructions)
Ye source code aap free use kar sakte ho. Bot chalane ke liye niche diye gaye sab steps follow karein.

⚠️ Bot sirf educational OSINT purpose ke liye hai. Illegal use aapki zimmedari hogi.

______________

🔧 1. Replace These Values in the Code

✔ BOT Token (BotFather se)

BOT_TOKEN = "YOUR_BOT_TOKEN"

✔ Bot Username (without @)

BOT_USERNAME = "YOUR_BOT_USERNAME"

✔ Credits Buy Contact Username (without @)

BUY_CREDITS_USERNAME = "YOUR_USERNAME"

✔ Admin User IDs (numeric)

ADMIN_IDS = [123456789, 987654321]

______________

🔥 2. API Endpoints (MOST IMPORTANT PART)

Niche diye format ko apne API URL se replace karein.
{num}, {aadhaar}, {cnic}, {rc}, {ifsc}, {upi} KO MAT HATANA!
Bot automatically input replace karega.

PHONE_IN_API = "https://yourapi.com/phone_in?number={num}"
PHONE_PK_API = "https://yourapi.com/phone_pk?number={num}"
AADHAAR_API = "https://yourapi.com/aadhaar?id={aadhaar}"
FAMILY_AADHAAR_API = "https://yourapi.com/family?id={aadhaar}"
CNIC_API = "https://yourapi.com/cnic?id={cnic}"
RC_API = "https://yourapi.com/rc?rc={rc}"
VEHICLE_API = "https://yourapi.com/vehicle?rc={rc}"
IFSC_API = "https://yourapi.com/ifsc?ifsc={ifsc}"
UPI_API = "https://yourapi.com/upi?id={upi}"

Bas https://yourapi.com/... ko apne API URL se replace kar do.

______________

🗂 3. Files Bot Automatically Create Karta Hai

Aapko manually kuch nahi karna:

users.json

redeem_codes.json

backup_meta.json

______________

📦 4. requirements.txt

Is bot ke liye sirf ye 2 packages chahiye:

python-telegram-bot==20.7
requests

Mene Already Zip Mein Requirements.txt Di Hein Tumhe Nahin Banani Padegi

______________

▶️ 5. How to Run the Bot

Termux / PC / Linux:

pip install -r requirements.txt
python bot.py

Hosting (Render / Railway / VPS):

python bot.py

______________

🎯 6. Bot Features

Phone Lookup (India / Pakistan)

Aadhaar Lookup + Family Mode

CNIC Lookup

Vehicle / RC Lookup

IFSC Lookup

UPI Lookup

Redeem Code System

Daily Bonus

Referral System

User Credit System

Admin Panel

Ban / Unban

Add / Deduct Credits

Generate Redeem Codes

Broadcast

Auto Backup

______________

⚖️ 7. Legal Disclaimer

Bot ka illegal use strictly prohibited hai.
Developer koi zimmedari nahi leta.

______________

⭐ 8. Credits

Source Giveaway By: @IndianWatchdogs / @Indian_Hackers_Team
