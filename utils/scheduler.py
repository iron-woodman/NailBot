import logging
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Appointment
from config import load_config

logger = logging.getLogger(__name__)
config = load_config()

async def send_reminder(bot: Bot, appointment: Appointment, time_left: str):
    """
    Отправляет напоминание о предстоящей записи.

    Args:
        bot (Bot): Экземпляр бота.
        appointment (Appointment): Объект записи.
        time_left (str): Оставшееся время (например, "24 часа" или "2 часа").
    """
    user_id = appointment.user.telegram_id
    service_name = appointment.service.name
    start_time_str = appointment.start_time.strftime('%H:%M')
    
    try:
        await bot.send_message(
            user_id,
            f"🔔 Напоминание!\n\n"
            f"У вас скоро запись на услугу <b>'{service_name}'</b>.\n"
            f"Ждем вас сегодня в <b>{start_time_str}</b>.\n\n"
            f"До встречи осталось {time_left}!"
        )
        logger.info(f"Отправлено напоминание пользователю {user_id} о записи {appointment.id}")
    except Exception as e:
        logger.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")

async def check_upcoming_appointments(bot: Bot, session_pool):
    """
    Проверяет предстоящие записи и отправляет напоминания.
    """
    now = datetime.utcnow()
    reminder_time_24h = now + timedelta(hours=24)
    reminder_time_2h = now + timedelta(hours=2)

    async with session_pool() as session:
        # Записи, до которых осталось 23-24 часа
        result_24h = await session.execute(
            select(Appointment)
            .options(selectinload(Appointment.user), selectinload(Appointment.service))
            .where(
                Appointment.status == 'confirmed',
                Appointment.start_time.between(
                    reminder_time_24h - timedelta(minutes=15),
                    reminder_time_24h + timedelta(minutes=15)
                )
            )
        )
        appointments_24h = result_24h.scalars().all()
        for app in appointments_24h:
            await send_reminder(bot, app, "24 часа")

        # Записи, до которых осталось 1-2 часа
        result_2h = await session.execute(
            select(Appointment)
            .options(selectinload(Appointment.user), selectinload(Appointment.service))
            .where(
                Appointment.status == 'confirmed',
                Appointment.start_time.between(
                    reminder_time_2h - timedelta(minutes=15),
                    reminder_time_2h + timedelta(minutes=15)
                )
            )
        )
        appointments_2h = result_2h.scalars().all()
        for app in appointments_2h:
            await send_reminder(bot, app, "2 часа")

def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot, session_pool):
    """
    Настраивает и запускает задачи в планировщике.
    """
    scheduler.add_job(
        check_upcoming_appointments,
        'interval',
        minutes=30,
        args=(bot, session_pool),
        id='appointment_reminders'
    )
    logger.info("Задача для проверки напоминаний добавлена в планировщик.")
