import os
import logging
import json
import aiohttp
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


url_routes = os.getenv('URL_ROUTES')
url_late = os.getenv('URL_LATE')
token = os.getenv('TOKEN')


async def get_routes(date):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "token": token,
                "date": date
            }
            logger.info(f"Дата: {date}")
            headers = {'Content-Type': 'application/json'}
            logger.info("Отправа запроса на роуты")
            async with session.post(url_routes, data=json.dumps(payload), headers=headers) as response:
                logger.info(
                    f"Статус: {response.status}")
                if response.status == 200:
                    text_response = await response.text()  # Получаем текст
                    logger.info(f"Полученный ответ: {text_response}")
                    try:
                        # Пробуем преобразовать в JSON
                        return json.loads(text_response)
                    except json.JSONDecodeError as json_error:
                        logger.error(
                            f"Ошибка при декодировании JSON: {json_error}")
                        return {'error': f"Неправильный формат ответа: {text_response}"}
                else:

                    text_response = await response.content()  # Получаем текст
                    logger.info(f"Полученный ответ: {text_response}")
                    return {'error': f"HTTP Error: {response.status}"}
    except Exception as e:
        logger.error(f"Ошибка при выполнении POST запроса: {e}")
        return {'error': str(e)}
