import logging
import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Загрузка .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Этапы диалога
GENDER, WEIGHT, GOAL = range(3)

# Клавиатуры
gender_keyboard = [["Мужчина", "Женщина"]]
goal_keyboard = [["Похудение", "Поддержание", "Набор массы"]]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я — Калькулятор БЖУ.\n\n"
        "Я помогу рассчитать твою норму белков, жиров и углеводов.\n\n"
        "Сначала выбери свой пол:",
        reply_markup=ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER


async def gender_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ["Мужчина", "Женщина"]:
        await update.message.reply_text("Пожалуйста, выбери пол из кнопок.")
        return GENDER

    context.user_data["gender"] = "м" if text == "Мужчина" else "ж"
    await update.message.reply_text(
        "Отлично! Теперь введи свой вес в килограммах (например: 70 или 65.5):",
        reply_markup=ReplyKeyboardRemove()
    )
    return WEIGHT


async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        weight = float(text)
        if weight <= 0 or weight > 300:
            raise ValueError
        context.user_data["weight"] = weight
    except (ValueError, TypeError):
        await update.message.reply_text("Пожалуйста, введи корректный вес (например: 70.5)")
        return WEIGHT

    await update.message.reply_text(
        "Какова твоя цель?",
        reply_markup=ReplyKeyboardMarkup(goal_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GOAL


async def goal_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    weight = context.user_data["weight"]

    if text == "Похудение":
        protein = weight * 2.2
        carbs = weight * 2
    elif text == "Набор массы":
        protein = weight * 2.0
        carbs = weight * 4
    elif text == "Поддержание":
        protein = weight * 2.0
        carbs = weight * 3
    else:
        await update.message.reply_text("Пожалуйста, выбери цель из кнопок.")
        return GOAL

    # Жиры — всегда вес × 1 (для всех!)
    fat = weight * 1

    # Округляем
    protein = round(protein)
    fat = round(fat)
    carbs = round(carbs)

    # Считаем калории для информации
    calories = round(protein * 4 + fat * 9 + carbs * 4)

    result = (
        "✅ Твой расчёт готов!\n\n"
        f"• Калории: {calories} ккал\n"
        f"• Белки: {protein} г\n"
        f"• Жиры: {fat} г\n"
        f"• Углеводы: {carbs} г\n\n"
        "Ты уже чемпион!\n"
        "Стань лучшей версией себя с дисциплиной 💪"
    )

    await update.message.reply_text(result, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Расчёт отменён. Напиши /start, чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден. Добавь его в .env файл.")

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_input)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_input)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))  # позволяет перезапускать в любой момент

    print("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
