# Telegram-бот для записи к мастеру ногтевого сервиса

Полнофункциональный Telegram-бот для управления записями клиентов к мастеру ногтевого сервиса с административной панелью.

## Возможности

### Для клиентов:
- Запись на услуги через интуитивный интерфейс
- Выбор даты и времени из доступных слотов
- Просмотр своих записей
- Отмена записей
- Автоматические напоминания за 24 часа и 2 часа до визита
- Интеграция с Google Calendar

### Для администратора:
- Административная панель (FastAPI) для управления:
  - Услугами (добавление, редактирование, удаление)
  - Рабочим расписанием по дням недели
  - Выходными днями
  - Просмотром всех записей
  - Настройками (горизонт планирования, часовой пояс)

## Установка и настройка

### Предварительные требования

- Python 3.11+
- pip
- SQLite (встроен в Python)

### Шаг 1: Клонирование и установка зависимостей

```bash
# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 2: Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_ID=ваш_telegram_id
DATABASE_URL=sqlite+aiosqlite:///database/nails.db
TIMEZONE=Europe/Moscow
GOOGLE_CALENDAR_URL=https://calendar.google.com/calendar/render
```

**Как получить токен бота:**
1. Напишите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и скопируйте токен

**Как узнать свой Telegram ID:**
1. Напишите @userinfobot в Telegram
2. Он пришлет ваш ID

### Шаг 3: Инициализация базы данных

```bash
python3 -m database.init_db
```

Эта команда создаст:
- Структуру базы данных
- Начальные услуги (можно редактировать через админ-панель)
- Рабочее расписание (Пн-Пт с 9:00 до 18:00)

### Шаг 4: Запуск бота

```bash
# Используя скрипт
./run_bot.sh

# Или напрямую
python3 main.py
```

### Шаг 5: Запуск административной панели

В отдельном терминале:

```bash
# Используя скрипт
./run_miniapp.sh

# Или напрямую
uvicorn miniapp.app:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступно по адресу: `http://localhost:8000`

Документация API: `http://localhost:8000/docs`

## Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## Структура проекта

```
.
├── config.py                 # Конфигурация приложения
├── main.py                   # Точка входа бота
├── requirements.txt          # Зависимости Python
├── .env                      # Переменные окружения
├── database/
│   ├── models.py            # Модели SQLAlchemy
│   ├── session.py           # Настройка БД
│   └── init_db.py           # Инициализация БД
├── handlers/
│   ├── start.py             # Обработчик /start
│   ├── menu.py              # Главное меню
│   ├── booking.py           # Процесс записи
│   ├── appointments.py      # Управление записями
│   ├── contacts.py          # Контакты
│   └── error_handler.py     # Обработка ошибок
├── middlewares/
│   └── db.py                # Middleware для БД
├── miniapp/
│   ├── app.py               # FastAPI приложение
│   ├── auth.py              # Авторизация админа
│   └── routers/
│       ├── services.py      # CRUD услуг
│       ├── appointments.py  # Управление записями
│       ├── schedule.py      # Расписание и выходные
│       └── settings.py      # Настройки приложения
└── utils/
    ├── keyboards.py         # Клавиатуры для бота
    ├── time_utils.py        # Работа со временем
    ├── scheduler.py         # Планировщик напоминаний
    ├── google_calendar.py   # Генерация ссылок
    └── messages.py          # Текстовые шаблоны
```

## API Endpoints

### Авторизация

Все запросы к API требуют заголовок:
```
Authorization: tma <telegram_web_app_init_data>
```

### Услуги

- `GET /api/services` - Список всех услуг
- `POST /api/services` - Создать услугу
- `PUT /api/services/{id}` - Обновить услугу
- `DELETE /api/services/{id}` - Деактивировать услугу

### Записи

- `GET /api/appointments` - Список записей (с фильтрацией)
- `PUT /api/appointments/{id}/status` - Изменить статус
- `DELETE /api/appointments/{id}` - Отменить запись

### Расписание

- `GET /api/work-schedule` - Рабочее расписание
- `PUT /api/work-schedule/{weekday}` - Обновить день недели
- `GET /api/holidays` - Список выходных
- `POST /api/holidays` - Добавить выходной
- `DELETE /api/holidays/{id}` - Удалить выходной

### Настройки

- `GET /api/settings` - Текущие настройки
- `PUT /api/settings` - Обновить настройки

## Использование

### Для клиента

1. Напишите боту `/start`
2. Нажмите "Записаться"
3. Выберите услугу
4. Выберите дату
5. Выберите время
6. Подтвердите запись
7. Получите ссылку для добавления в Google Calendar

### Для администратора

1. Убедитесь, что ваш Telegram ID указан в `ADMIN_ID` в `.env`
2. Используйте API для управления услугами, расписанием и записями
3. Можно создать веб-интерфейс (Telegram Mini App) для удобного управления

## Напоминания

Бот автоматически отправляет напоминания:
- За 24 часа до записи
- За 2 часа до записи

Планировщик проверяет записи каждые 30 минут.

## Часовые пояса

Все время в базе данных хранится в UTC. Конвертация происходит автоматически на основе настройки `TIMEZONE` в `.env`.

## Troubleshooting

### Бот не отвечает
- Проверьте, что токен бота правильный
- Убедитесь, что бот запущен
- Проверьте логи на наличие ошибок

### Не приходят напоминания
- Убедитесь, что планировщик запущен (логи при старте)
- Проверьте настройку часового пояса
- Проверьте, что записи имеют статус `confirmed`

### Ошибки при работе с БД
- Убедитесь, что директория `database/` существует и доступна для записи
- Проверьте путь в `DATABASE_URL`

## Развертывание на VPS

### С использованием systemd

1. Создайте файл `/etc/systemd/system/nailbot.service`:

```ini
[Unit]
Description=Nails Appointment Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 /path/to/project/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Активируйте сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nailbot
sudo systemctl start nailbot
sudo systemctl status nailbot
```

### С использованием Docker

См. раздел "Запуск через Docker" выше.

## Лицензия

MIT

## Поддержка

При возникновении вопросов или проблем создайте issue в репозитории проекта.
