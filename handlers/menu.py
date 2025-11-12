import logging

from aiogram import Router, types
from aiogram.filters import Text

from utils.keyboards import main_menu_keyboard
from handlers.appointments import my_appointments_handler

logger = logging.getLogger(__name__)
router = Router()

@router.message(Text(text="Главное меню"))
@router.callback_query(Text(text="back_to_main_menu"))
async def show_main_menu(message: types.Message | types.CallbackQuery) -> None:
    """
    Показывает главное меню бота.

    Args:
        message (types.Message | types.CallbackQuery): Объект сообщения или callback-запроса.
    """
    if isinstance(message, types.Message):
        await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
    elif isinstance(message, types.CallbackQuery):
        await message.message.edit_text("Выберите действие:", reply_markup=main_menu_keyboard())
        await message.answer()

# Регистрируем обработчик для кнопки "Мои записи"
router.callback_query.register(my_appointments_handler, Text(text="my_appointments"))
