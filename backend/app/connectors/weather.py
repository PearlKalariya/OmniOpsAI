"""OpenWeatherMap connector (current conditions)."""

from app.connectors.base import get
from app.core.config import settings

API = "https://api.openweathermap.org/data/2.5/weather"


def is_configured() -> bool:
    return bool(settings.openweather_api_key)


def current(city: str) -> dict:
    data = get(
        API,
        params={"q": city, "appid": settings.openweather_api_key, "units": "metric"},
    )
    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "description": data["weather"][0]["description"],
        "temp_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity_pct": data["main"]["humidity"],
        "wind_ms": data["wind"]["speed"],
    }
