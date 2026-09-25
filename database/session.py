import logging
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import load_config

logger = logging.getLogger(__name__)

# Загрузка конфигурации для получения URL базы данных
config = load_config()
DATABASE_URL = config.db.database_url

# Создание асинхронного движка SQLAlchemy.
# echo включается только через SQL_ECHO=1: иначе в логи попадают имена и
# username клиентов из параметров каждого запроса.
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Бот и API — два процесса на одном файле БД, поэтому ждём снятия блокировки
# вместо мгновенного "database is locked".
connect_args = {"timeout": 30} if IS_SQLITE else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO") == "1",
    connect_args=connect_args,
)

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

async def _add_missing_columns(conn) -> None:
    """
    Досоздаёт колонки, появившиеся в моделях после создания базы.

    create_all() умеет только CREATE TABLE, поэтому в базе, созданной до
    появления новой колонки, её не будет — и запрос упадёт на "no such column".

    ponytail: только ADD COLUMN для SQLite. Переименования, смену типа и
    удаление колонок не делает — если схема начнёт активно меняться, нужен Alembic.
    """
    for table in Base.metadata.sorted_tables:
        rows = await conn.exec_driver_sql(f"PRAGMA table_info({table.name})")
        existing = {row[1] for row in rows.fetchall()}
        if not existing:
            continue  # таблицы ещё нет, её создаст create_all

        for column in table.columns:
            if column.name in existing:
                continue

            ddl = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {column.type.compile(conn.dialect)}"
            if not column.nullable:
                # SQLite не даёт добавить NOT NULL колонку без значения по умолчанию.
                default = getattr(column.default, "arg", None)
                if default is None or callable(default):
                    raise RuntimeError(
                        f"Не могу добавить NOT NULL колонку {table.name}.{column.name}: "
                        f"у неё нет скалярного значения по умолчанию"
                    )
                literal = int(default) if isinstance(default, bool) else repr(default)
                ddl += f" NOT NULL DEFAULT {literal}"

            await conn.exec_driver_sql(ddl)
            logger.info(f"Добавлена колонка {table.name}.{column.name}")

async def init_db() -> None:
    """
    Функция для инициализации базы данных, создания всех таблиц.
    """
    # Модели регистрируются в Base.metadata на импорте, а session.py их не
    # импортирует (иначе цикл). Без этого create_all не увидит ни одной таблицы,
    # если вызвать init_db() раньше импорта моделей.
    from database import models  # noqa: F401

    async with engine.begin() as conn:
        if IS_SQLITE:
            # WAL даёт читателям работать параллельно с пишущим процессом.
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            await _add_missing_columns(conn)
        await conn.run_sync(Base.metadata.create_all)
