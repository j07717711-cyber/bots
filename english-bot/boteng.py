import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)

BOT_TOKEN = "7592766307:AAGDkqHAx9MFDpN_NEt507UAPsSG9gZffpU"  
GROUP_ID = -4805955822  

NAME, AGE, CITIZENSHIP, FROM_COUNTRY, DATES, PEOPLE, PURPOSE, CONTACT = range(8)


# --- GREETING (only for private chats) ---
async def greet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    user = update.effective_user
    name = user.first_name or user.username or "friend"
    keyboard = [["🚀 Start Application"]]
    with open("usa_flag.jpg", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=(
                f"👋 Hello, {name}! 🇺🇸\n\n"
                "I’ll help you with the legal immigration process to the USA.\n\n"
                "Click the button below to start your application 👇"
            ),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )


# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await greet(update, context)


# --- APPLICATION FORM ---
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("What is your full name?", reply_markup=ReplyKeyboardRemove())
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("How old are you?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("What is your citizenship?")
    return CITIZENSHIP


async def get_citizenship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["citizenship"] = update.message.text
    await update.message.reply_text("What country are you departing from?")
    return FROM_COUNTRY


async def get_from_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["from_country"] = update.message.text
    await update.message.reply_text("Preferred departure dates?")
    return DATES


async def get_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dates"] = update.message.text
    await update.message.reply_text("How many people are traveling?")
    return PEOPLE


async def get_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["people"] = update.message.text
    reply_keyboard = [
        ["Political Asylum", "Talent Visa"],
        ["Legalization", "Automatic Transition"]
    ]
    await update.message.reply_text(
        "What is the purpose of your travel?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PURPOSE


async def get_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["purpose"] = update.message.text
    await update.message.reply_text(
        "Please leave your contact information (phone, email, or Telegram @username) so our manager can reach you:",
        reply_markup=ReplyKeyboardRemove()
    )
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text

    data = context.user_data
    message = (
        f"📋 <b>New Application:</b>\n\n"
        f"👤 Name: {data['name']}\n"
        f"🎂 Age: {data['age']}\n"
        f"🛂 Citizenship: {data['citizenship']}\n"
        f"🌍 From: {data['from_country']}\n"
        f"📅 Dates: {data['dates']}\n"
        f"👥 People: {data['people']}\n"
        f"🎯 Purpose: {data['purpose']}\n"
        f"📞 Contact: {data['contact']}"
    )

    processing = await update.message.reply_text("🕐 Processing your application...")
    await asyncio.sleep(2)
    await processing.delete()

    # Send to group WITHOUT keyboard
    await context.bot.send_message(chat_id=GROUP_ID, text=message, parse_mode="HTML")

    # Thank the user privately
    await update.message.reply_text("✅ Thank you! Your application has been submitted.")
    await asyncio.sleep(1)
    await update.message.reply_text("🤖 Our team is already reviewing your case!")
    await asyncio.sleep(1)

    # Return greeting only in private chat
    await greet(update, context)
    return ConversationHandler.END


# --- MAIN ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("(?i)(start application|🚀 start application)"), start_form)
        ],
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

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.ALL & ~filters.COMMAND, greet))

    print("🚀 Bot is running and waiting for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
