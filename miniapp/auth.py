import hashlib
import hmac
import logging
import time
from typing import Optional
from urllib.parse import parse_qsl

from fastapi import HTTPException, Header
from config import load_config

logger = logging.getLogger(__name__)
config = load_config()

# Telegram не обновляет initData в течение сессии WebApp, поэтому TTL берём с запасом.
INIT_DATA_TTL_SECONDS = 24 * 3600

def verify_telegram_web_app_data(init_data: str) -> dict:
    """
    Проверяет подпись данных от Telegram WebApp Init Data.

    Args:
        init_data (str): Строка с данными инициализации от Telegram WebApp.

    Returns:
        dict: Распарсенные данные пользователя.

    Raises:
        HTTPException: Если подпись недействительна.
    """
    try:
        parsed_data = dict(parse_qsl(init_data))

        if 'hash' not in parsed_data:
            raise HTTPException(status_code=403, detail="Hash not found")

        received_hash = parsed_data.pop('hash')

        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

        secret_key = hmac.new(
            key=b"WebAppData",
            msg=config.tg_bot.token.encode(),
            digestmod=hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            raise HTTPException(status_code=403, detail="Invalid hash")

        # Подпись сама по себе бессрочна: без этой проверки перехваченный
        # initData оставался бы валидным навсегда.
        auth_date = int(parsed_data.get('auth_date', 0))
        if time.time() - auth_date > INIT_DATA_TTL_SECONDS:
            raise HTTPException(status_code=403, detail="Init data expired")

        return parsed_data
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Не удалось проверить initData: {e}")
        raise HTTPException(status_code=403, detail="Verification failed")

async def verify_admin(authorization: Optional[str] = Header(None)) -> dict:
    """
    Проверяет, является ли пользователь администратором.

    Args:
        authorization (Optional[str]): Заголовок Authorization с init_data.

    Returns:
        dict: Данные авторизованного администратора.

    Raises:
        HTTPException: Если пользователь не авторизован или не является админом.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    init_data = authorization[4:]
    user_data = verify_telegram_web_app_data(init_data)

    if 'user' not in user_data:
        raise HTTPException(status_code=403, detail="User data not found")

    import json
    user_info = json.loads(user_data['user'])
    user_id = user_info.get('id')

    if user_id != config.tg_bot.admin_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return user_info
