import logging
import datetime
import pytz

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Service, User, Appointment
from utils.keyboards import (
    services_keyboard, calendar_keyboard, time_slots_keyboard,
    confirmation_keyboard, main_menu_keyboard
)
from utils.time_utils import (
    get_planning_horizon, is_working_day, is_holiday,
    get_current_time_in_timezone, get_timezone, get_work_schedule_for_day,
    get_appointments_for_day, get_available_time_slots
)
from utils.google_calendar import generate_google_calendar_link
from config import load_config

logger = logging.getLogger(__name__)
router = Router()
config = load_config()

class Booking(StatesGroup):
    """
    Состояния для процесса записи на услугу.
    """
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirming_appointment = State()

async def get_active_services(session: AsyncSession) -> list[Service]:
    """
    Возвращает список активных услуг из базы данных.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        list[Service]: Список активных услуг.
    """
    result = await session.execute(select(Service).where(Service.active == True).order_by(Service.name))
    return result.scalars().all()

async def get_available_dates(session: AsyncSession) -> list[datetime.date]:
    """
    Возвращает список доступных для записи дат.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        list[datetime.date]: Список доступных дат.
    """
    planning_horizon = await get_planning_horizon(session)
    timezone_str = await get_timezone(session)
    today = get_current_time_in_timezone(timezone_str).date()
    
    available_dates = []
    for i in range(planning_horizon):
        current_date = today + datetime.timedelta(days=i)
        if await is_working_day(session, current_date) and not await is_holiday(session, current_date):
            available_dates.append(current_date)
    return available_dates

@router.callback_query(F.data == "book_appointment")
async def book_appointment_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """
    Обработчик нажатия на кнопку "Записаться". Начинает процесс записи,
    отображая список доступных услуг.
    """
    await callback.answer()
    services = await get_active_services(session)
    if not services:
        await callback.message.edit_text("К сожалению, на данный момент нет доступных услуг для записи.")
        return

    await callback.message.edit_text(
        "Выберите услугу:",
        reply_markup=services_keyboard(services)
    )
    await state.set_state(Booking.choosing_service)

@router.callback_query(Booking.choosing_service, F.data.startswith("service_"))
async def service_chosen_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """
    Обработчик выбора услуги. Сохраняет выбранную услугу в контекст
    и переходит к выбору даты, отображая календарь.
    """
    await callback.answer()
    service_id = int(callback.data.split("_")[1])

    service = await session.get(Service, service_id)
    if not service:
        await callback.message.edit_text("Выбранная услуга не найдена. Пожалуйста, попробуйте еще раз.")
        return

    await state.update_data(service_id=service.id, service_name=service.name, service_duration=service.duration_minutes)

    available_dates = await get_available_dates(session)
    timezone_str = await get_timezone(session)
    today = get_current_time_in_timezone(timezone_str).date()
    
    await callback.message.edit_text(
        f"Вы выбрали услугу: {service.name}.\n\nТеперь выберите дату:",
        reply_markup=calendar_keyboard(today.year, today.month, available_dates)
    )
    await state.set_state(Booking.choosing_date)

@router.callback_query(Booking.choosing_date, F.data.startswith("calendar_"))
async def calendar_navigation_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """
    Обработчик навигации по календарю (переключение месяцев).
    """
    await callback.answer()
    parts = callback.data.split("_")
    if len(parts) < 2:
        return

    action = parts[1]
    if action == "ignore":
        return

    if action == "nav" and len(parts) >= 4:
        year, month = int(parts[2]), int(parts[3])

        available_dates = await get_available_dates(session)

        await callback.message.edit_text(
            "Выберите дату:",
            reply_markup=calendar_keyboard(year, month, available_dates)
        )

@router.callback_query(Booking.choosing_date, F.data.startswith("date_"))
async def date_chosen_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """
    Обработчик выбора даты. Сохраняет выбранную дату, рассчитывает доступное время
    и предлагает его для выбора.
    """
    await callback.answer()
    selected_date_str = callback.data.split("_")[1]
    selected_date = datetime.date.fromisoformat(selected_date_str)

    await state.update_data(selected_date=selected_date.isoformat())
    user_data = await state.get_data()
    service_duration = user_data.get("service_duration")
    
    timezone_str = await get_timezone(session)
    schedule = await get_work_schedule_for_day(session, selected_date)
    appointments = await get_appointments_for_day(session, selected_date)

    if not schedule or not service_duration:
        await callback.message.edit_text("Произошла ошибка. Пожалуйста, начните заново.")
        await state.clear()
        return

    time_slots = get_available_time_slots(schedule, appointments, service_duration, selected_date, timezone_str)

    if not time_slots:
        await callback.message.edit_text(
            "К сожалению, на выбранную дату нет свободного времени. Пожалуйста, выберите другую дату."
        )
        return

    await callback.message.edit_text(
        f"Вы выбрали дату: {selected_date.strftime('%d.%m.%Y')}.\n\nТеперь выберите время:",
        reply_markup=time_slots_keyboard(time_slots)
    )
    await state.set_state(Booking.choosing_time)

@router.callback_query(Booking.choosing_time, F.data.startswith("time_"))
async def time_chosen_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора времени. Сохраняет выбранное время и переходит
    к подтверждению записи.
    """
    await callback.answer()
    selected_time_str = callback.data.split("_")[1]
    
    await state.update_data(selected_time=selected_time_str)
    
    user_data = await state.get_data()
    service_name = user_data.get("service_name")
    selected_date = datetime.date.fromisoformat(user_data.get("selected_date"))
    
    await callback.message.edit_text(
        f"<b>Подтвердите вашу запись:</b>\n\n"
        f"<b>Услуга:</b> {service_name}\n"
        f"<b>Дата:</b> {selected_date.strftime('%d.%m.%Y')}\n"
        f"<b>Время:</b> {selected_time_str}\n\n"
        f"Все верно?",
        reply_markup=confirmation_keyboard()
    )
    await state.set_state(Booking.confirming_appointment)

@router.callback_query(Booking.confirming_appointment, F.data == "confirm_appointment")
async def confirm_appointment_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик подтверждения записи. Сохраняет запись в БД,
    отправляет уведомления и генерирует ссылку на Google Calendar.
    """
    await callback.answer("Запись подтверждена!")
    user_data = await state.get_data()
    
    telegram_id = callback.from_user.id
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one()

    service_id = user_data.get("service_id")
    service_name = user_data.get("service_name")
    service_duration = user_data.get("service_duration")
    selected_date_str = user_data.get("selected_date")
    selected_time_str = user_data.get("selected_time")

    selected_date = datetime.date.fromisoformat(selected_date_str)
    selected_time = datetime.time.fromisoformat(selected_time_str)

    timezone_str = await get_timezone(session)
    tz = pytz.timezone(timezone_str)
    
    start_time_naive = datetime.datetime.combine(selected_date, selected_time)
    start_time_aware = tz.localize(start_time_naive)
    end_time_aware = start_time_aware + datetime.timedelta(minutes=service_duration)

    # Сохранение в UTC
    start_time_utc = start_time_aware.astimezone(pytz.utc)
    end_time_utc = end_time_aware.astimezone(pytz.utc)

    new_appointment = Appointment(
        user_id=user.id,
        service_id=service_id,
        start_time=start_time_utc,
        end_time=end_time_utc,
        status="confirmed"
    )
    session.add(new_appointment)
    await session.commit()

    calendar_link = generate_google_calendar_link(service_name, start_time_utc, end_time_utc)

    await callback.message.edit_text(
        f"Отлично! Ваша запись на услугу <b>'{service_name}'</b> успешно создана.\n\n"
        f"<b>Дата:</b> {selected_date.strftime('%d.%m.%Y')}\n"
        f"<b>Время:</b> {selected_time_str} ({timezone_str})\n\n"
        f"<a href='{calendar_link}'>Добавить в Google Calendar</a>\n\n"
        f"Мы будем ждать вас!",
        disable_web_page_preview=True
    )

    # Уведомление мастеру
    await bot.send_message(
        chat_id=config.tg_bot.admin_id,
        text=(
            f"Новая запись!\n\n"
            f"Клиент: {user.full_name} (@{user.username or 'N/A'})\n"
            f"Услуга: {service_name}\n"
            f"Дата: {selected_date.strftime('%d.%m.%Y')}\n"
            f"Время: {selected_time_str}"
        )
    )
    
    await state.clear()

@router.callback_query(Booking.confirming_appointment, F.data == "cancel_appointment_creation")
async def cancel_appointment_creation_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик отмены создания записи.
    """
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "Создание записи отменено. Вы возвращены в главное меню.",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(Booking.choosing_time, F.data == "back_to_date_selection")
async def back_to_date_selection_handler(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    """
    Обработчик для кнопки "Назад к выбору даты". Возвращает пользователя
    к календарю.
    """
    await callback.answer()
    available_dates = await get_available_dates(session)
    timezone_str = await get_timezone(session)
    today = get_current_time_in_timezone(timezone_str).date()

    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=calendar_keyboard(today.year, today.month, available_dates)
    )
    await state.set_state(Booking.choosing_date)
