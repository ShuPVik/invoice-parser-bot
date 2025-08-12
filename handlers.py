import logging
import os

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramForbiddenError
from dotenv import load_dotenv

from image_processing import handle_image, invoice_processing
from state import images

logger = logging.getLogger("telegram_bot")
# Создаем роутер для регистрации хендлеров
router = Router()

load_dotenv()

not_allowed_chats = os.getenv("NOT_ALLOWED_CHATS", "").split(",")

# Обработчик текстовых сообщений


@router.message(F.content_type == "photo")
async def handle_photo(message: types.Message, bot: Bot):
    logger.info("Обработка фотографии.")
    user_id = message.chat.id
    # Берем самое большое изображение
    if not message.photo:
        raise ValueError

    try:
        if user_id not in not_allowed_chats:
            await handle_image(message, user_id, is_document=False, bot=bot)
    except TelegramForbiddenError:
        logger.error(
            f"""Бот не может отправить сообщение пользователю 
            {user_id}. Возможно, бот заблокирован."""
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке фотографии от пользователя {user_id}: {e}")


@router.message(F.content_type == "document")
async def handle_document(message: types.Message, bot: Bot):
    logger.info("Обработка документа.")
    user_id = message.chat.id
    file_name = message.document.file_name

    try:
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            if user_id not in not_allowed_chats:
                await handle_image(message, user_id, is_document=True, bot=bot)
    except TelegramForbiddenError:
        logger.error(f"Бот не может отправить сообщение пользователю {user_id}. Возможно, бот заблокирован.")
    except Exception as e:
        logger.error(f"Ошибка при обработке документа от пользователя {user_id}: {e}")


# Обработчик callback-кнопок
@router.callback_query(lambda call: call.data.split(":")[0] in ["received", "delivered", "other"])
async def handle_inline_button(call: types.CallbackQuery, bot: Bot):
    user_id = call.message.chat.id
    action, image_id = call.data.split(":")
    logger.info(f"Получен запрос от пользователя {user_id} для изображения {image_id} с действием {action}.")
    try:
        if image_id not in images:
            return
        image_data = images[image_id]
        invoice = image_data["invoice"]
        message_id = image_data.get("message_id")
        logger.info(f"Получен message_id.{message_id}")
        logger.info(f"Обработка статуса '{action}' для накладной {invoice} от пользователя {user_id}.")
        text, bot_message = await invoice_processing(
            invoice,
            image_data.get("base64_image"),
            image_data.get("file_extension"),
            action,
        )
        await call.answer(text)

        # Удаляем предыдущее сообщение
        await bot.delete_message(chat_id=image_data["user_id"], message_id=image_data["new_message_id"])

        # Отправляем новое сообщение с ответом на оригинальное
        await bot.send_message(
            chat_id=image_data["user_id"],
            text=f"{bot_message}",
            # Ответ на оригинальное сообщение
            reply_to_message_id=image_data["message_id"],
        )

        del images[image_id]

    except Exception as e:
        logger.error(f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}")
