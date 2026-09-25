import datetime
import logging
from typing import List

import pytz
from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Appointment, User, Service
from database.session import get_async_session
from config import load_config
from miniapp.auth import verify_admin
from utils.time_utils import format_in_timezone, get_timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/appointments", tags=["appointments"])
config = load_config()

async def notify_client_cancelled(appointment: Appointment, timezone_str: str) -> None:
    """
    Сообщает клиенту, что мастер отменил его запись.

    Без этого клиент узнавал об отмене только придя на приём.

    Args:
        appointment (Appointment): Отменённая запись (с загруженными user и service).
        timezone_str (str): Часовой пояс для отображения времени.
    """
    bot = Bot(token=config.tg_bot.token)
    try:
        await bot.send_message(
            appointment.user.telegram_id,
            f"К сожалению, ваша запись на услугу '{appointment.service.name}' "
            f"{format_in_timezone(appointment.start_time, timezone_str, '%d.%m.%Y в %H:%M')} "
            f"была отменена мастером.\n\n"
            f"Вы можете записаться на другое время."
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить клиента об отмене записи {appointment.id}: {e}")
    finally:
        await bot.session.close()

class AppointmentResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_username: str | None
    service_id: int
    service_name: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    status: str | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Получить список всех записей с фильтрацией.
    """
    query = select(Appointment).options(
        selectinload(Appointment.user),
        selectinload(Appointment.service)
    ).order_by(Appointment.start_time.desc())

    if status:
        query = query.where(Appointment.status == status)

    if date_from or date_to:
        tz = pytz.timezone(await get_timezone(session))

    if date_from:
        start_of_day = tz.localize(datetime.datetime.combine(date_from, datetime.time.min)).astimezone(pytz.utc)
        query = query.where(Appointment.start_time >= start_of_day)

    if date_to:
        end_of_day = tz.localize(datetime.datetime.combine(date_to, datetime.time.max)).astimezone(pytz.utc)
        query = query.where(Appointment.start_time <= end_of_day)

    result = await session.execute(query)
    appointments = result.scalars().all()

    return [
        AppointmentResponse(
            id=app.id,
            user_id=app.user_id,
            user_name=app.user.full_name,
            user_username=app.user.username,
            service_id=app.service_id,
            service_name=app.service.name,
            start_time=app.start_time,
            end_time=app.end_time,
            status=app.status,
            created_at=app.created_at
        )
        for app in appointments
    ]

@router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    status: str,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Обновить статус записи.
    """
    valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Недопустимый статус. Допустимые: {valid_statuses}")

    appointment = await session.get(Appointment, appointment_id, options=[
        selectinload(Appointment.user),
        selectinload(Appointment.service)
    ])

    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    was_cancelled = appointment.status == "cancelled"
    appointment.status = status
    await session.commit()

    if status == "cancelled" and not was_cancelled:
        await notify_client_cancelled(appointment, await get_timezone(session))

    logger.info(f"Обновлен статус записи {appointment_id} на {status}")
    return {"status": "success", "message": f"Статус обновлен на {status}"}

@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Отменить запись.
    """
    appointment = await session.get(Appointment, appointment_id, options=[
        selectinload(Appointment.user),
        selectinload(Appointment.service)
    ])

    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    was_cancelled = appointment.status == "cancelled"
    appointment.status = "cancelled"
    await session.commit()

    if not was_cancelled:
        await notify_client_cancelled(appointment, await get_timezone(session))

    logger.info(f"Отменена запись {appointment_id} администратором")
    return {"status": "success", "message": "Запись отменена"}
