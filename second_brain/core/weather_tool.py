"""Optional stretch — Weather Tool (OpenWeatherMap, free tier)."""
import requests
from core.config import OPENWEATHER_API_KEY


def get_weather(city: str) -> str:
    if not OPENWEATHER_API_KEY:
        return "Weather tool not configured (missing OPENWEATHER_API_KEY)."
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if r.status_code != 200:
            return f"Could not fetch weather for {city}: {data.get('message', 'unknown error')}"
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{city}: {desc}, {temp}°C"
    except Exception as e:
        return f"Weather lookup failed: {e}"
