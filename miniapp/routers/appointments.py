import datetime
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Appointment, User, Service
from database.session import get_async_session
from miniapp.auth import verify_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/appointments", tags=["appointments"])

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

    if date_from:
        query = query.where(Appointment.start_time >= datetime.datetime.combine(date_from, datetime.time.min))

    if date_to:
        query = query.where(Appointment.start_time <= datetime.datetime.combine(date_to, datetime.time.max))

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

    appointment.status = status
    await session.commit()

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

    appointment.status = "cancelled"
    await session.commit()

    logger.info(f"Отменена запись {appointment_id} администратором")
    return {"status": "success", "message": "Запись отменена"}
