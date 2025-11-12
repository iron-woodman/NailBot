#!/bin/bash

echo "Запуск административной панели (MiniApp API)..."

if [ ! -f ".env" ]; then
    echo "Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

echo "Запуск FastAPI сервера..."
uvicorn miniapp.app:app --host 0.0.0.0 --port 8000 --reload
