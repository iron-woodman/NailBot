from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import load_config

# Загрузка конфигурации для получения URL базы данных
config = load_config()
DATABASE_URL = config.db.database_url

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=True)

# Создание фабрики асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    """
    Базовый класс для декларативного определения моделей SQLAlchemy.
    """
    pass

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Функция-генератор для получения асинхронной сессии базы данных.

    Yields:
        AsyncSession: Асинхронная сессия базы данных.
    """
    async with AsyncSessionLocal() as session:
        yield session

async def init_db() -> None:
    """
    Функция для инициализации базы данных, создания всех таблиц.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
