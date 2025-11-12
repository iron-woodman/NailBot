import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from miniapp.routers import services, appointments, schedule, settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nails Appointment MiniApp API",
    description="API для административной панели управления записями.",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services.router)
app.include_router(appointments.router)
app.include_router(schedule.router)
app.include_router(settings.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик исключений.
    """
    logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Главная страница административной панели.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
async def api_info():
    """
    Информация об API.
    """
    return {
        "message": "Welcome to the MiniApp API!",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """
    Эндпоинт для проверки здоровья API.
    """
    return {"status": "healthy"}

logger.info("FastAPI приложение инициализировано.")
