import os
import logging
from dotenv import load_dotenv
import nest_asyncio
nest_asyncio.apply()

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, CallbackContext
)
from apscheduler.schedulers.background import BackgroundScheduler
from data_updater import download_xlsx_from_yadisk, YANDEX_PUBLIC_URL

# Определение состояний разговора
DISTRICT, SUBJECT = range(2)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Ошибка: Токен не загружен из .env!")

# Глобальная переменная для хранения данных
df = None

def update_data():
    """Обновляет данные из Яндекс.Диска"""
    global df
    try:
        df = download_xlsx_from_yadisk(YANDEX_PUBLIC_URL)
        logger.info("✅ Данные успешно обновлены.")
    except Exception as e:
        logger.error(f"⚠️ Ошибка при обновлении данных: {e}")

# Запуск планировщика для обновления данных каждые 5 минут
scheduler = BackgroundScheduler()
scheduler.add_job(update_data, 'interval', minutes=5)
scheduler.start()

# Остановка планировщика при завершении работы
import atexit
atexit.register(scheduler.shutdown)

# Начальная загрузка данных
update_data()

async def start(update: Update, context: CallbackContext) -> int:
    """Приветственное сообщение и выбор округа"""
    global df
    if df is None or 'ФО' not in df.columns:
        await update.message.reply_text("Данные пока не загружены, попробуйте позже.")
        return ConversationHandler.END
    
    districts = df['ФО'].dropna().unique().tolist()
    if not districts:
        await update.message.reply_text("Нет доступных федеральных округов.")
        return ConversationHandler.END
    
    district_keyboard = [[str(district)] for district in districts]
    menu_keyboard = [["🔄 Начать заново"]]
    
    await update.message.reply_text(
        "👋 Привет! Этот бот предназначен для мониторинга статуса подписания ПГС.\n\nВыберите федеральный округ:",
        reply_markup=ReplyKeyboardMarkup(district_keyboard + menu_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return DISTRICT

async def menu(update: Update, context: CallbackContext) -> int:
    """Обрабатывает нажатие кнопки 'Начать заново'"""
    return await start(update, context)

async def handle_district(update: Update, context: CallbackContext) -> int:
    """Обрабатывает выбор федерального округа"""
    global df
    selected_district = update.message.text
    if selected_district == "🔄 Начать заново":
        return await menu(update, context)
    
    context.user_data['selected_district'] = selected_district
    logger.info(f"Пользователь выбрал федеральный округ: {selected_district}")

    if df is None or 'ФО' not in df.columns or 'Субъект' not in df.columns:
        await update.message.reply_text("Данные пока не загружены, попробуйте позже.")
        return ConversationHandler.END

    subjects = df[df['ФО'] == selected_district]['Субъект'].dropna().unique().tolist()
    if not subjects:
        await update.message.reply_text("Для выбранного округа нет субъектов. Попробуйте выбрать другой округ.")
        return DISTRICT

    # Формируем клавиатуру с субъектами
    keyboard = [[str(subject)] for subject in subjects]
    
    logger.info(f"Формируем клавиатуру субъектов: {keyboard}")
    
    await update.message.reply_text(
        "Выберите субъект РФ:",
        reply_markup=ReplyKeyboardMarkup(keyboard + [["🔄 Начать заново"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return SUBJECT

async def handle_subject(update: Update, context: CallbackContext) -> int:
    """Обрабатывает выбор субъекта"""
    global df
    selected_subject = update.message.text
    
    if selected_subject == "🔄 Начать заново":
        return await menu(update, context)
    
    logger.info(f"Пользователь выбрал субъект: {selected_subject}")

    if df is None or 'Субъект' not in df.columns or 'Статус' not in df.columns:
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
