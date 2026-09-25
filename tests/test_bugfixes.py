"""
Проверки на баги из бэклога аудита.

Запуск: TZ=Europe/Moscow python3 tests/test_bugfixes.py
"""
import asyncio
import datetime
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("BOT_TOKEN", "123:TEST")
os.environ.setdefault("ADMIN_ID", "777")

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.session import Base
from database.models import WorkSchedule, Holiday
from handlers.appointments import parse_appointment_id
from utils.time_utils import BOOKING_LEAD_MINUTES, get_available_time_slots
from utils.users import get_or_create_user

MSK = "Europe/Moscow"


def test_parse_appointment_id_survives_non_numeric():
    """Нечисловой хвост не должен валить хендлер с ValueError."""
    assert parse_appointment_id("cancel_appointment_12") == 12
    assert parse_appointment_id("confirm_cancel_7") == 7
    # ровно тот callback, на котором падал int(): "creation" вместо id
    assert parse_appointment_id("cancel_appointment_creation") is None
    assert parse_appointment_id("cancel_appointment") is None
    print("[OK] parse_appointment_id: нечисловой хвост -> None, а не ValueError")


def test_slots_respect_lead_buffer():
    """Слот, до которого меньше запаса, предлагать нельзя."""
    tz = pytz.timezone(MSK)
    now = datetime.datetime.now(tz)
    schedule = WorkSchedule(weekday=now.weekday(), start_time=datetime.time(0, 0),
                            end_time=datetime.time(23, 59), is_working=True)

    slots = get_available_time_slots(schedule, [], 30, now.date(), MSK)
    earliest_allowed = now + datetime.timedelta(minutes=BOOKING_LEAD_MINUTES)

    for slot in slots:
        slot_dt = tz.localize(datetime.datetime.combine(now.date(), slot))
        assert slot_dt >= earliest_allowed, f"слот {slot} ближе, чем запас {BOOKING_LEAD_MINUTES} мин"
    print(f"[OK] слоты: ближе {BOOKING_LEAD_MINUTES} мин к текущему времени не предлагаются")


def test_slots_stay_on_work_start_grid():
    """Сетка слотов отсчитывается от начала рабочего дня, даже если он не в ровный час."""
    schedule = WorkSchedule(weekday=0, start_time=datetime.time(9, 15),
                            end_time=datetime.time(18, 0), is_working=True)
    future = datetime.date.today() + datetime.timedelta(days=3)

    slots = get_available_time_slots(schedule, [], 60, future, MSK)

    assert slots[0] == datetime.time(9, 15), f"первый слот {slots[0]}, ожидали 09:15"
    assert datetime.time(9, 45) in slots, "сетка уехала с шага 30 мин от 09:15"
    assert datetime.time(9, 30) not in slots, "слот не на сетке рабочего дня"
    print("[OK] слоты: сетка привязана к началу рабочего дня (09:15, 09:45, ...)")


def test_sqlite_migration_adds_missing_columns():
    """База, созданная до появления reminder_* колонок, должна досоздать их."""
    path = os.path.join(tempfile.mkdtemp(), "legacy.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, service_id INTEGER NOT NULL,
            start_time DATETIME NOT NULL, end_time DATETIME NOT NULL,
            status VARCHAR NOT NULL, google_event_id VARCHAR, created_at DATETIME);
        INSERT INTO appointments (user_id, service_id, start_time, end_time, status)
        VALUES (1, 1, '2026-10-12 07:00:00.000000', '2026-10-12 08:00:00.000000', 'confirmed');
    """)
    conn.commit()
    before = {r[1] for r in conn.execute("PRAGMA table_info(appointments)")}
    assert "reminder_24h_sent" not in before
    conn.close()

    # init_db читает DATABASE_URL на импорте модуля, поэтому запускаем в подпроцессе
    import subprocess
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{path}",
           "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..")}
    subprocess.run([sys.executable, "-c",
                    "import asyncio; from database.session import init_db; asyncio.run(init_db())"],
                   env=env, check=True, capture_output=True)

    conn = sqlite3.connect(path)
    after = {r[1] for r in conn.execute("PRAGMA table_info(appointments)")}
    assert {"reminder_24h_sent", "reminder_2h_sent"} <= after, f"колонки не добавлены: {after}"
    row = conn.execute("SELECT status, reminder_24h_sent, reminder_2h_sent FROM appointments").fetchone()
    assert row == ("confirmed", 0, 0), f"данные повреждены: {row}"
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    conn.close()
    print("[OK] миграция: reminder_* колонки досозданы, данные целы, WAL включён")


async def test_get_or_create_user_and_holiday_date():
    """Пользователь создаётся на лету; Holiday.date остаётся датой."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    S = async_sessionmaker(engine, expire_on_commit=False)

    class FakeFrom:
        id, full_name, username = 555, "Новый клиент", "newbie"

    async with S() as s:
        user, created = await get_or_create_user(s, FakeFrom())
        assert created and user.id, "пользователь не создан"
        again, created2 = await get_or_create_user(s, FakeFrom())
        assert not created2 and again.id == user.id, "создан дубль"
    print("[OK] get_or_create_user: создаёт один раз, потом возвращает существующего")

    async with S() as s:
        s.add(Holiday(date=datetime.date(2026, 10, 12), reason="отпуск"))
        await s.commit()
    async with S() as s:
        found = (await s.execute(
            select(Holiday).where(Holiday.date == datetime.date(2026, 10, 12)))).scalar_one_or_none()
        assert found is not None, "поиск выходного по date не работает"
        assert found.date == datetime.date(2026, 10, 12), f"вернулось {found.date!r}, а не date"
    print("[OK] Holiday.date: хранится и читается как date, поиск по дате работает")


if __name__ == "__main__":
    print(f"системная TZ: {os.environ.get('TZ', '(не задана)')}")
    test_parse_appointment_id_survives_non_numeric()
    test_slots_respect_lead_buffer()
    test_slots_stay_on_work_start_grid()
    test_sqlite_migration_adds_missing_columns()
    asyncio.run(test_get_or_create_user_and_holiday_date())
    print("\nвсе проверки пройдены")
