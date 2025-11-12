import logging

from aiogram import Router, types, F
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

CONTACTS_TEXT = """
<b>Наши контакты:</b>

📞 <b>Телефон:</b> +7 (999) 123-45-67
💬 <b>Telegram:</b> @your_telegram_username
📸 <b>Instagram:</b> @your_instagram_handle
📍 <b>Адрес:</b> г. Город, ул. Улица, д. 1, каб. 101

⏰ <b>Время работы:</b>
Пн-Пт: 10:00 - 20:00
Сб: 11:00 - 19:00
Вс: выходной
"""

@router.callback_query(F.data == "contacts")
async def contacts_handler(callback: types.CallbackQuery):
    """
    Обработчик для кнопки "Контакты". Отображает контактную информацию.
    """
    await callback.answer()
    await callback.message.edit_text(
        CONTACTS_TEXT,
        reply_markup=main_menu_keyboard(),
        disable_web_page_preview=True
    )
