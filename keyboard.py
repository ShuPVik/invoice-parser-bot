import logging
import os
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import types, F
from aiogram import Bot
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


@router.message(F.text == "/remove_keyboard")
async def remove_keyboard(message: types.Message):
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


def format_route_info(data: dict) -> str:
    return (
        f"*🚍 Номер рейса:* `{data['number']}`\n"
        f"*📍 Маршрут:* {data['name']}\n"
        f"*👤 Водитель:* {data['user']}\n"
        f"*🚗 Авто:* {data['auto']}"
    )


async def send_routes(user_id, routes, bot: Bot):
    for route in routes:
        text = format_route_info(route)
        await bot.send_message(
            user_id,
            text=text,
            # Текст с описанием
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Получить детали", callback_data=f"details:{route['number']}")],
                    [InlineKeyboardButton(
                        text="Рейс задерживается", callback_data=f"late:{route['number']}")]

                ]
            )
        )


# Обработчик callback-кнопок
@router.callback_query(lambda call: call.data.split(':')[0] in ["details", "late"])
async def handle_inline_button(call: types.CallbackQuery, bot: Bot):
    user_id = call.message.chat.id
    action, number = call.data.split(':')
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}.")
    try:
        if action == "details":
            await bot.send_message(user_id, text="Вы выбрали посмотреть детали")

        if action == "details":
            await bot.send_message(user_id, text="Вы выбрали, что рейс задеживается")
    except Exception as e:
        logger.error(
            f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}")
