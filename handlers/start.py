import logging

from aiogram import Router, types
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from utils.keyboards import main_menu_keyboard
from utils.messages import WELCOME_MESSAGE, RETURNING_USER_MESSAGE
from utils.users import get_or_create_user

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
    user, created = await get_or_create_user(session, message.from_user)

    template = WELCOME_MESSAGE if created else RETURNING_USER_MESSAGE
    if not created:
        logger.info(f"Пользователь {user.full_name} (ID: {user.telegram_id}) уже зарегистрирован.")

    await message.answer(
        template.format(full_name=message.from_user.full_name),
        reply_markup=main_menu_keyboard()
    )
