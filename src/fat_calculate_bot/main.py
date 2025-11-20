import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
    await update.message.reply_text(
        "Привет! 👋 Я — Калькулятор БЖУ и калорий.\n"
        "Я помогу рассчитать твою суточную норму питания.\n\n"
        "Введи /cancel в любой момент, чтобы остановить.",
        reply_markup=ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER

# Обработка пола
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    if "Мужской" in user_input:
        context.user_data["gender"] = "м"
    elif "Женский" in user_input:
        context.user_data["gender"] = "ж"
    else:
        await update.message.reply_text("Пожалуйста, выберите из кнопок.")
        return GENDER

    await update.message.reply_text("Введите ваш возраст (полных лет):", reply_markup=ReplyKeyboardRemove())
    return AGE

# Обработка возраста
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age_val = int(update.message.text)
        if age_val < 1 or age_val > 120:
            raise ValueError
        context.user_data["age"] = age_val
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректный возраст (от 1 до 120).")
        return AGE

    await update.message.reply_text("Введите ваш вес (в кг):")
    return WEIGHT

# Обработка веса
async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight_val = float(update.message.text)
        if weight_val <= 0 or weight_val > 300:
            raise ValueError
        context.user_data["weight"] = weight_val
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректный вес (например: 70.5).")
        return WEIGHT

    await update.message.reply_text("Введите ваш рост (в см):")
    return HEIGHT

# Обработка роста
async def height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height_val = float(update.message.text)
        if height_val <= 0 or height_val > 250:
            raise ValueError
        context.user_data["height"] = height_val
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректный рост (например: 175).")
        return HEIGHT

    await update.message.reply_text(
        "Какова ваша цель?",
        reply_markup=ReplyKeyboardMarkup(goal_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GOAL

# Обработка цели
async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Похудение" in text:
        context.user_data["goal"] = "1"
    elif "Поддержание" in text:
        context.user_data["goal"] = "2"
    elif "Набор массы" in text:
        context.user_data["goal"] = "3"
    else:
        await update.message.reply_text("Пожалуйста, выберите цель из кнопок.")
        return GOAL

    await update.message.reply_text(
        "Выберите уровень физической активности:",
        reply_markup=ReplyKeyboardMarkup(activity_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ACTIVITY

# Обработка активности и расчёт
async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    activity_map = {
        "1. Минимальная": "1",
        "2. Лёгкая": "2",
        "3. Средняя": "3",
        "4. Высокая": "4",
        "5. Экстремальная": "5",
    }
    if text not in activity_map:
        await update.message.reply_text("Пожалуйста, выберите активность из кнопок.")
        return ACTIVITY

    context.user_data["activity"] = activity_map[text]

    # Расчёт
    data = context.user_data
    gender = data["gender"]
    age = data["age"]
    weight = data["weight"]
    height = data["height"]
    goal = data["goal"]
    activity = data["activity"]

    # BMR
    if gender == "м":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Multiplier
    mult = {"1": 1.2, "2": 1.375, "3": 1.55, "4": 1.725, "5": 1.9}[activity]
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
        "✅ Ваш расчёт готов!\n\n"
        f"• Калории: {calories} ккал\n"
        f"• Белки: {protein} г\n"
        f"• Жиры: {fat} г\n"
        f"• Углеводы: {carbs} г\n\n"
        "💡 Совет: эти значения — ориентир. "
        "Корректируйте под самочувствие и результаты!"
    )

    await update.message.reply_text(result, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Расчёт отменён. Введи /start, чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
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