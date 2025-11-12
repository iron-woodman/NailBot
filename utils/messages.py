WELCOME_MESSAGE = """
Привет, {full_name}! Добро пожаловать в бот для записи к мастеру ногтевого сервиса.

Здесь вы можете:
- Записаться на услугу
- Просмотреть свои записи
- Отменить запись
- Связаться с нами
"""

RETURNING_USER_MESSAGE = """
С возвращением, {full_name}! Чем могу помочь?
"""

NO_SERVICES_MESSAGE = """
К сожалению, на данный момент нет доступных услуг для записи.
"""

NO_APPOINTMENTS_MESSAGE = """
У вас нет предстоящих записей.
"""

NO_AVAILABLE_DATES_MESSAGE = """
К сожалению, на ближайшее время нет доступных дат для записи.
"""

NO_AVAILABLE_TIME_MESSAGE = """
К сожалению, на выбранную дату нет свободного времени. Пожалуйста, выберите другую дату.
"""

APPOINTMENT_NOT_FOUND_MESSAGE = """
Запись не найдена.
"""

APPOINTMENT_CANCELLED_MESSAGE = """
Ваша запись на {date} в {time} успешно отменена.
"""

APPOINTMENT_CREATION_CANCELLED_MESSAGE = """
Создание записи отменено. Вы возвращены в главное меню.
"""

CONFIRM_APPOINTMENT_MESSAGE = """
<b>Подтвердите вашу запись:</b>

<b>Услуга:</b> {service_name}
<b>Дата:</b> {date}
<b>Время:</b> {time}

Все верно?
"""

APPOINTMENT_CONFIRMED_MESSAGE = """
Отлично! Ваша запись на услугу <b>'{service_name}'</b> успешно создана.

<b>Дата:</b> {date}
<b>Время:</b> {time} ({timezone})

<a href='{calendar_link}'>Добавить в Google Calendar</a>

Мы будем ждать вас!
"""

MASTER_NEW_APPOINTMENT_MESSAGE = """
Новая запись!

Клиент: {full_name} (@{username})
Услуга: {service_name}
Дата: {date}
Время: {time}
"""

MASTER_CANCELLED_APPOINTMENT_MESSAGE = """
Клиент отменил запись!

Клиент: {full_name} (@{username})
Услуга: {service_name}
Дата: {date}
Время: {time}
"""

REMINDER_24H_MESSAGE = """
Напоминание!

У вас скоро запись на услугу <b>'{service_name}'</b>.
Ждем вас {date} в <b>{time}</b>.

До встречи осталось 24 часа!
"""

REMINDER_2H_MESSAGE = """
Напоминание!

У вас скоро запись на услугу <b>'{service_name}'</b>.
Ждем вас сегодня в <b>{time}</b>.

До встречи осталось 2 часа!
"""

ERROR_MESSAGE = """
Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.
"""
