from dotenv import load_dotenv
import os
from dataclasses import dataclass

# Загрузка переменных окружения из файла .env
load_dotenv()

@dataclass
class TgBot:
    """
    Класс для хранения конфигурации Telegram-бота.

    Attributes:
        token (str): Токен Telegram-бота.
        admin_id (int): ID администратора бота.
    """
    token: str
    admin_id: int

@dataclass
class DbConfig:
    """
    Класс для хранения конфигурации базы данных.

    Attributes:
        database_url (str): URL для подключения к базе данных.
    """
    database_url: str

@dataclass
class SchedulerConfig:
    """
    Класс для хранения конфигурации планировщика задач.

    Attributes:
        timezone (str): Часовой пояс для планировщика.
    """
    timezone: str

@dataclass
class GoogleCalendarConfig:
    """
    Класс для хранения конфигурации Google Calendar.

    Attributes:
        url (str): Базовый URL для создания событий в Google Calendar.
    """
    url: str

@dataclass
class Config:
    """
    Основной класс для хранения всей конфигурации приложения.

    Attributes:
        tg_bot (TgBot): Конфигурация Telegram-бота.
        db (DbConfig): Конфигурация базы данных.
        scheduler (SchedulerConfig): Конфигурация планировщика.
        google_calendar (GoogleCalendarConfig): Конфигурация Google Calendar.
    """
    tg_bot: TgBot
    db: DbConfig
    scheduler: SchedulerConfig
    google_calendar: GoogleCalendarConfig

def load_config() -> Config:
    """
    Функция загружает конфигурацию приложения из переменных окружения.

    Returns:
        Config: Объект конфигурации приложения.
    """
    return Config(
        tg_bot=TgBot(
            token=os.getenv("BOT_TOKEN", ""),
            admin_id=int(os.getenv("ADMIN_ID", "0"))
        ),
        db=DbConfig(
            database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database/nails.db")
        ),
        scheduler=SchedulerConfig(
            timezone=os.getenv("TIMEZONE", "Europe/Moscow")
        ),
        google_calendar=GoogleCalendarConfig(
            url=os.getenv("GOOGLE_CALENDAR_URL", "")
        )
    )

