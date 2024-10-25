from dotenv import load_dotenv
import os
import openai 
from openai import AsyncOpenAI
import base64
import cv2
import numpy as np
from PIL import Image
import io
import pytesseract
import json
import requests
from utils import convert_image_to_base64
from prompt import prompt
import logging


logger = logging.getLogger(__name__)


load_dotenv()

def correct_skew(image):
    logger.debug("Попытка исправить наклон изображения.")
    # Преобразуем изображение в градации серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    # Определение координат текста и получение минимального ограничивающего угла
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]

    # Исправление угла
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    logger.debug(f"Обнаружен угол поворота: {angle} градусов.")

    # Поворот изображения для выравнивания текста
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    logger.info("Наклон изображения исправлен.")
    return rotated

# Обновляем функцию проверки ориентации текста
def check_text_orientation(image):
    logger.debug("Преобразование изображения в градации серого для проверки ориентации текста.")
    corrected_image = correct_skew(image)  # Исправляем наклон изображения перед проверкой текста
    gray = cv2.cvtColor(corrected_image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    logger.debug(f"Извлеченный текст: {text}")
    result = len(text) > 10
    logger.info(f"Ориентация текста {'правильная' if result else 'неправильная'} (количество символов: {len(text)}).")
    return result



# Поворот изображения на 90 градусов
def rotate_image_90_degrees(image, clockwise=False):
    direction = "по часовой стрелке" if clockwise else "против часовой стрелки"
    logger.info(f"Поворот изображения на 90 градусов {direction}.")
    if clockwise:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    else:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

# Извлечение номера накладной с помощью openai
async def get_invoice_from_image(base64_image):
    try:
        logger.info("Начало запроса к OpenAI для извлечения номера накладной.")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        content = response.choices[0].message.content
        logger.info(f"Успешно извлечен номер накладной: {content}")
        return content
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        return {"error": str(e)}

openai.api_key = os.getenv('OPENAI_API_KEY')
client = AsyncOpenAI()

# Асинхронная функция для обработки изображения и извлечения номера накладной
async def get_number_using_openai(cv_image):
    try:
        logger.info("Начало обработки изображения для извлечения номера накладной.")
        if not check_text_orientation(cv_image):
            logger.info("Текст не читается. Поворот изображения.")
            for attempt in range(3):
                cv_image = rotate_image_90_degrees(cv_image, clockwise=False)
                if check_text_orientation(cv_image):
                    logger.info(f"Текст стал читаемым после поворота (попытка {attempt + 1}).")
                    break
            else:
                logger.warning("Не удалось сделать текст читаемым после трех поворотов.")
        base64_image = convert_image_to_base64(cv_image)
        logger.debug("Изображение перекодировано обратно в base64 для отправки в OpenAI.")
        invoice_data = await get_invoice_from_image(base64_image)
        logger.info("Номер накладной успешно извлечен.")
        return json.loads(invoice_data)

    except requests.RequestException as e:
        logger.error(f"Ошибка сети при запросе: {e}")
        return {"error": str(e)}

    