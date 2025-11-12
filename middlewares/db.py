from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для передачи асинхронной сессии базы данных в обработчики.
    """
    def __init__(self, session_pool: Callable[[], AsyncSession]):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """
        Выполняет передачу сессии базы данных в обработчик.

        Args:
            handler (Callable): Обработчик события.
            event (Message | CallbackQuery): Объект события (сообщение или callback-запрос).
            data (Dict[str, Any]): Словарь с данными события.

        Returns:
            Any: Результат выполнения обработчика.
        """
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)
