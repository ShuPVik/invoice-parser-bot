# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Установим зависимости для OpenCV и Zbar
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    zbar-tools


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
