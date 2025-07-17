import os, re, json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

ROOT_REPORT = "reports"
DATA_FILE = "all_transactions.json"
BOT_TOKEN = "7601064850:AAFdcLzg0jiXIDlHdwZIUsHzOB-6EirkSUY"
ABA_BOT_ID = 1236061511   # ប្រាកដជាត្រូវតែមើល Debug

for sub in ["daily", "weekly", "monthly", "yearly"]:
    os.makedirs(os.path.join(ROOT_REPORT, sub), exist_ok=True)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_range_keys(dt):
    y, m, d = dt.year, dt.month, dt.day
    week = dt.isocalendar()[1]
    return {
        "daily": f"{y:04d}-{m:02d}-{d:02d}",
        "weekly": f"{y:04d}-W{week:02d}",
        "monthly": f"{y:04d}-{m:02d}",
        "yearly": f"{y:04d}"
    }

def append_and_save_reports(txns):
    data = load_data()
    for txn in txns:
        data.append(txn)
    save_data(data)
    for txn in txns:
        dt = datetime.strptime(txn["datetime"], "%Y-%m-%d %H:%M")
        keys = get_range_keys(dt)
        for report_type in ["daily", "weekly", "monthly", "yearly"]:
            path = os.path.join(ROOT_REPORT, report_type, f"{keys[report_type]}.json")
            arr = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    arr = json.load(f)
            arr.append(txn)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(arr, f, indent=2, ensure_ascii=False)

def parse_aba_transaction(text):
    usd_matches = re.findall(r'\$([0-9,]+\.\d{2})', text)
    khr_matches = re.findall(r'៛\s?([0-9,]+)', text)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    transactions = []
    detected = False
    for usd in usd_matches:
        amt = float(usd.replace(',', ''))
        transactions.append({
            "currency": "USD",
            "amount": amt,
            "text": text,
            "datetime": now,
            "detected": True
        })
        detected = True
    for khr in khr_matches:
        amt = int(khr.replace(',', ''))
        transactions.append({
            "currency": "KHR",
            "amount": amt,
            "text": text,
            "datetime": now,
            "detected": True
        })
        detected = True
    if not detected:
        transactions.append({
            "currency": None,
            "amount": None,
            "text": text,
            "datetime": now,
            "detected": False
        })
    return transactions

# ---- DEBUG: Show User ID & Name (only enable 1st time for ABA Bot ID!) ----
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    name = update.message.from_user.full_name
    text = update.message.text
    # ABA Bot Only
    if user_id == ABA_BOT_ID:
        txns = parse_aba_transaction(text)
        append_and_save_reports(txns)
        new_usd = sum(1 for txn in txns if txn.get("currency") == "USD")
        new_khr = sum(1 for txn in txns if txn.get("currency") == "KHR")
        if new_usd or new_khr:
            tmp = []
            if new_usd:
                tmp.append(f"✅ ចាប់បាន USD {new_usd} ដង")
            if new_khr:
                tmp.append(f"✅ ចាប់បាន KHR {new_khr} ដង")
            msg = "\n".join(tmp)
        else:
            msg = "✅ រក្សាទុកសារបានជោគជ័យ (មិនមាន $ ឬ ៛)"
        await update.message.reply_text(msg)
    # ---- (Uncomment for debug, to see User ID of sender) ----
    # await update.message.reply_text(f"User ID: {user_id}\nName: {name}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btns = [
        [KeyboardButton("📆 ប្រចាំថ្ងៃ"), KeyboardButton("📅 ប្រចាំសប្ដាហ៍")],
        [KeyboardButton("🗓️ ប្រចាំខែ"), KeyboardButton("📈 ប្រចាំឆ្នាំ")],
    ]
    markup = ReplyKeyboardMarkup(btns, resize_keyboard=True)
    await update.message.reply_text("📊 សូមជ្រើសរើសរបាយការណ៍:", reply_markup=markup)

def get_report_keys(type_, now):
    if type_ == "daily":
        return get_range_keys(now)["daily"]
    elif type_ == "weekly":
        return get_range_keys(now)["weekly"]
    elif type_ == "monthly":
        return get_range_keys(now)["monthly"]
    elif type_ == "yearly":
        return get_range_keys(now)["yearly"]
    return None

def format_date(dt):
    return dt.strftime("%d %b %Y")

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    txt = update.message.text
    if txt == "📆 ប្រចាំថ្ងៃ":
        typ = "daily"
    elif txt == "📅 ប្រចាំសប្ដាហ៍":
        typ = "weekly"
    elif txt == "🗓️ ប្រចាំខែ":
        typ = "monthly"
    elif txt == "📈 ប្រចាំឆ្នាំ":
        typ = "yearly"
    else:
        typ = None

    if typ:
        key = get_report_keys(typ, now)
        path = os.path.join(ROOT_REPORT, typ, f"{key}.json")
        usd_list, khr_list = [], []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                arr = json.load(f)
            usd_list = [x for x in arr if x.get("currency") == "USD" and x.get("detected")]
            khr_list = [x for x in arr if x.get("currency") == "KHR" and x.get("detected")]
        usd = sum(float(x["amount"]) for x in usd_list)
        khr = sum(int(x["amount"]) for x in khr_list)
        # Date Range
        if typ == "daily":
            start_str = end_str = format_date(now)
        elif typ == "weekly":
            start = now - timedelta(days=now.weekday())
            end = start + timedelta(days=6)
            start_str = format_date(start)
            end_str = format_date(end)
        elif typ == "monthly":
            start = now.replace(day=1)
            end = now
            start_str = format_date(start)
            end_str = format_date(end)
        elif typ == "yearly":
            start = now.replace(month=1, day=1)
            end = now
            start_str = format_date(start)
            end_str = format_date(end)
        msg = (
            f"📊 Summary from {start_str} → {end_str}\n"
            f"💵 USD: ${usd:.2f} ({len(usd_list)} transactions)\n"
            f"🇰🇭 KHR: ៛{khr:,} ({len(khr_list)} transactions)"
        )
    else:
        msg = "❓ មិនដឹងប៊ូតុងនេះទេ។ សូមចុច /report ដើម្បីមើលប៊ូតុង!"
    await update.message.reply_text(msg)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.Regex(r"^(📆 ប្រចាំថ្ងៃ|📅 ប្រចាំសប្ដាហ៍|🗓️ ប្រចាំខែ|📈 ប្រចាំឆ្នាំ)$"), handle_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
