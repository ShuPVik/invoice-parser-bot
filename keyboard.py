import logging
import os
import asyncio
import datetime
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import types, F
from aiogram import Bot
import pytz
from handlers import router, tz_novosibirsk

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


# Загружаем текст маршрута по номеру рейса (можно из базы данных или словаря)
routes_data = {
}


async def clear_routes_data():
    while True:
        now = datetime.datetime.now(pytz.utc).astimezone(
            tz_novosibirsk)  # Текущее время в Новосибирске
        # Следующая очистка в 07:00
        next_run = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if now >= next_run:  # Если уже после 07:00, назначаем на следующий день
            next_run += datetime.timedelta(days=1)

        wait_time = (next_run - now).total_seconds()  # Время до очистки

        logger.info(
            f"⏳ Ожидание до следующей очистки данных в 07:00 Новосибирска ({next_run}). Осталось {wait_time} секунд.")
        await asyncio.sleep(wait_time)

        routes_data.clear()
        logger.info("🚮 Данные маршрутов очищены!")


async def send_routes(user_id, routes, bot: Bot):
    for route in routes:
        text = format_route_info(route)
        routes_data[f'{route['number']}'] = text
        await bot.send_message(
            user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📋 Детали", callback_data=f"details:{route['number']}")],
                    [InlineKeyboardButton(
                        text="⚠️ Сообщить о задержке", callback_data=f"late:{route['number']}")]
                ]
            )
        )


# Обработчик callback-кнопок

@router.callback_query(lambda call: call.data.split(':')[0] in ["details", "late"])
async def handle_inline_button(call: types.CallbackQuery):
    user_id = call.message.chat.id
    action, number = call.data.split(':')  # Убрали text из callback_data
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}.")

    text = routes_data.get(number, "Информация о рейсе не найдена.")

    try:
        if action == "details":
            await call.message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🔙 Назад", callback_data=f"back:{number}")]
                ])
            )

        elif action == "late":
            await call.message.edit_text(
                text=f"⚠️ Вы уверены, что хотите сообщить о задержке рейса {number}?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Да", callback_data=f"yes:{number}")],
                    [InlineKeyboardButton(
                        text="🔙 Назад", callback_data=f"back:{number}")]
                ])
            )

        await call.answer()

    except Exception as e:
        logger.error(
            f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}")


# Обработчик callback-кнопок
@router.callback_query(lambda call: call.data.split(':')[0] in ["yes", "no", "back"])
async def handle_yes_no_button(call: types.CallbackQuery):
    user_id = call.message.chat.id
    action, number = call.data.split(':')
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}.")
    try:
        if action == "yes":
            await call.message.edit_text(text="Уведоление успешно отправлено")

        elif action == "back":
            await call.message.edit_text(
                text=f"🚌 Информация о рейсе {number}.{routes_data[number]}\nВыберите действие:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📋 Детали", callback_data=f"details:{number}")],
                    [InlineKeyboardButton(
                        text="⚠️ Сообщить о задержке", callback_data=f"late:{number}")]
                ])
            )

        await call.answer()
    except Exception as e:
        logger.error(
            f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}")
