import logging
import os
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot, types, F
from handlers import router

load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

run_chats = os.getenv("ROUTER_CHATS").split(",")

# ✅ Отображаем клавиатуру при команде /keyboard


@router.message(F.text == "/keyboard")
async def show_keyboard(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} вызвал клавиатуру")
    await message.answer("Выберите опцию:", reply_markup=get_main_keyboard())


@router.message(F.text == "Список рейсов на сегодня")
async def handle_button1(message: types.Message, bot: Bot):
    logger.info(
        f"Пользователь {message.from_user.id} нажал 'Список рейсов на сегодня'")
    await message.answer("Вы нажали 'Список рейсов на сегодня'!")


@router.message(F.text == "Список рейсов на вчера")
async def handle_button2(message: types.Message, bot: Bot):
    logger.info(
        f"Пользователь {message.from_user.id} нажал 'Список рейсов на вчера'")
    await message.answer("Вы нажали 'Список рейсов на вчера'!")


@router.message(F.text == "/remove_keyboard")
async def remove_keyboard(message: types.Message, bot: Bot):
    logger.info(f"Пользователь {message.from_user.id} скрыл клавиатуру")
    await message.answer("Клавиатура скрыта!", reply_markup=ReplyKeyboardRemove())


# Создаём клавиатуру
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Список рейсов на сегодня")],
            [KeyboardButton(text="Список рейсов на вчера")]
        ],
        resize_keyboard=True,  # Уменьшает клавиатуру под размер экрана
        one_time_keyboard=False  # Оставляет клавиатуру на экране
    )
    return keyboard
