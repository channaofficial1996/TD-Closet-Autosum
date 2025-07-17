import os
import re
import json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

DATA_FILE = "transactions.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_transaction(text):
    match = re.search(r"([៛$])([\d,]+(?:\.\d{2})?) paid by (.+?) \(.*?\) on (\w+ \d+), (\d{1,2}:\d{2} (?:AM|PM))", text)
    if match:
        currency, amount, name, date_str, time_str = match.groups()
        try:
            amount = float(amount.replace(",", ""))
            full_date = datetime.strptime(f"{date_str} {time_str}", "%b %d %I:%M %p")
            return {
                "name": name.strip(),
                "amount": amount,
                "currency": currency,
                "date": full_date.strftime("%Y-%m-%d")
            }
        except:
            return None
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tx = parse_transaction(text)
    if tx:
        data = load_data()
        data.append(tx)
        save_data(data)
        await update.message.reply_text("✅ Transaction saved.")
    else:
        await update.message.reply_text("❌ Message format not recognized.")

def summarize_by_range(start_date, end_date, currency):
    data = load_data()
    selected = [t for t in data if start_date <= t["date"] <= end_date and t.get("currency") == currency]
    total = sum(t["amount"] for t in selected)
    count = len(selected)
    return total, count

async def send_summary(update: Update, start, end, label):
    usd_total, usd_count = summarize_by_range(start, end, "$")
    khm_total, khm_count = summarize_by_range(start, end, "៛")

    message = f"{label}\n"
    message += f"💵 USD: ${usd_total:.2f} ({usd_count} transactions)\n"
    message += f"🇰🇭 KHR: ៛{khm_total:,.0f} ({khm_count} transactions)"
    await update.message.reply_text(message)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.today().strftime("%Y-%m-%d")
    await send_summary(update, today, today, "📅 Today")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.today()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    label = f"🗓 This Week ({start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')})"
    await send_summary(update, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), label)

async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = today
    label = f"📆 This Month ({start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')})"
    await send_summary(update, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), label)

async def yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.today()
    start_date = today.replace(month=1, day=1)
    end_date = today
    label = f"📈 This Year ({start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')})"
    await send_summary(update, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), label)

async def custom_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❗ Usage: /range YYYY-MM-DD YYYY-MM-DD")
        return
    try:
        start_date = datetime.strptime(args[0], "%Y-%m-%d")
        end_date = datetime.strptime(args[1], "%Y-%m-%d")
        label = f"📊 Summary from {start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')}"
        await send_summary(update, args[0], args[1], label)
    except ValueError:
        await update.message.reply_text("❌ Invalid date format. Use YYYY-MM-DD.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/daily", "/weekly"],
        ["/monthly", "/yearly"],
        ["/range 2025-07-01 2025-07-17"]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Choose a report"
    )
    await update.message.reply_text(
        "👋 Welcome! Choose a report below or type /range <start> <end>",
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    BOT_TOKEN = "7601064850:AAFdcLzg0jiXIDlHdwZIUsHzOB-6EirkSUY"
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(CommandHandler("monthly", monthly))
    app.add_handler(CommandHandler("yearly", yearly))
    app.add_handler(CommandHandler("range", custom_range))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
