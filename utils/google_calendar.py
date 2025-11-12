import urllib.parse
from datetime import datetime

def generate_google_calendar_link(
    event_name: str,
    start_time: datetime,
    end_time: datetime,
    description: str = "Запись на услугу",
    location: str = "Адрес мастера"
) -> str:
    """
    Генерирует ссылку для добавления события в Google Calendar.

    Args:
        event_name (str): Название события (услуги).
        start_time (datetime): Время начала события (UTC).
        end_time (datetime): Время окончания события (UTC).
        description (str, optional): Описание события. По умолчанию "Запись на услугу".
        location (str, optional): Место проведения. По умолчанию "Адрес мастера".

    Returns:
        str: URL-ссылка для добавления события в Google Calendar.
    """
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    
    params = {
        "text": event_name,
        "dates": f"{start_time.strftime('%Y%m%dT%H%M%SZ')}/{end_time.strftime('%Y%m%dT%H%M%SZ')}",
        "details": description,
        "location": location,
        "crm": "AVAILABLE"
    }
    
    return f"{base_url}&{urllib.parse.urlencode(params)}"