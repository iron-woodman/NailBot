import logging

from aiogram import Router, types
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def command_start_handler(message: types.Message, session: AsyncSession) -> None:
    """
    Обработчик команды /start. Регистрирует нового пользователя в базе данных, если его нет.

    Args:
        message (types.Message): Объект сообщения от пользователя.
        session (AsyncSession): Асинхронная сессия базы данных.
    """
    user_telegram_id = message.from_user.id
    user_full_name = message.from_user.full_name
    user_username = message.from_user.username

    # Проверка наличия пользователя в БД
    result = await session.execute(select(User).where(User.telegram_id == user_telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        # Если пользователя нет, создаем нового
        new_user = User(
            telegram_id=user_telegram_id,
            full_name=user_full_name,
            username=user_username
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Новый пользователь зарегистрирован: {new_user.full_name} (ID: {new_user.telegram_id})")
        await message.answer(f"Привет, {user_full_name}! Добро пожаловать в бот для записи к мастеру ногтевого сервиса.", reply_markup=main_menu_keyboard())
    else:
        logger.info(f"Пользователь {user.full_name} (ID: {user.telegram_id}) уже зарегистрирован.")
        await message.answer(f"С возвращением, {user_full_name}! Чем могу помочь?", reply_markup=main_menu_keyboard())

    # TODO: Добавить вызов главного меню
