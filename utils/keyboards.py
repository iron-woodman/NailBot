from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models import Service
import datetime

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для главного меню бота.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура главного меню.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Записаться", callback_data="book_appointment"),
        InlineKeyboardButton(text="Мои записи", callback_data="my_appointments")
    )
    builder.row(
        InlineKeyboardButton(text="Отменить запись", callback_data="cancel_appointment"),
        InlineKeyboardButton(text="Контакты", callback_data="contacts")
    )
    return builder.as_markup()

def services_keyboard(services: list[Service]) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру со списком услуг.

    Args:
        services (list[Service]): Список услуг.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура со списком услуг.
    """
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.row(
            InlineKeyboardButton(
                text=f"{service.name} ({service.duration_minutes} мин) - {service.price} руб.",
                callback_data=f"service_{service.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="Назад в главное меню", callback_data="back_to_main_menu"))
    return builder.as_markup()

def appointments_keyboard(appointments: list) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру со списком записей и кнопками для отмены.

    Args:
        appointments (list[Appointment]): Список записей пользователя.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура для управления записями.
    """
    builder = InlineKeyboardBuilder()
    for appointment in appointments:
        builder.row(
            InlineKeyboardButton(
                text=f"Отменить запись на {appointment.start_time.strftime('%d.%m %H:%M')}",
                callback_data=f"cancel_appointment_{appointment.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="Назад в главное меню", callback_data="back_to_main_menu"))
    return builder.as_markup()

def confirmation_cancel_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подтверждения отмены записи.

    Args:
        appointment_id (int): ID записи для отмены.

    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да, отменить", callback_data=f"confirm_cancel_{appointment_id}"),
        InlineKeyboardButton(text="Нет, вернуться", callback_data="cancel_appointment")
    )
    return builder.as_markup()

def calendar_keyboard(year: int, month: int, available_dates: list[datetime.date]) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с календарем для выбора даты.

    Args:
        year (int): Год для отображения.
        month (int): Месяц для отображения.
        available_dates (list[datetime.date]): Список доступных для записи дат.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура календаря.
    """
    builder = InlineKeyboardBuilder()
    today = datetime.date.today()

    # Заголовок с месяцем и годом
    builder.row(InlineKeyboardButton(text=f"{datetime.date(year, month, 1).strftime('%B %Y')}", callback_data="ignore"))

    # Дни недели
    builder.row(
        InlineKeyboardButton(text="Пн", callback_data="ignore"),
        InlineKeyboardButton(text="Вт", callback_data="ignore"),
        InlineKeyboardButton(text="Ср", callback_data="ignore"),
        InlineKeyboardButton(text="Чт", callback_data="ignore"),
        InlineKeyboardButton(text="Пт", callback_data="ignore"),
        InlineKeyboardButton(text="Сб", callback_data="ignore"),
        InlineKeyboardButton(text="Вс", callback_data="ignore")
    )

    # Дни месяца
    first_day_of_month = datetime.date(year, month, 1)
    # Определяем, с какого дня недели начинается месяц (0=Пн, 6=Вс)
    # Python's weekday() returns 0 for Monday, 6 for Sunday
    # We want to start our calendar grid on Monday, so we need to adjust
    start_offset = first_day_of_month.weekday()

    # Заполняем пустые клетки до первого дня месяца
    row_buttons = []
    for _ in range(start_offset):
        row_buttons.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    if month == 12:
        days_in_month = 31
    else:
        days_in_month = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)).day

    for day in range(1, days_in_month + 1):
        current_date = datetime.date(year, month, day)
        if current_date in available_dates and current_date >= today:
            row_buttons.append(InlineKeyboardButton(text=str(day), callback_data=f"date_{current_date.isoformat()}"))
        else:
            row_buttons.append(InlineKeyboardButton(text=str(day), callback_data="ignore"))

        if len(row_buttons) == 7:
            builder.row(*row_buttons)
            row_buttons = []

    if row_buttons:
        builder.row(*row_buttons)

    # Кнопки навигации по месяцам
    prev_month = first_day_of_month - datetime.timedelta(days=1)
    next_month = first_day_of_month + datetime.timedelta(days=days_in_month)

    builder.row(
        InlineKeyboardButton(text="<", callback_data=f"calendar_nav_{prev_month.year}_{prev_month.month}"),
        InlineKeyboardButton(text="Назад в главное меню", callback_data="back_to_main_menu"),
        InlineKeyboardButton(text=">", callback_data=f"calendar_nav_{next_month.year}_{next_month.month}")
    )

    return builder.as_markup()

def time_slots_keyboard(time_slots: list[datetime.time]) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру с доступными временными слотами.

    Args:
        time_slots (list[datetime.time]): Список доступных временных слотов.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура временных слотов.
    """
    builder = InlineKeyboardBuilder()
    for slot in time_slots:
        builder.row(
            InlineKeyboardButton(
                text=slot.strftime('%H:%M'),
                callback_data=f"time_{slot.isoformat()}"
            )
        )
    builder.row(InlineKeyboardButton(text="Назад к выбору даты", callback_data="back_to_date_selection"))
    return builder.as_markup()

def confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подтверждения записи.

    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data="confirm_appointment"),
        InlineKeyboardButton(text="Отменить", callback_data="cancel_appointment_creation")
    )
    return builder.as_markup()
