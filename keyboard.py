import logging
import os
from typing import Callable, Awaitable, Dict, Any
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import Message
from aiogram import BaseMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot, types, F
from handlers import router

load_dotenv()

run_chats = os.getenv("RUN_CHATS").split(",")


@router.message(F.text == "Список рейсов на сегодня")
async def handle_button1(message: types.Message, bot: Bot):
    await message.answer("Вы нажали 'Кнопка 1'!")


@router.message(F.text == "Список рейсов на вчера")
async def handle_button2(message: types.Message, bot: Bot):
    await message.answer("Вы нажали 'Кнопка 2'!")


@router.message(F.text == "Скрыть клавиатуру")
async def remove_keyboard(message: types.Message, bot: Bot):
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


class KeyboardMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]) -> Any:
        """Добавляет клавиатуру после каждого текстового сообщения"""
        result = await handler(event, data)

        # Только для обычных текстовых сообщений
        if event.text:
            await event.answer(" ", reply_markup=get_main_keyboard())

        return result
