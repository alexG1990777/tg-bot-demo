# Используем Python 3.11 как базовый образ
FROM python:3.11-slim

# Установим рабочую директорию внутри контейнера
WORKDIR /app

# Обновляем pip до последней версии
RUN pip install --upgrade pip

# Копируем файл зависимостей requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . .

# Запускаем приложение
CMD ["python", "bot.py"]
