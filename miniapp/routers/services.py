import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Service
from database.session import get_async_session
from miniapp.auth import verify_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/services", tags=["services"])

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    price: float
    description: str = ""
    active: bool = True

class ServiceUpdate(BaseModel):
    name: str | None = None
    duration_minutes: int | None = None
    price: float | None = None
    description: str | None = None
    active: bool | None = None

class ServiceResponse(BaseModel):
    id: int
    name: str
    duration_minutes: int
    price: float
    description: str | None
    active: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ServiceResponse])
async def get_services(
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Получить список всех услуг.
    """
    result = await session.execute(select(Service).order_by(Service.name))
    services = result.scalars().all()
    return services

@router.post("/", response_model=ServiceResponse)
async def create_service(
    service_data: ServiceCreate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Создать новую услугу.
    """
    result = await session.execute(select(Service).where(Service.name == service_data.name))
    existing_service = result.scalar_one_or_none()

    if existing_service:
        raise HTTPException(status_code=400, detail="Услуга с таким названием уже существует")

    new_service = Service(
        name=service_data.name,
        duration_minutes=service_data.duration_minutes,
        price=service_data.price,
        description=service_data.description,
        active=service_data.active
    )

    session.add(new_service)
    await session.commit()
    await session.refresh(new_service)

    logger.info(f"Создана новая услуга: {new_service.name}")
    return new_service

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Обновить существующую услугу.
    """
    service = await session.get(Service, service_id)

    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    if service_data.name is not None:
        result = await session.execute(
            select(Service).where(Service.name == service_data.name, Service.id != service_id)
        )
        existing_service = result.scalar_one_or_none()
        if existing_service:
            raise HTTPException(status_code=400, detail="Услуга с таким названием уже существует")
        service.name = service_data.name

    if service_data.duration_minutes is not None:
        service.duration_minutes = service_data.duration_minutes

    if service_data.price is not None:
        service.price = service_data.price

    if service_data.description is not None:
        service.description = service_data.description

    if service_data.active is not None:
        service.active = service_data.active

    await session.commit()
    await session.refresh(service)

    logger.info(f"Обновлена услуга: {service.name}")
    return service

@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(verify_admin)
):
    """
    Удалить услугу (мягкое удаление - деактивация).
    """
    service = await session.get(Service, service_id)

    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    service.active = False
    await session.commit()

    logger.info(f"Деактивирована услуга: {service.name}")
    return {"status": "success", "message": "Услуга деактивирована"}
