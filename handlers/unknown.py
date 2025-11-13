import logging

from aiogram import Router, types
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message()
async def handle_unexpected_message(message: types.Message) -> None:
    """
    Обработчик неожиданных сообщений, которые не соответствуют ни одному шаблону.

    Args:
        message (types.Message): Объект сообщения от пользователя.
    """
    logger.info(f"Получено неожиданное сообщение от {message.from_user.id}: {message.text}")

    await message.answer(
        "Не понял вашу команду. Пожалуйста, используйте кнопки меню.",
        reply_markup=main_menu_keyboard()
    )
