import os
import sys
import types
from dotenv import load_dotenv
import threading
import asyncio
from flask import Flask

# 🔧 Имитация отсутствующего модуля imghdr (для Python 3.13)
if 'imghdr' not in sys.modules:
    fake_imghdr = types.ModuleType('imghdr')
    fake_imghdr.what = lambda *args, **kwargs: None
    sys.modules['imghdr'] = fake_imghdr

# ✅ Добавляем путь к текущей директории
sys.path.append(os.path.dirname(__file__))

# --- Импорт Telegram API ---
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# ✅ Загрузка .env (Render и локально)
if os.path.exists("/etc/secrets/.env"):
    load_dotenv("/etc/secrets/.env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-4986401168"))

print("DEBUG: BOT_TOKEN =", BOT_TOKEN)
print("DEBUG: GROUP_ID =", GROUP_ID)

# --- Константы для этапов анкеты ---
NAME, AGE, CITIZENSHIP, FROM_COUNTRY, DATES, PEOPLE, PURPOSE, CONTACT = range(8)

# --- Flask ---
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "OK", 200

@flask_app.route("/health")
def health():
    return "healthy", 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)


# --- Telegram handlers ---
async def greet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "друг"
    keyboard = [["🚀 Начать анкету"]]
    try:
        with open("usa_flag.jpg", "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=(f"👋 Привет, {name}! 🇺🇸\n\n"
                         "Я помогу вам с легальной иммиграцией в США.\n\n"
                         "Нажмите кнопку ниже, чтобы начать заполнение анкеты 👇"),
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
    except FileNotFoundError:
        await update.message.reply_text(
            f"👋 Привет, {name}! 🇺🇸\n\n"
            "Я помогу вам с легальной иммиграцией в США.\n\n"
            "Нажмите кнопку ниже, чтобы начать заполнение анкеты 👇",
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

    await update.message.reply_text("🕐 Обрабатываем заявку...")
    await asyncio.sleep(1)
    await context.bot.send_message(chat_id=GROUP_ID, text=message, parse_mode="HTML")
    await update.message.reply_text("✅ Спасибо! Ваша заявка отправлена.")
    await asyncio.sleep(1)
    await greet(update, context)
    return ConversationHandler.END


# --- Основной запуск ---
async def run_bot():
    if not BOT_TOKEN:
        print("❌ Ошибка: переменная окружения BOT_TOKEN не задана!")
        return

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

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

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, greet))

    print("🚀 Бот запущен (async polling)...")
    await application.run_polling(close_loop=False)


if __name__ == "__main__":
    # Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Асинхронный запуск бота
    asyncio.run(run_bot())
