import logging

from aiogram import Router, types
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent

from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.error()
async def error_handler(event: ErrorEvent) -> None:
    """
    Глобальный обработчик ошибок бота.

    Args:
        event (ErrorEvent): Событие ошибки.
    """
    logger.error(f"Произошла ошибка: {event.exception}", exc_info=True)

    if event.update.callback_query:
        try:
            await event.update.callback_query.message.edit_text(
                "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
    elif event.update.message:
        try:
            await event.update.message.answer(
                "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
