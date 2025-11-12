import logging
import datetime

from aiogram import Router, types, F, Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Appointment, User
from utils.keyboards import main_menu_keyboard, appointments_keyboard, confirmation_cancel_keyboard
from config import load_config

logger = logging.getLogger(__name__)
router = Router()
config = load_config()

async def get_user_appointments(session: AsyncSession, telegram_id: int) -> list[Appointment]:
    """
    Возвращает список предстоящих записей пользователя.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        telegram_id (int): Telegram ID пользователя.

    Returns:
        list[Appointment]: Список записей.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    result = await session.execute(
        select(Appointment)
        .join(User)
        .where(User.telegram_id == telegram_id, Appointment.start_time >= now_utc, Appointment.status == 'confirmed')
        .options(selectinload(Appointment.service))
        .order_by(Appointment.start_time)
    )
    return result.scalars().all()

@router.callback_query(F.data == "my_appointments")
async def my_appointments_handler(callback: types.CallbackQuery, session: AsyncSession) -> None:
    """
    Обработчик для кнопки "Мои записи". Отображает список предстоящих
    записей пользователя.
    """
    await callback.answer()
    
    appointments = await get_user_appointments(session, callback.from_user.id)
    
    if not appointments:
        await callback.message.edit_text(
            "У вас нет предстоящих записей.",
            reply_markup=main_menu_keyboard()
        )
        return

    response_text = "<b>Ваши предстоящие записи:</b>\n\n"
    for app in appointments:
        response_text += (
            f"<b>Услуга:</b> {app.service.name}\n"
            f"<b>Дата:</b> {app.start_time.strftime('%d.%m.%Y')}\n"
            f"<b>Время:</b> {app.start_time.strftime('%H:%M')}\n"
            f"--------------------\n"
        )

    await callback.message.edit_text(response_text, reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "cancel_appointment")
async def cancel_appointment_list_handler(callback: types.CallbackQuery, session: AsyncSession) -> None:
    """
    Обработчик для кнопки "Отменить запись". Отображает список записей
    для отмены.
    """
    await callback.answer()
    appointments = await get_user_appointments(session, callback.from_user.id)

    if not appointments:
        await callback.message.edit_text(
            "У вас нет предстоящих записей для отмены.",
            reply_markup=main_menu_keyboard()
        )
        return

    await callback.message.edit_text(
        "Какую запись вы хотите отменить?",
        reply_markup=appointments_keyboard(appointments)
    )

@router.callback_query(F.data.startswith("cancel_appointment_"))
async def cancel_appointment_confirm_handler(callback: types.CallbackQuery, session: AsyncSession) -> None:
    """
    Запрашивает подтверждение отмены записи.
    """
    await callback.answer()
    appointment_id = int(callback.data.split("_")[2])
    
    appointment = await session.get(Appointment, appointment_id, options=[selectinload(Appointment.service)])
    if not appointment:
        await callback.message.edit_text("Запись не найдена.", reply_markup=main_menu_keyboard())
        return

    await callback.message.edit_text(
        f"Вы уверены, что хотите отменить запись на услугу "
        f"<b>{appointment.service.name}</b> на "
        f"<b>{appointment.start_time.strftime('%d.%m.%Y в %H:%M')}</b>?",
        reply_markup=confirmation_cancel_keyboard(appointment_id)
    )

@router.callback_query(F.data.startswith("confirm_cancel_"))
async def cancel_appointment_confirmed_handler(callback: types.CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """
    Обрабатывает подтвержденную отмену записи, обновляет статус в БД
    и отправляет уведомления.
    """
    await callback.answer("Запись отменена.")
    appointment_id = int(callback.data.split("_")[2])

    appointment = await session.get(Appointment, appointment_id, options=[selectinload(Appointment.service), selectinload(Appointment.user)])
    if not appointment:
        await callback.message.edit_text("Запись не найдена.", reply_markup=main_menu_keyboard())
        return

    appointment.status = "cancelled"
    await session.commit()

    await callback.message.edit_text(
        f"Ваша запись на <b>{appointment.start_time.strftime('%d.%m.%Y в %H:%M')}</b> успешно отменена.",
        reply_markup=main_menu_keyboard()
    )

    # Уведомление мастеру
    await bot.send_message(
        chat_id=config.tg_bot.admin_id,
        text=(
            f"Клиент отменил запись!\n\n"
            f"Клиент: {appointment.user.full_name} (@{appointment.user.username or 'N/A'})\n"
            f"Услуга: {appointment.service.name}\n"
            f"Дата: {appointment.start_time.strftime('%d.%m.%Y')}\n"
            f"Время: {appointment.start_time.strftime('%H:%M')}"
        )
    )
