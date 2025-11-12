import datetime
from typing import Optional

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkSchedule, Holiday, Settings, Appointment

async def get_timezone(session: AsyncSession) -> str:
    """
    Извлекает часовой пояс из настроек базы данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        str: Строка с названием часового пояса (например, 'Europe/Moscow').
    """
    settings = await session.get(Settings, 1)
    return settings.timezone if settings else "Europe/Moscow"

async def get_planning_horizon(session: AsyncSession) -> int:
    """
    Извлекает горизонт планирования из настроек базы данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        int: Горизонт планирования в днях.
    """
    settings = await session.get(Settings, 1)
    return settings.planning_horizon_days if settings else 30

async def is_working_day(session: AsyncSession, date: datetime.date) -> bool:
    """
    Проверяет, является ли указанная дата рабочим днем согласно расписанию.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        date (datetime.date): Проверяемая дата.

    Returns:
        bool: True, если день рабочий, False в противном случае.
    """
    weekday = date.weekday() # Понедельник - 0, Воскресенье - 6
    result = await session.execute(select(WorkSchedule).where(WorkSchedule.weekday == weekday))
    schedule = result.scalar_one_or_none()
    return schedule.is_working if schedule else False

async def is_holiday(session: AsyncSession, date: datetime.date) -> bool:
    """
    Проверяет, является ли указанная дата праздничным/выходным днем.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        date (datetime.date): Проверяемая дата.

    Returns:
        bool: True, если день является выходным, False в противном случае.
    """
    result = await session.execute(select(Holiday).where(Holiday.date == date))
    holiday = result.scalar_one_or_none()
    return holiday is not None

def convert_to_timezone(dt: datetime.datetime, tz_name: str) -> datetime.datetime:
    """
    Конвертирует datetime объект в указанный часовой пояс.

    Args:
        dt (datetime.datetime): Объект datetime (предполагается UTC, если не timezone-aware).
        tz_name (str): Название целевого часового пояса (например, 'Europe/Moscow').

    Returns:
        datetime.datetime: Объект datetime в указанном часовом поясе.
    """
    utc_tz = pytz.utc
    target_tz = pytz.timezone(tz_name)

    if dt.tzinfo is None:
        # Если datetime наивный, предполагаем, что он в UTC
        dt = utc_tz.localize(dt)
    else:
        # Если datetime уже timezone-aware, конвертируем его в UTC
        dt = dt.astimezone(utc_tz)

    return dt.astimezone(target_tz)

def get_current_time_in_timezone(tz_name: str) -> datetime.datetime:
    """
    Возвращает текущее время в указанном часовом поясе.

    Args:
        tz_name (str): Название целевого часового пояса (например, 'Europe/Moscow').

    Returns:
        datetime.datetime: Текущее время в указанном часовом поясе.
    """
    target_tz = pytz.timezone(tz_name)
    return datetime.datetime.now(target_tz)

async def get_work_schedule_for_day(session: AsyncSession, date: datetime.date) -> Optional[WorkSchedule]:
    """
    Возвращает рабочее расписание для указанного дня недели.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        date (datetime.date): Дата, для которой нужно получить расписание.

    Returns:
        Optional[WorkSchedule]: Объект WorkSchedule или None, если расписание не найдено.
    """
    weekday = date.weekday()
    result = await session.execute(select(WorkSchedule).where(WorkSchedule.weekday == weekday))
    return result.scalar_one_or_none()

async def get_appointments_for_day(session: AsyncSession, date: datetime.date) -> list[Appointment]:
    """
    Возвращает список записей на указанный день.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        date (datetime.date): Дата, для которой нужно получить записи.

    Returns:
        list[Appointment]: Список записей.
    """
    start_of_day = datetime.datetime.combine(date, datetime.time.min)
    end_of_day = datetime.datetime.combine(date, datetime.time.max)
    result = await session.execute(
        select(Appointment)
        .where(Appointment.start_time >= start_of_day, Appointment.start_time <= end_of_day)
        .order_by(Appointment.start_time)
    )
    return result.scalars().all()

def get_available_time_slots(
    schedule: WorkSchedule,
    appointments: list[Appointment],
    service_duration: int,
    date: datetime.date,
    timezone_str: str
) -> list[datetime.time]:
    """
    Рассчитывает и возвращает список доступных временных слотов для записи.

    Args:
        schedule (WorkSchedule): Рабочее расписание на день.
        appointments (list[Appointment]): Список существующих записей на день.
        service_duration (int): Длительность услуги в минутах.
        date (datetime.date): Дата, для которой рассчитываются слоты.
        timezone_str (str): Часовой пояс.

    Returns:
        list[datetime.time]: Список доступных временных слотов.
    """
    if not schedule or not schedule.is_working:
        return []

    tz = pytz.timezone(timezone_str)
    now = datetime.datetime.now(tz)

    work_start_time = tz.localize(datetime.datetime.combine(date, schedule.start_time))
    work_end_time = tz.localize(datetime.datetime.combine(date, schedule.end_time))

    available_slots = []
    current_time = work_start_time

    # Начинаем проверку слотов с текущего времени, если выбран сегодняшний день
    if date == now.date() and now > current_time:
        # Округляем текущее время до следующего 30-минутного интервала
        minute = 30 if now.minute >= 30 else 0
        current_time = now.replace(minute=minute, second=0, microsecond=0)
        if now.minute > 0:
            current_time += datetime.timedelta(minutes=30)


    while current_time + datetime.timedelta(minutes=service_duration) <= work_end_time:
        slot_end_time = current_time + datetime.timedelta(minutes=service_duration)
        is_slot_available = True

        for appointment in appointments:
            appointment_start = appointment.start_time.astimezone(tz)
            appointment_end = appointment.end_time.astimezone(tz)

            # Проверка на пересечение временных интервалов
            if max(current_time, appointment_start) < min(slot_end_time, appointment_end):
                is_slot_available = False
                break

        if is_slot_available:
            available_slots.append(current_time.time())

        current_time += datetime.timedelta(minutes=30) # Интервал между слотами

    return available_slots
