# Настройка проекта для работы с Supabase

Этот документ описывает процесс миграции проекта с SQLite на Supabase (PostgreSQL).

## Предварительные требования

1. Аккаунт на [supabase.com](https://supabase.com)
2. Созданный проект в Supabase
3. URL подключения к базе данных и API ключи

## Шаг 1: Создание проекта в Supabase

1. Перейдите на [supabase.com](https://supabase.com)
2. Создайте новый проект
3. Выберите регион (рекомендуется региональный сервер ближе к вашему местоположению)
4. Установите пароль для пользователя `postgres`
5. Дождитесь создания проекта

## Шаг 2: Получение учетных данных

В панели Supabase перейдите в **Settings → Database**:

- **Host**: `[YOUR_PROJECT].supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: [пароль, который вы установили]

Также получите **API URL** и **Anon Key** в **Settings → API**

## Шаг 3: Обновление переменных окружения

Обновите `.env` файл:

```bash
# Вместо SQLite используем PostgreSQL через Supabase
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_PROJECT.supabase.co:5432/postgres

# API для Telegram WebApp
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_ANON_KEY

# Остальные переменные остаются без изменений
BOT_TOKEN=your_bot_token
ADMIN_ID=your_admin_id
TIMEZONE=Europe/Moscow
GOOGLE_CALENDAR_URL=https://calendar.google.com/calendar/render
```

## Шаг 4: Обновление зависимостей

Установите драйвер PostgreSQL вместо aiosqlite:

```bash
# Удалить старую зависимость
pip uninstall aiosqlite -y

# Установить новые зависимости
pip install psycopg[binary] asyncpg
```

Обновите `requirements.txt`:

```bash
aiogram==3.1.1
SQLAlchemy==2.0.23
asyncpg==0.28.0
psycopg[binary]==3.1.12
APScheduler==3.10.4
FastAPI==0.104.1
python-dotenv==1.0.0
pytz==2023.3.post1
uvicorn==0.24.0
pydantic==2.4.2
jinja2==3.1.2
supabase==2.0.1
```

## Шаг 5: Обновление database/session.py

Измените строку подключения:

```python
# Вместо sqlite+aiosqlite используем postgresql+asyncpg
DATABASE_URL = config.db.database_url  # postgresql://user:pass@host/db

# Убедитесь, что используется asyncpg
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Проверка соединения перед использованием
)
```

## Шаг 6: Запуск миграций

### Использование SQL напрямую в Supabase

1. Откройте **SQL Editor** в Supabase
2. Выполните запросы из файла `supabase_migrations/001_create_initial_tables.sql`
3. Выполните запросы из файла `supabase_migrations/002_add_rls_policies.sql`

### Или используйте psql

```bash
# Установите psql (если еще не установлен)
# MacOS:
brew install postgresql

# Ubuntu/Debian:
sudo apt-get install postgresql-client

# Подключитесь и выполните миграции
psql postgresql://postgres:PASSWORD@YOUR_PROJECT.supabase.co:5432/postgres < supabase_migrations/001_create_initial_tables.sql
psql postgresql://postgres:PASSWORD@YOUR_PROJECT.supabase.co:5432/postgres < supabase_migrations/002_add_rls_policies.sql
```

## Шаг 7: Обновление конфигурации RLS

Суpabase использует собственную систему аутентификации. Для работы приложения нужно:

1. Создать пользователя-администратора в Supabase Auth
2. Установить роль `admin` в `raw_app_meta_data`

### Установка роли администратора

Выполните в SQL Editor Supabase:

```sql
-- Обновить метаданные пользователя как администратора
UPDATE auth.users
SET raw_app_meta_data = jsonb_set(
  COALESCE(raw_app_meta_data, '{}'),
  '{role}',
  '"admin"'
)
WHERE email = 'admin@example.com';
```

## Шаг 8: Обновление клиентского кода (опционально)

Если вы хотите использовать Supabase Client для работы с базой:

```python
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

## Шаг 9: Запуск приложения

```bash
# Убедитесь, что используются правильные переменные окружения
source .env

# Инициализируйте БД
python3 -m database.init_db

# Запустите бота
python3 main.py

# В отдельном терминале запустите API
uvicorn miniapp.app:app --reload
```

## Решение проблем

### Ошибка: "column "weekday" is not unique"

```bash
# Удалите дубликаты перед вставкой
DELETE FROM work_schedule WHERE weekday IN (0,1,2,3,4,5,6) AND weekday NOT IN (SELECT MAX(id) FROM work_schedule GROUP BY weekday);
```

### Ошибка подключения

Проверьте:
1. Правильно ли указан `DATABASE_URL`
2. IP адрес добавлен в Supabase firewall (Settings → Network)
3. Пароль не содержит спецсимволы (иначе URL-кодируйте)

### RLS блокирует операции

Убедитесь, что:
1. Пользователь аутентифицирован
2. JWT токен содержит правильные claims
3. Политики корректно настроены

## Переменные окружения

Полный список переменных для `.env`:

```bash
# Telegram Bot
BOT_TOKEN=your_token_here
ADMIN_ID=your_telegram_id

# Database
DATABASE_URL=postgresql://postgres:password@your_project.supabase.co:5432/postgres

# Supabase API
SUPABASE_URL=https://your_project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Application Settings
TIMEZONE=Europe/Moscow
GOOGLE_CALENDAR_URL=https://calendar.google.com/calendar/render
```

## Развертывание на Vercel/Railway

### Используя Railway (рекомендуется)

1. Создайте проект на [railway.app](https://railway.app)
2. Добавьте PostgreSQL плагин
3. Скопируйте `DATABASE_URL` из Railway
4. Добавьте переменные окружения
5. Добавьте GitHub репозиторий и разверните

### Используя Docker

```bash
# Убедитесь, что Dockerfile использует правильный DATABASE_URL
docker build -t nails-bot .
docker run -e DATABASE_URL="postgresql://..." nails-bot
```

## Резервное копирование данных

Supabase автоматически создает резервные копии. Вы можете также экспортировать данные:

```bash
# Экспорт всех данных
pg_dump postgresql://postgres:PASSWORD@YOUR_PROJECT.supabase.co:5432/postgres > backup.sql

# Импорт данных
psql postgresql://postgres:PASSWORD@YOUR_PROJECT.supabase.co:5432/postgres < backup.sql
```

## Поддержка

Для дополнительной информации см:
- [Документация Supabase](https://supabase.com/docs)
- [PostgreSQL документация](https://www.postgresql.org/docs/)
- [SQLAlchemy + asyncpg](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#asyncpg)
