# bot.py — Render-ready version
import os
import threading
from flask import Flask
from dotenv import load_dotenv
import asyncio

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# --- Load env ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not set. Put BOT_TOKEN into Render Environment variables.")
GROUP_ID = int(os.getenv("GROUP_ID", "-4986401168"))

# --- Conversation states ---
NAME, AGE, CITIZENSHIP, FROM_COUNTRY, DATES, PEOPLE, PURPOSE, CONTACT = range(8)

# --- Flask app for healthchecks (Render expects a bound port) ---
app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Bot is running (Render health endpoint).", 200

# --- Handlers (kept your original questionnaire logic) ---
async def greet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or user.username or "друг"
    keyboard = [["🚀 Начать анкету"]]
    text = (
        f"👋 Привет, {name}! 🇺🇸\n\n"
        "Я помогу вам с легальной иммиграцией в США.\n\n"
        "Нажмите кнопку ниже, чтобы начать заполнение анкеты 👇"
    )
    try:
        with open("usa_flag.jpg", "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=text,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
    except FileNotFoundError:
        await update.message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await greet(update, context)

async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Ваш возраст?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Ваше гражданство?")
    return CITIZENSHIP

async def get_citizenship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["citizenship"] = update.message.text
    await update.message.reply_text("Страна отправления?")
    return FROM_COUNTRY

async def get_from_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["from_country"] = update.message.text
    await update.message.reply_text("Желательные даты вылета?")
    return DATES

async def get_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dates"] = update.message.text
    await update.message.reply_text("Количество человек?")
    return PEOPLE

async def get_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["people"] = update.message.text
    reply_keyboard = [
        ["Политическое убежище", "Виза талантов"],
        ["Легализация", "Автопереход"]
    ]
    await update.message.reply_text(
        "Ваша цель:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PURPOSE

async def get_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["purpose"] = update.message.text
    await update.message.reply_text(
        "Пожалуйста, оставьте Ваш контакт (телефон, email или Telegram @username), "
        "наш менеджер с Вами свяжется:",
        reply_markup=ReplyKeyboardRemove()
    )
    return CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    data = context.user_data

    message = (
        f"📋 <b>Новая заявка:</b>\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"🎂 Возраст: {data.get('age')}\n"
        f"🛂 Гражданство: {data.get('citizenship')}\n"
        f"🌍 Страна отправления: {data.get('from_country')}\n"
        f"📅 Даты вылета: {data.get('dates')}\n"
        f"👥 Кол-во человек: {data.get('people')}\n"
        f"🎯 Цель: {data.get('purpose')}\n"
        f"📞 Контакт: {data.get('contact')}"
    )

    processing = await update.message.reply_text("🕐 Обрабатываем заявку...")
    await asyncio.sleep(1.5)
    await processing.delete()

    await context.bot.send_message(chat_id=GROUP_ID, text=message, parse_mode="HTML")
    await update.message.reply_text("✅ Спасибо! Ваша заявка отправлена.")
    await asyncio.sleep(0.8)
    await update.message.reply_text("🤖 Команда уже работает над этой заявкой!")
    await asyncio.sleep(0.8)

    await greet(update, context)
    return ConversationHandler.END

# --- Telegram runner (runs in a separate thread) ---
def telegram_thread_target():
    # Build synchronous Application and run_polling (blocking) inside thread
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("(?i)(начать анкету|🚀 начать анкету)"), start_form)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITIZENSHIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_citizenship)],
            FROM_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_from_country)],
            DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dates)],
            PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_people)],
            PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_purpose)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, greet))

    # This is blocking call but it's okay inside the thread
    print("🚀 Telegram thread: starting run_polling()")
    app.run_polling()
    print("⚠️ Telegram thread: run_polling() exited")


if __name__ == "__main__":
    # 1) Start Telegram in background daemon thread
    telegram_thread = threading.Thread(target=telegram_thread_target, name="tg-thread", daemon=True)
    telegram_thread.start()

    # 2) Run Flask in main thread and bind to PORT (Render uses this to keep service alive)
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask healthcheck available at 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)


