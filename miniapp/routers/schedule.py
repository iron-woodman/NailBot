import datetime
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkSchedule, Holiday
from database.session import get_async_session
from miniapp.auth import verify_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["schedule"])

class WorkScheduleResponse(BaseModel):
    id: int
    weekday: int
    start_time: str
    end_time: str
    is_working: bool

    class Config:
        from_attributes = True

class WorkScheduleUpdate(BaseModel):
    start_time: str
    end_time: str
    is_working: bool

class HolidayCreate(BaseModel):
    date: datetime.date
    reason: str = ""

class HolidayResponse(BaseModel):
    id: int
    date: datetime.date
    reason: str | None

    class Config:
        from_attributes = True

@router.get("/work-schedule", response_model=List[WorkScheduleResponse])
async def get_work_schedule(
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Получить рабочее расписание на все дни недели.
    """
    result = await session.execute(select(WorkSchedule).order_by(WorkSchedule.weekday))
    schedules = result.scalars().all()

    return [
        WorkScheduleResponse(
            id=schedule.id,
            weekday=schedule.weekday,
            start_time=schedule.start_time.strftime('%H:%M'),
            end_time=schedule.end_time.strftime('%H:%M'),
            is_working=schedule.is_working
        )
        for schedule in schedules
    ]

@router.put("/work-schedule/{weekday}")
async def update_work_schedule(
    weekday: int,
    schedule_data: WorkScheduleUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Обновить рабочее расписание для конкретного дня недели.
    """
    if weekday < 0 or weekday > 6:
        raise HTTPException(status_code=400, detail="День недели должен быть от 0 (Пн) до 6 (Вс)")

    result = await session.execute(select(WorkSchedule).where(WorkSchedule.weekday == weekday))
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание для этого дня не найдено")

    try:
        start_time = datetime.datetime.strptime(schedule_data.start_time, '%H:%M').time()
        end_time = datetime.datetime.strptime(schedule_data.end_time, '%H:%M').time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат времени. Используйте HH:MM")

    schedule.start_time = start_time
    schedule.end_time = end_time
    schedule.is_working = schedule_data.is_working

    await session.commit()
    await session.refresh(schedule)

    logger.info(f"Обновлено расписание для дня недели {weekday}")
    return {
        "status": "success",
        "schedule": WorkScheduleResponse(
            id=schedule.id,
            weekday=schedule.weekday,
            start_time=schedule.start_time.strftime('%H:%M'),
            end_time=schedule.end_time.strftime('%H:%M'),
            is_working=schedule.is_working
        )
    }

@router.get("/holidays", response_model=List[HolidayResponse])
async def get_holidays(
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Получить список всех выходных дней.
    """
    result = await session.execute(select(Holiday).order_by(Holiday.date))
    holidays = result.scalars().all()
    return holidays

@router.post("/holidays", response_model=HolidayResponse)
async def create_holiday(
    holiday_data: HolidayCreate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Добавить новый выходной день.
    """
    result = await session.execute(select(Holiday).where(Holiday.date == holiday_data.date))
    existing_holiday = result.scalar_one_or_none()

    if existing_holiday:
        raise HTTPException(status_code=400, detail="Этот день уже отмечен как выходной")

    new_holiday = Holiday(
        date=holiday_data.date,
        reason=holiday_data.reason
    )

    session.add(new_holiday)
    await session.commit()
    await session.refresh(new_holiday)

    logger.info(f"Добавлен выходной день: {new_holiday.date}")
    return new_holiday

@router.delete("/holidays/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Удалить выходной день.
    """
    holiday = await session.get(Holiday, holiday_id)

    if not holiday:
        raise HTTPException(status_code=404, detail="Выходной день не найден")

    await session.delete(holiday)
    await session.commit()

    logger.info(f"Удален выходной день: {holiday.date}")
    return {"status": "success", "message": "Выходной день удален"}
