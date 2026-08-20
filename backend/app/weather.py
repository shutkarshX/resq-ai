"""Small Open-Meteo adapter for the commander dashboard."""
import threading
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL_SECONDS = 300
REQUEST_TIMEOUT_SECONDS = 3.0

_cache: dict[tuple[float, float], tuple[float, dict]] = {}
_cache_lock = threading.Lock()


def _condition_for_code(code: Optional[int]) -> str:
    if code is None:
        return "Current conditions"
    if code == 0:
        return "Clear conditions"
    if code in {1, 2, 3}:
        return "Cloudy conditions"
    if code in {45, 48}:
        return "Foggy conditions"
    if code in {51, 53, 55, 56, 57}:
        return "Drizzle"
    if code in {61, 63, 65, 66, 67, 80, 81, 82}:
        return "Rain"
    if code in {95, 96, 99}:
        return "Thunderstorm risk"
    return "Current conditions"


def _trend_from_hourly(values: list[float]) -> Optional[str]:
    if len(values) < 2:
        return None
    previous, latest = values[-2:]
    if latest > previous:
        return "Increasing"
    if latest < previous:
        return "Decreasing"
    return "Stable"


def get_weather(latitude: float, longitude: float) -> Optional[dict]:
    """Return cached Open-Meteo data, or None when the provider is unavailable."""
    key = (round(latitude, 4), round(longitude, 4))
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "precipitation,weather_code",
        "hourly": "precipitation",
        "past_hours": 2,
        "forecast_hours": 1,
        "timezone": "auto",
    }
    try:
        response = httpx.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current") or {}
        hourly = payload.get("hourly") or {}
        current_precipitation = current.get("precipitation")
        weather_code = current.get("weather_code")
        if current_precipitation is None or weather_code is None:
            return None
        hourly_values = [value for value in (hourly.get("precipitation") or []) if isinstance(value, (int, float))]
        result = {
            "current_precipitation": float(current_precipitation),
            "condition": _condition_for_code(int(weather_code)),
            "trend": _trend_from_hourly(hourly_values),
            "updated_at": current.get("time") or datetime.now(timezone.utc).isoformat(),
            "source": "Open-Meteo",
        }
        with _cache_lock:
            _cache[key] = (now, result)
        return result
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return None
