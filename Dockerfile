# Базовый образ Python
FROM python:3.11-slim

# Установка зависимостей для компиляции
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app

# Указываем, какой файл будет запускаться
CMD ["python", "bot.py"]
