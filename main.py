import re, json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

DATA_FILE = "transactions.json"
BOT_TOKEN = "7601064850:AAFdcLzg0jiXIDlHdwZIUsHzOB-6EirkSUY"

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    txns = parse_aba_transaction(text)
    data = load_data()
    msg = ""
    new_usd = sum(1 for txn in txns if txn.get("currency") == "USD")
    new_khr = sum(1 for txn in txns if txn.get("currency") == "KHR")
    for txn in txns:
        data.append(txn)
    save_data(data)
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

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btns = [
        [KeyboardButton("📆 ប្រចាំថ្ងៃ"), KeyboardButton("📅 ប្រចាំសប្ដាហ៍")],
        [KeyboardButton("🗓️ ប្រចាំខែ"), KeyboardButton("📈 ប្រចាំឆ្នាំ")],
    ]
    markup = ReplyKeyboardMarkup(btns, resize_keyboard=True)
    await update.message.reply_text("📊 សូមជ្រើសរើសរបាយការណ៍:", reply_markup=markup)

def get_range(type_, now):
    if type_ == "daily":
        start = now.replace(hour=0, minute=0)
        end = now.replace(hour=23, minute=59)
    elif type_ == "weekly":
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6, hours=23, minutes=59)
    elif type_ == "monthly":
        start = now.replace(day=1, hour=0, minute=0)
        end = now.replace(hour=23, minute=59)
    elif type_ == "yearly":
        start = now.replace(month=1, day=1, hour=0, minute=0)
        end = now.replace(hour=23, minute=59)
    return start, end

def format_date(dt):
    return dt.strftime("%d %b %Y")

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
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
        start, end = get_range(typ, now)
        usd_list = [x for x in data if x.get("currency")=="USD" and x.get("detected") and start <= datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M") <= end]
        khr_list = [x for x in data if x.get("currency")=="KHR" and x.get("detected") and start <= datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M") <= end]
        usd = sum(float(x["amount"]) for x in usd_list)
        khr = sum(int(x["amount"]) for x in khr_list)
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
