import asyncio
import os
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# --- Загружаем токены ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GROUP_ID = int(os.getenv("GROUP_ID", "-4986401168"))

# --- Flask для Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running on Render!"

# --- Этапы анкеты ---
NAME, AGE, CITIZENSHIP, FROM_COUNTRY, DATES, PEOPLE, PURPOSE, CONTACT = range(8)

# --- Приветствие ---
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
        await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await greet(update, context)

# --- Анкета ---
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    return NAME

async def get_name(update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Ваш возраст?")
    return AGE

async def get_age(update, context):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Ваше гражданство?")
    return CITIZENSHIP

async def get_citizenship(update, context):
    context.user_data["citizenship"] = update.message.text
    await update.message.reply_text("Страна отправления?")
    return FROM_COUNTRY

async def get_from_country(update, context):
    context.user_data["from_country"] = update.message.text
    await update.message.reply_text("Желательные даты вылета?")
    return DATES

async def get_dates(update, context):
    context.user_data["dates"] = update.message.text
    await update.message.reply_text("Количество человек?")
    return PEOPLE

async def get_people(update, context):
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

async def get_purpose(update, context):
    context.user_data["purpose"] = update.message.text
    await update.message.reply_text(
        "Пожалуйста, оставьте Ваш контакт (телефон, email или Telegram @username):",
        reply_markup=ReplyKeyboardRemove()
    )
    return CONTACT

async def get_contact(update, context):
    context.user_data["contact"] = update.message.text
    data = context.user_data

    message = (
        f"📋 <b>Новая заявка:</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"🛂 Гражданство: {data['citizenship']}\n"
        f"🌍 Страна отправления: {data['from_country']}\n"
        f"📅 Даты вылета: {data['dates']}\n"
        f"👥 Кол-во человек: {data['people']}\n"
        f"🎯 Цель: {data['purpose']}\n"
        f"📞 Контакт: {data['contact']}"
    )

    await context.bot.send_message(chat_id=GROUP_ID, text=message, parse_mode="HTML")
    await update.message.reply_text("✅ Спасибо! Ваша заявка отправлена.")
    await asyncio.sleep(1)
    await greet(update, context)
    return ConversationHandler.END

# --- Основной запуск бота ---
async def run_bot():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()

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
        fallbacks=[],
    )

    app_telegram.add_handler(conv_handler)
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, greet))

    print("🚀 Бот запущен и слушает обновления...")
    await app_telegram.run_polling()

# --- Flask сервер в отдельном потоке ---
def start_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=start_flask, daemon=True).start()
    asyncio.run(run_bot())


