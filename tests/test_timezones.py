"""
Проверка работы с часовыми поясами: время в БД хранится в UTC, а показывать
и считать пересечения слотов нужно в часовом поясе мастера.

Запуск: TZ=Europe/Moscow python3 tests/test_timezones.py
Тесты намеренно гоняются при TZ != UTC — именно так проявлялся баг, когда
naive datetime из SQLite трактовался как локальное время сервера.
"""
import asyncio
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytz
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.session import Base
from database.models import User, Service, Appointment, WorkSchedule
from utils.time_utils import format_in_timezone, get_available_time_slots

MSK = "Europe/Moscow"


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def test_roundtrip_stays_utc_aware():
    """Запись на 10:00 МСК должна читаться из БД как 07:00 UTC с tzinfo."""
    S = await _session()
    async with S() as s:
        user = User(telegram_id=1, full_name="Клиент")
        service = Service(name="Маникюр", duration_minutes=60, price=1500.0)
        s.add_all([user, service])
        await s.commit()

        start_msk = pytz.timezone(MSK).localize(datetime.datetime(2026, 10, 12, 10, 0))
        s.add(Appointment(
            user_id=user.id, service_id=service.id,
            start_time=start_msk.astimezone(pytz.utc),
            end_time=(start_msk + datetime.timedelta(hours=1)).astimezone(pytz.utc),
            status="confirmed",
        ))
        await s.commit()

    async with S() as s:
        from sqlalchemy import select
        appt = (await s.execute(select(Appointment))).scalar_one()

        assert appt.start_time.tzinfo is not None, "из БД пришёл naive datetime"
        assert appt.start_time.utcoffset() == datetime.timedelta(0), appt.start_time
        assert appt.start_time.hour == 7, f"ожидали 07:00 UTC, получили {appt.start_time}"

        shown = format_in_timezone(appt.start_time, MSK, "%d.%m.%Y %H:%M")
        assert shown == "12.10.2026 10:00", f"клиенту показывается {shown}, а не 10:00"
    print("[OK] 10:00 МСК -> 07:00 UTC в БД -> 10:00 МСК в сообщении")


def test_slots_exclude_booked_interval():
    """Занятый слот 10:00-11:00 МСК не должен предлагаться повторно."""
    schedule = WorkSchedule(weekday=0, start_time=datetime.time(9, 0),
                            end_time=datetime.time(18, 0), is_working=True)
    date = datetime.date(2026, 10, 12)
    start_msk = pytz.timezone(MSK).localize(datetime.datetime.combine(date, datetime.time(10, 0)))
    booked = Appointment(
        start_time=start_msk.astimezone(pytz.utc),
        end_time=(start_msk + datetime.timedelta(hours=1)).astimezone(pytz.utc),
        status="confirmed",
    )

    slots = get_available_time_slots(schedule, [booked], 60, date, MSK)

    assert datetime.time(9, 0) in slots, "свободный слот 09:00 пропал"
    for taken in (datetime.time(9, 30), datetime.time(10, 0), datetime.time(10, 30)):
        assert taken not in slots, f"слот {taken} пересекается с записью 10:00-11:00, но предложен"
    assert datetime.time(11, 0) in slots, "слот 11:00 сразу после записи должен быть свободен"
    print("[OK] пересечения слотов считаются в МСК, а не в UTC")


if __name__ == "__main__":
    print(f"системная TZ: {os.environ.get('TZ', '(не задана)')}")
    asyncio.run(test_roundtrip_stays_utc_aware())
    test_slots_exclude_booked_interval()
    print("\nвсе проверки пройдены")
