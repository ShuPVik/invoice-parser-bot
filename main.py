import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers import router  # Импортируем router из handlers
from keyboard import get_main_keyboard
from logger import logger
# Загрузить переменные окружения
load_dotenv()
API_TOKEN = os.getenv('TG_API_TOKEN')

# Создаем объекты бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Регистрируем router с хендлерами
dp.include_router(router)


async def main():
    logger.info('Бот запущен')
    # await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
