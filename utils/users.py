import logging

from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

logger = logging.getLogger(__name__)

async def get_or_create_user(session: AsyncSession, from_user: types.User) -> tuple[User, bool]:
    """
    Возвращает пользователя из базы, создавая его при необходимости.

    Нужно не только в /start: пользователь может нажать кнопку в старом
    сообщении, ни разу не запустив бота (или после сброса базы).

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        from_user (types.User): Пользователь Telegram из события.

    Returns:
        tuple[User, bool]: Пользователь и флаг, был ли он только что создан.
    """
    result = await session.execute(select(User).where(User.telegram_id == from_user.id))
    user = result.scalar_one_or_none()
    if user:
        return user, False

    user = User(
        telegram_id=from_user.id,
        full_name=from_user.full_name,
        username=from_user.username,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info(f"Новый пользователь зарегистрирован: {user.full_name} (ID: {user.telegram_id})")
    return user, True
