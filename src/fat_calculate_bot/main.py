import logging
import os
from typing import Any, Dict, cast

from telegram import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Попытка загрузить переменные из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv не установлен, используем системные переменные окружения

# Включим логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

UserData = Dict[str, Any]


def _ensure_user_data(context: ContextTypes.DEFAULT_TYPE) -> UserData:
    user_data = context.user_data
    if user_data is None:
        raise ValueError("user_data is not available on the context.")
    return cast(UserData, user_data)


def _require_message(update: Update) -> Message:
    message = update.message
    if message is None:
        raise ValueError("Update does not contain a message.")
    return message

# Этапы диалога
GENDER, AGE, WEIGHT, HEIGHT, GOAL, ACTIVITY = range(6)

# Клавиатуры
gender_keyboard = [["Мужской", "Женский"]]
goal_keyboard = [["Похудение", "Поддержание", "Набор массы"]]
activity_keyboard = [
    ["1. Минимальная"],
    ["2. Лёгкая"],
    ["3. Средняя"],
    ["4. Высокая"],
    ["5. Экстремальная"],
]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    await message.reply_text(
        "Привет! 👋 Я — Калькулятор БЖУ и калорий.\n"
        "Я помогу рассчитать твою суточную норму питания.\n\n"
        "Введи /cancel в любой момент, чтобы остановить.",
        reply_markup=ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER

# Обработка пола
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    user_input = message.text
    if user_input is None:
        await message.reply_text("Пожалуйста, выберите из кнопок.")
        return GENDER


    user_data = _ensure_user_data(context)
    if "Мужской" in user_input:
        user_data["gender"] = "м"
    elif "Женский" in user_input:
        user_data["gender"] = "ж"
    else:
        await message.reply_text("Пожалуйста, выберите из кнопок.")
        return GENDER

    await message.reply_text("Введите ваш возраст (полных лет):", reply_markup=ReplyKeyboardRemove())
    return AGE

# Обработка возраста
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    raw_text = message.text
    if raw_text is None:
        await message.reply_text("Пожалуйста, введите корректный возраст (от 1 до 120).")
        return AGE

    try:
        age_val = int(raw_text)
        if age_val < 1 or age_val > 120:
            raise ValueError
        _ensure_user_data(context)["age"] = age_val
    except ValueError:
        await message.reply_text("Пожалуйста, введите корректный возраст (от 1 до 120).")
        return AGE

    await message.reply_text("Введите ваш вес (в кг):")
    return WEIGHT

# Обработка веса
async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    raw_text = message.text
    if raw_text is None:
        await message.reply_text("Пожалуйста, введите корректный вес (например: 70.5).")
        return WEIGHT

    try:
        weight_val = float(raw_text)
        if weight_val <= 0 or weight_val > 300:
            raise ValueError
        _ensure_user_data(context)["weight"] = weight_val
    except ValueError:
        await message.reply_text("Пожалуйста, введите корректный вес (например: 70.5).")
        return WEIGHT

    await message.reply_text("Введите ваш рост (в см):")
    return HEIGHT

# Обработка роста
async def height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    raw_text = message.text
    if raw_text is None:
        await message.reply_text("Пожалуйста, введите корректный рост (например: 175).")
        return HEIGHT

    try:
        height_val = float(raw_text)
        if height_val <= 0 or height_val > 250:
            raise ValueError
        _ensure_user_data(context)["height"] = height_val
    except ValueError:
        await message.reply_text("Пожалуйста, введите корректный рост (например: 175).")
        return HEIGHT

    await message.reply_text(
        "Какова ваша цель?",
        reply_markup=ReplyKeyboardMarkup(goal_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GOAL

# Обработка цели
async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    text = message.text
    if text is None:
        await message.reply_text("Пожалуйста, выберите цель из кнопок.")
        return GOAL

    user_data = _ensure_user_data(context)
    if "Похудение" in text:
        user_data["goal"] = "1"
    elif "Поддержание" in text:
        user_data["goal"] = "2"
    elif "Набор массы" in text:
        user_data["goal"] = "3"
    else:
        await message.reply_text("Пожалуйста, выберите цель из кнопок.")
        return GOAL

    await message.reply_text(
        "Выберите уровень физической активности:",
        reply_markup=ReplyKeyboardMarkup(activity_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ACTIVITY

# Обработка активности и расчёт
async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    text = message.text
    if text is None:
        await message.reply_text("Пожалуйста, выберите активность из кнопок.")
        return ACTIVITY

    user_data = _ensure_user_data(context)
    activity_map = {
        "1. Минимальная": "1",
        "2. Лёгкая": "2",
        "3. Средняя": "3",
        "4. Высокая": "4",
        "5. Экстремальная": "5",
    }
    if text not in activity_map:
        await message.reply_text("Пожалуйста, выберите активность из кнопок.")
        return ACTIVITY

    user_data["activity"] = activity_map[text]

    # Расчёт
    gender = user_data["gender"]
    age = user_data["age"]
    weight = user_data["weight"]
    height = user_data["height"]
    goal = user_data["goal"]
    activity_value = user_data["activity"]

    # BMR
    if gender == "м":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Multiplier
    mult = {"1": 1.2, "2": 1.375, "3": 1.55, "4": 1.725, "5": 1.9}[activity_value]
    tdee = bmr * mult

    # Цель
    if goal == "1":
        calories = tdee * 0.85
    elif goal == "3":
        calories = tdee * 1.15
    else:
        calories = tdee

    # БЖУ
    protein_per_kg = 2.2 if goal == "1" else (2.0 if goal == "3" else 1.6)
    protein = weight * protein_per_kg
    fat = calories * 0.3 / 9
    carbs = (calories - (protein * 4 + fat * 9)) / 4

    # Округление
    calories = round(calories)
    protein = round(protein)
    fat = round(fat)
    carbs = round(carbs)

    result = (
        "✅ Расчёт готов!\n\n"
        f"• Калории: {calories} ккал\n"
        f"• Белки: {protein} г\n"
        f"• Жиры: {fat} г\n"
        f"• Углеводы: {carbs} г\n\n"
        "Корректируй расчет под самочувствие и результаты и помни, что ты уже Чемпион! "
        "Стань лучшей версией себя при помощи дисциплины!"
    )

    await message.reply_text(result, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = _require_message(update)
    await message.reply_text("Расчёт отменён. Введи /start, чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Основная функция
def main():
    # Получаем токен из переменной окружения
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN не установлен. "
            "Установите переменную окружения или создайте .env файл с TELEGRAM_BOT_TOKEN=your_token"
        )

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal)],
            ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, activity)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("cancel", cancel))

    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()