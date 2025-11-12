import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import load_config, Config
from database.session import init_db, AsyncSessionLocal
from database.init_db import create_initial_data
from handlers import start, menu, booking, appointments, contacts
from middlewares.db import DbSessionMiddleware
from utils.scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def main() -> None:
    """
    Основная функция для запуска Telegram-бота и планировщика задач.
    """
    logger.info("Запуск бота...")

    # Загрузка конфигурации
    config: Config = load_config()

    # Инициализация бота и диспетчера
    bot = Bot(token=config.tg_bot.token, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Инициализация планировщика
    scheduler = AsyncIOScheduler(timezone=config.scheduler.timezone)

    # Инициализация базы данных
    await init_db()
    async with AsyncSessionLocal() as session:
        await create_initial_data(session)

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(booking.router)
    dp.include_router(appointments.router)
    dp.include_router(contacts.router)

    # Регистрация middleware
    dp.update.middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))

    try:
        # Настройка и запуск задач планировщика
        setup_scheduler(scheduler, bot, AsyncSessionLocal)
        scheduler.start()
        logger.info("Планировщик запущен.")

        # Запуск бота
        await dp.start_polling(bot)
    finally:
        # Остановка планировщика и бота при завершении работы
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот выключен!")
