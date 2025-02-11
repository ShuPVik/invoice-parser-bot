import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers import router  # Импортируем router из handlers
from utils import get_main_keyboard
from logger import logger
# Загрузить переменные окружения
load_dotenv()
API_TOKEN = os.getenv('TG_API_TOKEN')

# Создаем объекты бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Регистрируем router с хендлерами
dp.include_router(router)


async def on_startup(dispatcher: Dispatcher):
    """Функция запуска бота, устанавливает клавиатуру по умолчанию"""
    logger.info("Клаиватура установлена")
    dispatcher["default_reply_markup"] = get_main_keyboard()


async def main():
    logger.info('Бот запущен')
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
