import os, re, json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

DATA_FILE = "transactions.json"
BOT_TOKEN = "7601064850:AAFdcLzg0jiXIDlHdwZIUsHzOB-6EirkSUY"  # <<<< Hardcoded HERE

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_aba_transaction(text):
    m = re.search(r'(?i)(?:PayWay by ABA|Received)\s*\$([\d,\.]+)', text)
    if m:
        amt = float(m.group(1).replace(',', ''))
        return {"amount": amt, "text": text, "datetime": datetime.now().strftime("%Y-%m-%d %H:%M")}
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    txn = parse_aba_transaction(text)
    if txn:
        data = load_data()
        data.append(txn)
        save_data(data)
        await update.message.reply_text(f"✅ បញ្ចូលប្រាក់ចូល: ${txn['amount']:.2f}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btns = [
        [KeyboardButton("📆 ប្រចាំថ្ងៃ"), KeyboardButton("📅 ប្រចាំសប្ដាហ៍")],
        [KeyboardButton("🗓️ ប្រចាំខែ"), KeyboardButton("📈 ប្រចាំឆ្នាំ")],
    ]
    markup = ReplyKeyboardMarkup(btns, resize_keyboard=True)
    await update.message.reply_text("📊 សូមជ្រើសរើសរបាយការណ៍:", reply_markup=markup)

def sum_report(data, start, end):
    total = sum(float(x["amount"]) for x in data if start <= datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M") <= end)
    return total

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now()
    msg = ""
    if update.message.text == "📆 ប្រចាំថ្ងៃ":
        start = now.replace(hour=0, minute=0)
        end = now.replace(hour=23, minute=59)
        tot = sum_report(data, start, end)
        msg = f"📆​ ប្រាក់ចូលប្រចាំថ្ងៃ: **${tot:.2f}**"
    elif update.message.text == "📅 ប្រចាំសប្ដាហ៍":
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6, hours=23, minutes=59)
        tot = sum_report(data, start, end)
        msg = f"📅​ ប្រាក់ចូលប្រចាំសប្ដាហ៍: **${tot:.2f}**"
    elif update.message.text == "🗓️ ប្រចាំខែ":
        start = now.replace(day=1, hour=0, minute=0)
        end = now.replace(hour=23, minute=59)
        tot = sum_report(data, start, end)
        msg = f"🗓️​ ប្រាក់ចូលប្រចាំខែ: **${tot:.2f}**"
    elif update.message.text == "📈 ប្រចាំឆ្នាំ":
        start = now.replace(month=1, day=1, hour=0, minute=0)
        end = now.replace(hour=23, minute=59)
        tot = sum_report(data, start, end)
        msg = f"📈​ ប្រាក់ចូលប្រចាំឆ្នាំ: **${tot:.2f}**"
    else:
        msg = "❓ មិនដឹងប៊ូតុងនេះទេ។ សូមចុច /report ដើម្បីមើលប៊ូតុង!"
    await update.message.reply_text(msg, parse_mode="Markdown")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.Regex(r"^(📆 ប្រចាំថ្ងៃ|📅 ប្រចាំសប្ដាហ៍|🗓️ ប្រចាំខែ|📈 ប្រចាំឆ្នាំ)$"), handle_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
