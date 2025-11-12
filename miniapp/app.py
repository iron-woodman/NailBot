import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание экземпляра FastAPI
app = FastAPI(
    title="Nails Appointment MiniApp API",
    description="API для административной панели управления записями.",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретный домен MiniApp
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """
    Корневой эндпоинт для проверки работоспособности API.
    """
    return {"message": "Welcome to the MiniApp API!"}

# TODO: Добавить middleware для авторизации
# TODO: Добавить эндпоинты для управления услугами, расписанием, записями

logger.info("FastAPI приложение инициализировано.")

# Для локального запуска можно использовать:
# uvicorn miniapp.app:app --reload
