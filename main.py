import os
import logging
from dotenv import load_dotenv
import nest_asyncio
nest_asyncio.apply()

from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler
)
from apscheduler.schedulers.background import BackgroundScheduler
from data_updater import YANDEX_PUBLIC_URL, download_xlsx_from_yadisk

# Импортируем обработчики
from bot_handlers import start, handle_district, handle_subject, cancel, DISTRICT, SUBJECT

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

def main():
    """Запуск бота"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DISTRICT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_district)],
            SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()