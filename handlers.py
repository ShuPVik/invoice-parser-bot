import logging
from aiogram import Bot, Router, types, F  # Используем F для фильтрации
from state import user_images, user_states  # Глобальные переменные для состояния
from image_processing import handle_image, invoice_processing  # Функции для обработки изображений
from aiogram.exceptions import TelegramForbiddenError

# Создаем роутер для регистрации хендлеров
router = Router()

@router.message(F.content_type == 'photo')
async def handle_photo(message: types.Message, bot: Bot):
    logging.info("Обработка фотографии.")
    user_id = int(message.from_user.id)
    try:
        await handle_image(message, user_id, is_document=False, bot=bot)
    except TelegramForbiddenError:
        logging.error(f"Бот не может отправить сообщение пользователю {user_id}. Возможно, бот заблокирован.")
    except Exception as e:
        logging.error(f"Ошибка при обработке фотографии от пользователя {user_id}: {e}")

@router.message(F.content_type == 'document')
async def handle_document(message: types.Message, bot: Bot):
    logging.info("Обработка документа.")
    user_id = int(message.from_user.id)
    file_name = message.document.file_name

    try:
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            await handle_image(message, user_id, is_document=True, bot=bot)
        else:
            logging.warning(f"Некорректный формат файла для пользователя {user_id}: {file_name}")
    except TelegramForbiddenError:
        logging.error(f"Бот не может отправить сообщение пользователю {user_id}. Возможно, бот заблокирован.")
    except Exception as e:
        logging.error(f"Ошибка при обработке документа от пользователя {user_id}: {e}")


# Обработчик callback-кнопок
@router.callback_query(lambda call: call.data.split(':')[0] in ["received", "delivered", "other"])
async def handle_inline_button(call: types.CallbackQuery, bot: Bot):
    user_id = call.message.chat.id
    action, image_id = call.data.split(':')
    logging.info(f"Получен запрос от пользователя {user_id} для изображения {image_id} с действием {action}.")
    try:
        if user_id not in user_images or int(image_id) not in user_images[user_id]:
            return
        image_data = user_images[user_id][int(image_id)]
        invoice = image_data['invoice']
        message_id = image_data.get('message_id')
        logging.info(f"Получен message_id.{message_id}")
        logging.info(f"Обработка статуса '{action}' для накладной {invoice} от пользователя {user_id}.")
        text = await invoice_processing(invoice, image_data.get('base64_image'), image_data.get('file_extension'), action)
        await call.answer(text)

        # Удаляем предыдущее сообщение
        await bot.delete_message(chat_id=user_id, message_id=image_data['new_message_id'])

        # Отправляем новое сообщение с ответом на оригинальное
        await bot.send_message(
            chat_id=user_id,
            text=f"Обработка завершена для накладной {invoice}.",
            reply_to_message_id=image_data['message_id']  # Ответ на оригинальное сообщение
        )
        

        del user_images[user_id][int(image_id)]

        if not user_images[user_id]:
            del user_states[user_id]

    except Exception as e:
        logging.error(f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}")
