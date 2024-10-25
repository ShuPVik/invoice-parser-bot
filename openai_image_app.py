from dotenv import load_dotenv
import os
import openai 
from openai import AsyncOpenAI
import cv2
import numpy as np
import logging
import imutils
from utils import convert_image_to_base64
from prompt import prompt
import json
import requests

logger = logging.getLogger(__name__)

load_dotenv()

# Определение угла наклона изображения
def get_skew_angle(image):
    logger.debug("Определение угла наклона изображения.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    logger.debug(f"Обнаружен угол наклона: {angle} градусов.")
    return angle

# Исправление наклона изображения
def correct_skew(image):
    angle = get_skew_angle(image)
    
    if angle != 0:
        logger.info(f"Корректируем наклон изображения на {angle} градусов.")
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        logger.info("Наклон изображения исправлен.")
        return rotated
    
    logger.info("Изображение уже выровнено.")
    return image

# Улучшение изображения для OCR
def enhance_image(image):
    logger.debug("Улучшение изображения для улучшения распознавания.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary_image = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
    logger.debug("Изображение улучшено.")
    return morphed

# Основная функция для обработки изображения и получения номера накладной
async def get_number_using_openai(cv_image):
    try:
        logger.info("Начало обработки изображения для извлечения номера накладной.")
        corrected_image = correct_skew(cv_image)
        
        # Преобразуем изображение обратно в base64
        base64_image = convert_image_to_base64(corrected_image)
        logger.debug("Изображение перекодировано в base64 для отправки в OpenAI.")
        
        invoice_data = await get_invoice_from_image(base64_image)
        logger.info("Номер накладной успешно извлечен.")
        return json.loads(invoice_data)

    except requests.RequestException as e:
        logger.error(f"Ошибка сети при запросе: {e}")
        return {"error": str(e)}

# Извлечение номера накладной с помощью OpenAI
async def get_invoice_from_image(base64_image):
    try:
        logger.info("Начало запроса к OpenAI для извлечения номера накладной.")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
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
            }],
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
