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

# Текст кнопки — изменено на "Перерасчёт"
RESTART_BUTTON = "🔄 Перерасчёт"

# Клавиатуры с новой кнопкой
gender_keyboard = [["Мужчина", "Женщина"], [RESTART_BUTTON]]
goal_keyboard = [["Похудение", "Поддержка", "Набор"], [RESTART_BUTTON]]
weight_keyboard = [[RESTART_BUTTON]]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я — Калькулятор БЖУ.\n\n"
        "Я помогу рассчитать твою суточную потребность в калориях, белках, жирах и углеводах.\n\n"
        "Сначала выбери свой пол:",
        reply_markup=ReplyKeyboardMarkup(
            gender_keyboard,
            one_time_keyboard=False,
            resize_keyboard=True
        )
    )
    return GENDER


async def restart_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапускает расчёт с самого начала"""
    await update.message.reply_text(
        "🔄 Начинаем заново!\n\nВыбери свой пол:",
        reply_markup=ReplyKeyboardMarkup(
            gender_keyboard,
            one_time_keyboard=False,
            resize_keyboard=True
        )
    )
    return GENDER


async def gender_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == RESTART_BUTTON:
        return await restart_flow(update, context)

    if text not in ["Мужчина", "Женщина"]:
        await update.message.reply_text("Пожалуйста, выбери пол из кнопок.")
        return GENDER

    context.user_data["gender"] = "м" if text == "Мужчина" else "ж"
    await update.message.reply_text(
        "Отлично! Теперь введи свой вес в килограммах (например: 70 или 65.5):",
        reply_markup=ReplyKeyboardMarkup(
            weight_keyboard,
            one_time_keyboard=False,
            resize_keyboard=True
        )
    )
    return WEIGHT


async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == RESTART_BUTTON:
        return await restart_flow(update, context)

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
        reply_markup=ReplyKeyboardMarkup(
            goal_keyboard,
            one_time_keyboard=False,
            resize_keyboard=True
        )
    )
    return GOAL


async def goal_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == RESTART_BUTTON:
        return await restart_flow(update, context)

    weight = context.user_data.get("weight")
    if weight is None:
        await update.message.reply_text("Произошла ошибка. Напиши /start, чтобы начать заново.")
        return ConversationHandler.END

    if text == "Похудение":
        protein = weight * 2.2
        carbs = weight * 2
    elif text == "Набор":
        protein = weight * 2.0
        carbs = weight * 4
    elif text == "Поддержка":
        protein = weight * 2.0
        carbs = weight * 3
    else:
        await update.message.reply_text("Пожалуйста, выбери цель из кнопок.")
        return GOAL

    fat = weight * 1
    protein = round(protein)
    fat = round(fat)
    carbs = round(carbs)
    calories = round(protein * 4 + fat * 9 + carbs * 4)

    result = (
        "✅ Твой расчёт готов!\n\n"
        f"• Калории: {calories} ккал\n"
        f"• Белки: {protein} г\n"
        f"• Жиры: {fat} г\n"
        f"• Углеводы: {carbs} г\n\n"
        "Ты уже Чемпион!\n"
        "Стань лучшей версией себя с дисциплиной 💪"
    )

    await update.message.reply_text(
        result,
        reply_markup=ReplyKeyboardMarkup(
            [[RESTART_BUTTON]],
            one_time_keyboard=False,
            resize_keyboard=True
        )
    )
    return GOAL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Расчёт отменён. Нажми «🔄 Перерасчёт» или /start.",
        reply_markup=ReplyKeyboardMarkup(
            [[RESTART_BUTTON]],
            resize_keyboard=True
        )
    )
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
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))

    print("✅ Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
