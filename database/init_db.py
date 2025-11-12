import asyncio
import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Service, Appointment, WorkSchedule, Holiday, Settings
from database.session import AsyncSessionLocal, init_db
from config import load_config

logger = logging.getLogger(__name__)

async def create_initial_data(session: AsyncSession) -> None:
    """
    Функция для создания начальных данных в базе данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
    """
    logger.info("Создание начальных данных...")

    # Загрузка конфигурации для получения admin_id
    config = load_config()
    admin_id = config.tg_bot.admin_id

    # Создание настроек по умолчанию
    settings = await session.get(Settings, 1)
    if not settings:
        settings = Settings(id=1, admin_id=admin_id, planning_horizon_days=30, timezone="Europe/Moscow")
        session.add(settings)
        logger.info("Настройки по умолчанию добавлены.")
    else:
        logger.info("Настройки уже существуют.")

    # Создание расписания работы по умолчанию (Пн-Пт с 9:00 до 18:00)
    for i in range(7):
        schedule = await session.execute(WorkSchedule.__table__.select().where(WorkSchedule.weekday == i))
        if not schedule.scalar_one_or_none():
            is_working = True if 0 <= i <= 4 else False  # Пн-Пт рабочие дни
            start_time = datetime.time(9, 0) if is_working else datetime.time(0, 0)
            end_time = datetime.time(18, 0) if is_working else datetime.time(0, 0)
            session.add(WorkSchedule(weekday=i, start_time=start_time, end_time=end_time, is_working=is_working))
            logger.info(f"Расписание для дня {i} добавлено.")
        else:
            logger.info(f"Расписание для дня {i} уже существует.")

    # Создание нескольких услуг по умолчанию
    default_services = [
        {"name": "Маникюр", "duration_minutes": 60, "price": 1500.0, "description": "Классический маникюр"},
        {"name": "Педикюр", "duration_minutes": 90, "price": 2500.0, "description": "Классический педикюр"},
        {"name": "Покрытие гель-лаком", "duration_minutes": 45, "price": 1000.0, "description": "Покрытие ногтей гель-лаком"},
    ]

    for service_data in default_services:
        service = await session.execute(Service.__table__.select().where(Service.name == service_data["name"])) # type: ignore
        if not service.scalar_one_or_none():
            session.add(Service(**service_data))
            logger.info(f"Услуга '{service_data["name"]}' добавлена.")
        else:
            logger.info(f"Услуга '{service_data["name"]}' уже существует.")

    await session.commit()
    logger.info("Начальные данные успешно созданы.")

async def main() -> None:
    """
    Основная функция для инициализации базы данных и создания начальных данных.
    """
    await init_db()
    async with AsyncSessionLocal() as session:
        await create_initial_data(session)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
