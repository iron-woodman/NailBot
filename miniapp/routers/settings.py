import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Settings
from database.session import get_async_session
from miniapp.auth import verify_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsResponse(BaseModel):
    id: int
    admin_id: int
    planning_horizon_days: int
    timezone: str

    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    planning_horizon_days: int | None = None
    timezone: str | None = None

@router.get("/", response_model=SettingsResponse)
async def get_settings(
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Получить текущие настройки приложения.
    """
    settings = await session.get(Settings, 1)

    if not settings:
        raise HTTPException(status_code=404, detail="Настройки не найдены")

    return settings

@router.put("/", response_model=SettingsResponse)
async def update_settings(
    settings_data: SettingsUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Обновить настройки приложения.
    """
    settings = await session.get(Settings, 1)

    if not settings:
        raise HTTPException(status_code=404, detail="Настройки не найдены")

    if settings_data.planning_horizon_days is not None:
        if settings_data.planning_horizon_days < 1 or settings_data.planning_horizon_days > 365:
            raise HTTPException(status_code=400, detail="Горизонт планирования должен быть от 1 до 365 дней")
        settings.planning_horizon_days = settings_data.planning_horizon_days

    if settings_data.timezone is not None:
        import pytz
        if settings_data.timezone not in pytz.all_timezones:
            raise HTTPException(status_code=400, detail="Недопустимый часовой пояс")
        settings.timezone = settings_data.timezone

    await session.commit()
    await session.refresh(settings)

    logger.info(f"Обновлены настройки приложения")
    return settings
