from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

# Определение состояний разговора
DISTRICT, SUBJECT = range(2)

# Предполагается, что df – глобальная переменная, обновляемая в основном модуле или импортированная из data_updater

async def start(update: Update, context: CallbackContext) -> int:
    from main import df  # Импортируем глобальную переменную из основного модуля (или можно передавать её через context)
    if df is None:
        await update.message.reply_text("Данные пока не загружены, попробуйте позже.")
        return ConversationHandler.END
    districts = df['ФО'].unique()
    keyboard = [list(districts[i:i + 2]) for i in range(0, len(districts), 2)]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите федеральный округ:", reply_markup=reply_markup)
    return DISTRICT

async def handle_district(update: Update, context: CallbackContext) -> int:
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
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END
