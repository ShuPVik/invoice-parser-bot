# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости для OpenCV, Zbar и Tesseract OCR
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    zbar-tools \
    tesseract-ocr \
    tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем переменную среды для Tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

# Копируем файл с зависимостями в контейнер
COPY requirements.txt ./

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения в контейнер
COPY . .

# Указываем команду для запуска приложения
CMD ["python", "main.py"]
