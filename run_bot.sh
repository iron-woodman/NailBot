#!/bin/bash

echo "Запуск Telegram-бота для записи к мастеру ногтевого сервиса..."

if [ ! -d "database" ]; then
    echo "Создание директории для базы данных..."
    mkdir -p database
fi

if [ ! -f ".env" ]; then
    echo "Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

echo "Проверка переменных окружения..."
if ! grep -q "BOT_TOKEN=YOUR_BOT_TOKEN" .env; then
    echo "Инициализация базы данных..."
    python3 -m database.init_db

    echo "Запуск бота..."
    python3 main.py
else
    echo "ОШИБКА: Заполните переменные в файле .env перед запуском!"
    echo "Необходимо указать:"
    echo "  - BOT_TOKEN (токен от @BotFather)"
    echo "  - ADMIN_ID (ваш Telegram ID)"
    exit 1
fi
