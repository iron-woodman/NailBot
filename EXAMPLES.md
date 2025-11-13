# Примеры использования проекта

Этот документ содержит примеры использования различных компонентов системы.

## Содержание

1. [Использование Telegram бота](#telegram-бот)
2. [Использование API](#api)
3. [Программная работа с БД](#работа-с-бд)
4. [Развертывание](#развертывание)

## Telegram бот

### Для клиентов

#### 1. Регистрация и главное меню

```
Пользователь: /start

Бот ответит:
"Привет, Иван! Добро пожаловать в бот для записи к мастеру ногтевого сервиса.

Здесь вы можете:
- Записаться на услугу
- Просмотреть свои записи
- Отменить запись
- Связаться с нами

[Записаться] [Мои записи]
[Отменить запись] [Контакты]"
```

#### 2. Процесс записи

```
1. Нажмите "Записаться"
   Бот выведет список услуг:
   - Маникюр (30 мин) - 500 руб.
   - Педикюр (45 мин) - 800 руб.
   - Гель-лак (60 мин) - 1200 руб.
   и т.д.

2. Выберите услугу
   Бот выведет календарь с доступными датами

3. Выберите дату
   Бот выведет список доступного времени

4. Выберите время
   Бот покажет подтверждение:
   "Подтвердите вашу запись:
   Услуга: Гель-лак
   Дата: 20.11.2024
   Время: 14:00 (Europe/Moscow)

   Все верно?"

   [Подтвердить] [Отменить]

5. Нажмите "Подтвердить"
   Бот ответит:
   "Отлично! Ваша запись на услугу 'Гель-лак' успешно создана.

   Дата: 20.11.2024
   Время: 14:00 (Europe/Moscow)

   [Добавить в Google Calendar]

   Мы будем ждать вас!"
```

#### 3. Просмотр своих записей

```
Пользователь нажимает "Мои записи"

Бот выведет:
"Ваши предстоящие записи:

1. Маникюр - 15.11.2024 14:00
   [Отменить запись на 15.11 14:00]

2. Педикюр - 20.11.2024 10:30
   [Отменить запись на 20.11 10:30]

[Назад в главное меню]"
```

#### 4. Отмена записи

```
Пользователь нажимает "Отменить запись на 15.11 14:00"

Бот спросит:
"Вы уверены, что хотите отменить запись на 15.11.2024 14:00?
[Да, отменить] [Нет, вернуться]"

При согласии:
"Ваша запись на маникюр на 15.11.2024 14:00 успешно отменена."
```

### Для администратора

#### API для управления услугами

```bash
# Получить все услуги
curl -X GET http://localhost:8000/api/services \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA"

# Добавить новую услугу
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Покрытие (Base+Top)",
    "duration_minutes": 15,
    "price": 250.0,
    "description": "Базовое покрытие гель-лака",
    "active": true
  }'

# Изменить услугу
curl -X PUT http://localhost:8000/api/services/1 \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 300.0
  }'

# Деактивировать услугу
curl -X DELETE http://localhost:8000/api/services/1 \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA"
```

#### Управление расписанием

```bash
# Получить расписание
curl -X GET http://localhost:8000/api/work-schedule \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA"

# Изменить расписание для вторника (weekday=1)
curl -X PUT http://localhost:8000/api/work-schedule/1 \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "10:00",
    "end_time": "19:00",
    "is_working": true
  }'
```

#### Добавление выходного дня

```bash
# Добавить выходной на День благодарения
curl -X POST http://localhost:8000/api/holidays \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-11-28",
    "reason": "Благодарение"
  }'

# Просмотр всех выходных
curl -X GET http://localhost:8000/api/holidays \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA"

# Удалить выходной
curl -X DELETE http://localhost:8000/api/holidays/1 \
  -H "Authorization: tma YOUR_TELEGRAM_INIT_DATA"
```

## API

### Документация Swagger

Откройте в браузере: `http://localhost:8000/docs`

Все эндпоинты документированы и вы можете их тестировать прямо из браузера.

### Основные эндпоинты

#### Услуги

```
GET    /api/services              # Получить все услуги
POST   /api/services              # Создать услугу
PUT    /api/services/{id}         # Обновить услугу
DELETE /api/services/{id}         # Удалить услугу
```

#### Записи

```
GET    /api/appointments          # Получить все записи
PUT    /api/appointments/{id}/status  # Изменить статус
DELETE /api/appointments/{id}     # Отменить запись
```

#### Расписание

```
GET    /api/work-schedule         # Получить расписание
PUT    /api/work-schedule/{weekday}  # Обновить день
GET    /api/holidays              # Получить выходные
POST   /api/holidays              # Добавить выходной
DELETE /api/holidays/{id}         # Удалить выходной
```

#### Настройки

```
GET    /api/settings              # Получить настройки
PUT    /api/settings              # Обновить настройки
```

## Работа с БД

### Использование SQLAlchemy

```python
from sqlalchemy import select
from database.session import AsyncSessionLocal
from database.models import User, Service, Appointment

async def get_user_appointments(telegram_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Appointment).join(User).where(User.telegram_id == telegram_id)
        )
        return result.scalars().all()

async def create_service(name: str, duration: int, price: float):
    async with AsyncSessionLocal() as session:
        service = Service(
            name=name,
            duration_minutes=duration,
            price=price,
            active=True
        )
        session.add(service)
        await session.commit()
        return service
```

### Использование Supabase Client

```python
from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Получить услуги
response = supabase.table("services").select("*").eq("active", True).execute()
services = response.data

# Создать запись
new_appointment = {
    "user_id": 1,
    "service_id": 1,
    "start_time": "2024-11-20T14:00:00Z",
    "end_time": "2024-11-20T15:00:00Z",
    "status": "confirmed"
}
response = supabase.table("appointments").insert([new_appointment]).execute()
```

## Развертывание

### Локальное тестирование

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Создать .env файл
cp .env.example .env
# Отредактировать .env

# 3. Инициализировать БД
python3 -m database.init_db

# 4. Запустить бота (терминал 1)
python3 main.py

# 5. Запустить API (терминал 2)
uvicorn miniapp.app:app --reload --port 8000
```

### Использование Docker Compose

```bash
# 1. Отредактировать .env
nano .env

# 2. Запустить контейнеры
docker-compose up -d

# 3. Проверить логи
docker-compose logs -f

# 4. Остановить контейнеры
docker-compose down
```

### Развертывание на VPS

#### Используя systemd

```bash
# 1. Скопировать файл сервиса
sudo cp nailbot.service /etc/systemd/system/
sudo cp nailapi.service /etc/systemd/system/

# 2. Отредактировать пути в файлах
sudo nano /etc/systemd/system/nailbot.service
# Изменить /path/to/project на реальный путь

# 3. Перезагрузить systemd
sudo systemctl daemon-reload

# 4. Включить и запустить сервисы
sudo systemctl enable nailbot
sudo systemctl start nailbot
sudo systemctl enable nailapi
sudo systemctl start nailapi

# 5. Проверить статус
sudo systemctl status nailbot
sudo systemctl status nailapi

# 6. Просмотр логов
sudo journalctl -u nailbot -f
sudo journalctl -u nailapi -f
```

#### Используя Docker

```bash
# 1. Собрать образ
docker build -t nails-bot:latest .

# 2. Запустить контейнер
docker run -d \
  --name nails-bot \
  --restart always \
  -e BOT_TOKEN=your_token \
  -e ADMIN_ID=your_id \
  -e DATABASE_URL=sqlite:///database/nails.db \
  -v /path/to/project/database:/app/database \
  nails-bot:latest

# 3. Запустить API
docker run -d \
  --name nails-api \
  --restart always \
  -p 8000:8000 \
  -e BOT_TOKEN=your_token \
  -e ADMIN_ID=your_id \
  -e DATABASE_URL=sqlite:///database/nails.db \
  -v /path/to/project/database:/app/database \
  nails-bot:latest \
  uvicorn miniapp.app:app --host 0.0.0.0 --port 8000
```

### Проверка здоровья приложения

```bash
# Проверить статус API
curl http://localhost:8000/health

# Должен вернуть:
# {"status": "healthy"}

# Проверить информацию об API
curl http://localhost:8000/api

# Должен вернуть:
# {"message": "Welcome to the MiniApp API!", "version": "1.0.0", "status": "running"}
```

## Дополнительные команды

### Очистка данных

```bash
# Удалить все записи (осторожно!)
python3 << EOF
import asyncio
from sqlalchemy import delete
from database.session import AsyncSessionLocal
from database.models import Appointment

async def clear_appointments():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Appointment))
        await session.commit()
        print("Все записи удалены")

asyncio.run(clear_appointments())
EOF
```

### Экспорт данных

```bash
# Экспортировать все записи в CSV
python3 << EOF
import csv
import asyncio
from database.session import AsyncSessionLocal
from database.models import Appointment

async def export_appointments():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(Appointment))
        appointments = result.scalars().all()

        with open('appointments.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'User', 'Service', 'Date', 'Time', 'Status'])
            for app in appointments:
                writer.writerow([app.id, app.user.full_name, app.service.name,
                               app.start_time.date(), app.start_time.time(), app.status])

asyncio.run(export_appointments())
print("Данные экспортированы в appointments.csv")
EOF
```

## Решение проблем

### Бот не отвечает
```bash
# Проверить логи
tail -f /var/log/nails-bot.log

# Перезапустить бота
sudo systemctl restart nailbot
```

### API не доступен
```bash
# Проверить, запущен ли процесс
curl http://localhost:8000/health

# Перезапустить API
sudo systemctl restart nailapi
```

### Проблемы с БД
```bash
# Проверить файл БД
ls -la database/nails.db

# Пересоздать таблицы
python3 -m database.init_db
```
