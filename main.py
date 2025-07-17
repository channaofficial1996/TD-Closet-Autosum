import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

DATA_FILE = "transactions.json"
# FIX HERE:
TOKEN = "7601064850:AAFdcLzg0jiXIDlHdwZIUsHzOB-6EirkSUY"
# ឬប្រើ TOKEN = os.getenv("BOT_TOKEN")

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

main_menu = ReplyKeyboardMarkup([
    ["ប្រចាំថ្ងៃ", "ប្រចាំសប្ដាហ៍"],
    ["ប្រចាំខែ"]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "សូមជ្រើសរើសសកម្មភាព៖",
        reply_markup=main_menu
    )

async def add_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    if "KHR" in msg:
        currency = "KHR"
        amount = int(msg.replace("KHR:", "").strip())
    elif "USD" in msg:
        currency = "USD"
        amount = float(msg.replace("USD:", "").strip())
    else:
        await update.message.reply_text("បញ្ចូលទ្រង់ទ្រាយ KHR:50000 ឬ USD:5")
        return
    data = load_data()
    data.append({
        "amount": amount,
        "currency": currency,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    save_data(data)
    await update.message.reply_text("បានកត់ត្រា")

async def report_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    khr_total = sum(d["amount"] for d in data if d["currency"] == "KHR" and d["date"] == today)
    usd_total = sum(d["amount"] for d in data if d["currency"] == "USD" and d["date"] == today)
    khr_count = sum(1 for d in data if d["currency"] == "KHR" and d["date"] == today)
    usd_count = sum(1 for d in data if d["currency"] == "USD" and d["date"] == today)
    text = (
        f"សរុបប្រតិបត្តិការ ថ្ងៃទី {today}:\n"
        f"៛ (KHR): {khr_total:,} ចំនួនប្រតិបត្តិការសរុប: {khr_count}\n"
        f"$ (USD): {usd_total:.2f} ចំនួនប្រតិបត្តិការសរុប: {usd_count}"
    )
    await update.message.reply_text(text)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("^ប្រចាំថ្ងៃ$"), report_daily))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), add_transaction))

app.run_polling()
