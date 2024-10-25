from dotenv import load_dotenv
import os
import openai 
from openai import AsyncOpenAI
import cv2
import pytesseract
import json
import requests
from utils import convert_image_to_base64
from prompt import prompt, keywords
import logging
import imutils  # Импортируем imutils
from PIL import ImageEnhance
import numpy as np

logger = logging.getLogger(__name__)

load_dotenv()

def enhance_image(image):
    logger.debug("Начало улучшения изображения.")
    
    # Увеличиваем контраст, не меняя цвет
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(1.2)  # Значение > 1 увеличивает контраст
    
    logger.info("Улучшенное изображение подготовлено для распознавания.")
    
    # Конвертируем PIL Image в cv2 формат
    open_cv_image = cv2.cvtColor(np.array(enhanced_image), cv2.COLOR_RGB2BGR)
    
    return open_cv_image

# Проверка ориентации текста на русском языке
def check_text_orientation(image):
    logger.info("Начало проверки ориентации текста.")
    #enhanced_image_result = enhance_image(image)

    #logger.info("Улучшенное изображение подготовлено для распознавания.")
    """
    psm_modes = [1, 3, 4]
    text_results = []
    
    for psm in psm_modes:
        custom_config = f'--oem 3 --psm {psm} -l rus'
        text = pytesseract.image_to_string(image, config=custom_config)
        text_results.append((text, len(text)))
        logger.info(f"Извлеченный текст (PSM {psm}): '{text}' (длина: {len(text)})")

    best_text = max(text_results, key=lambda x: x[1])
    logger.info(f"Извлеченный текст: {best_text[0]}")
    
    result = best_text[1] > 10
    """

    custom_config = '--oem 3 --psm 6 -l rus'  # Либо 11, в зависимости от ваших нужд
    text = pytesseract.image_to_string(image, config=custom_config)
    logger.info(f"Извлеченнный текст: {text}")
    
    # Проверка наличия ключевых слов (без учета регистра)
    if any(keyword in text.lower() for keyword in keywords):
        result=True
    else:
        result = False
    #result = len(text) > 10
    logger.info(f"Ориентация текста {'правильная' if result else 'неправильная'} (количество символов: {len(text)}).")

    return result



# Извлечение номера накладной с помощью openai
async def get_invoice_from_image(base64_image):
    try:
        logger.info("Начало запроса к OpenAI для извлечения номера накладной.")
        response = await client.chat.completions.create(
            model="gpt-4o",
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
            max_tokens=30,
            temperature=0.8
        )
        content = response.choices[0].message.content
        logger.info(f"Успешно извлечен номер накладной: {content}")
        return content
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        return {"error": str(e)}

openai.api_key = os.getenv('OPENAI_API_KEY')
client = AsyncOpenAI()

# Основная функция для обработки изображения и получения номера накладной
async def get_number_using_openai(pil_image):
    try:
        cv_image=enhance_image(pil_image)
        logger.info("Начало обработки изображения для извлечения номера накладной.")
        
        # Проверяем оригинальное изображение
        #is_readable = check_text_orientation(cv_image)
        
        # Если текст не читаем, пробуем повороты
        #if not is_readable:
        for attempt in range(4):  # Проверяем 4 попытки: 0, 90, 180, 270 градусов
            if attempt > 0:
                cv_image = imutils.rotate(cv_image, 90)  # Поворачиваем на 90 градусов
            is_readable = check_text_orientation(cv_image)
            if is_readable:
                logger.info(f"Текст стал читаемым после поворота (попытка {attempt}).")
                break
        else:
            logger.warning("Не удалось сделать текст читаемым после четырех поворотов.")
        
        # Преобразуем изображение обратно в base64
        base64_image = convert_image_to_base64(cv_image)
        logger.debug("Изображение перекодировано в base64 для отправки в OpenAI.")
        
        invoice_data = await get_invoice_from_image(base64_image)
        logger.info("Номер накладной успешно извлечен.")
        return json.loads(invoice_data)

    except requests.RequestException as e:
        logger.error(f"Ошибка сети при запросе: {e}")
        return {"error": str(e)}

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return {"error": str(e)}
