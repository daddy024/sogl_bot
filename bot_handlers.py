from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler

# Определение состояний разговора
DISTRICT, SUBJECT, PASSWORD = range(3)  # Добавили PASSWORD

# Пароль для доступа к боту
BOT_PASSWORD = "1234"

# Локальное хранилище пользователей (заменяемым на БД)
user_data = {}

async def start(update: Update, context: CallbackContext) -> int:
    """Обрабатывает команду /start и показывает приветственное сообщение"""
    user_id = update.message.from_user.id
    
    # Проверяем, есть ли пользователь в базе
    if user_id in user_data and user_data[user_id].get("authenticated", False):
        await update.message.reply_text("Вы уже авторизованы. Выберите федеральный округ:")
        return DISTRICT

    # Приветственное сообщение с кнопкой "Начать"
    keyboard = [["🚀 Начать"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Привет! Этот бот предназначен для XYZ.\n\n"
        "Чтобы начать, нажмите кнопку ниже 👇",
        reply_markup=reply_markup
    )
    return PASSWORD  # Переводим пользователя в этап ввода пароля

async def handle_password(update: Update, context: CallbackContext) -> int:
    """Обрабатывает ввод пароля"""
    user_id = update.message.from_user.id
    entered_password = update.message.text

    if entered_password == BOT_PASSWORD:
        user_data[user_id] = {"authenticated": True}
        await update.message.reply_text("✅ Пароль верный! Теперь выберите федеральный округ.", reply_markup=ReplyKeyboardRemove())
        return DISTRICT
    else:
        await update.message.reply_text("🚫 Неверный пароль. Попробуйте снова.")
        return PASSWORD  # Оставляем пользователя в режиме ожидания пароля

async def handle_district(update: Update, context: CallbackContext) -> int:
    """Обрабатывает выбор федерального округа"""
    from main import df
    selected_district = update.message.text
    context.user_data['selected_district'] = selected_district

    if df is None:
        await update.message.reply_text("Данные пока не загружены, попробуйте позже.")
        return ConversationHandler.END
    
    subjects = df[df['ФО'] == selected_district]['Субъект'].unique()
    if len(subjects) == 0:
        await update.message.reply_text("Для выбранного округа нет субъектов. Попробуйте выбрать другой округ.")
        return DISTRICT

    keyboard = [list(subjects[i:i + 2]) for i in range(0, len(subjects), 2)]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите субъект РФ:", reply_markup=reply_markup)
    
    return SUBJECT

async def handle_subject(update: Update, context: CallbackContext) -> int:
    """Обрабатывает выбор субъекта"""
    from main import df
    selected_subject = update.message.text

    if df is None:
        await update.message.reply_text("Данные пока не загружены, попробуйте позже.")
        return ConversationHandler.END

    matching_rows = df[df['Субъект'] == selected_subject]
    if matching_rows.empty:
        await update.message.reply_text("Выбранный субъект не найден. Пожалуйста, попробуйте ещё раз.")
        return SUBJECT

    status = matching_rows['Статус'].values[0]
    await update.message.reply_text(f"Статус субъекта {selected_subject}: {status}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Обрабатывает команду /cancel"""
    await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
