import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.session import Base

class User(Base):
    """
    Модель пользователя Telegram.

    Attributes:
        id (int): Уникальный идентификатор пользователя в базе данных.
        telegram_id (int): ID пользователя в Telegram.
        username (Optional[str]): Имя пользователя в Telegram (если есть).
        full_name (str): Полное имя пользователя в Telegram.
        created_at (datetime.datetime): Дата и время создания записи пользователя.
        appointments (list["Appointment"]): Список записей пользователя.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

class Service(Base):
    """
    Модель услуги ногтевого сервиса.

    Attributes:
        id (int): Уникальный идентификатор услуги в базе данных.
        name (str): Название услуги.
        duration_minutes (int): Длительность услуги в минутах.
        price (float): Стоимость услуги.
        description (Optional[str]): Описание услуги.
        active (bool): Статус активности услуги (True - активна, False - неактивна).
        appointments (list["Appointment"]): Список записей, связанных с этой услугой.
    """
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="service")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name='{self.name}')>"

class Appointment(Base):
    """
    Модель записи на услугу.

    Attributes:
        id (int): Уникальный идентификатор записи в базе данных.
        user_id (int): ID пользователя, сделавшего запись.
        service_id (int): ID выбранной услуги.
        start_time (datetime.datetime): Время начала записи (UTC).
        end_time (datetime.datetime): Время окончания записи (UTC).
        status (str): Статус записи (например, 'pending', 'confirmed', 'cancelled', 'completed').
        google_event_id (Optional[str]): ID события в Google Calendar (если создано).
        created_at (datetime.datetime): Дата и время создания записи.
        user (User): Объект пользователя, связанный с записью.
        service (Service): Объект услуги, связанный с записью.
    """
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    google_event_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="appointments")
    service: Mapped["Service"] = relationship("Service", back_populates="appointments")

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, user_id={self.user_id}, service_id={self.service_id}, start_time='{self.start_time}')>"

class WorkSchedule(Base):
    """
    Модель рабочего расписания мастера по дням недели.

    Attributes:
        id (int): Уникальный идентификатор записи расписания.
        weekday (int): День недели (0=понедельник, 6=воскресенье).
        start_time (datetime.time): Время начала рабочего дня.
        end_time (datetime.time): Время окончания рабочего дня.
        is_working (bool): Флаг, указывающий, является ли день рабочим.
    """
    __tablename__ = "work_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    weekday: Mapped[int] = mapped_column(Integer, unique=True, nullable=False) # 0-6 для дней недели
    start_time: Mapped[datetime.time] = mapped_column(Time(timezone=True), nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time(timezone=True), nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<WorkSchedule(id={self.id}, weekday={self.weekday}, is_working={self.is_working})>"

class Holiday(Base):
    """
    Модель выходных и праздничных дней.

    Attributes:
        id (int): Уникальный идентификатор выходного дня.
        date (datetime.date): Дата выходного дня.
        reason (Optional[str]): Причина выходного дня.
    """
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(DateTime().with_variant(String, "sqlite"), unique=True, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<Holiday(id={self.id}, date='{self.date}')>"

class Settings(Base):
    """
    Модель для хранения общих настроек приложения.

    Attributes:
        id (int): Уникальный идентификатор настроек (всегда 1).
        admin_id (int): ID администратора бота.
        planning_horizon_days (int): Горизонт планирования записей в днях.
        timezone (str): Часовой пояс, используемый в приложении.
    """
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, default=1)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    planning_horizon_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    timezone: Mapped[str] = mapped_column(String, default="Europe/Moscow", nullable=False)

    def __repr__(self) -> str:
        return f"<Settings(id={self.id}, admin_id={self.admin_id})>"
