from config import PASSWORD
from bot_handlers import handle_password
import nest_asyncio
nest_asyncio.apply()

import pandas as pd
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler
)
from apscheduler.schedulers.background import BackgroundScheduler
from data_updater import download_xlsx_from_yadisk, YANDEX_PUBLIC_URL

# Импортируем обработчики
from bot_handlers import start, handle_district, handle_subject, cancel, DISTRICT, SUBJECT

# Глобальная переменная для хранения данных
df = None

def update_data():
    global df
    try:
        df = download_xlsx_from_yadisk(YANDEX_PUBLIC_URL)
        print("Данные успешно обновлены.")
    except Exception as e:
        print("Ошибка при обновлении данных:", e)

# Запуск планировщика для обновления данных каждые 5 минут
scheduler = BackgroundScheduler()
scheduler.add_job(update_data, 'interval', minutes=5)
scheduler.start()

# Начальная загрузка данных
update_data()

def main():
    application = ApplicationBuilder().token("7779772136:AAHjgVqi4pJhc80qjgWHm1ioTitZOvlhDFw").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
            DISTRICT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_district)],
            SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
