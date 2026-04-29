from __future__ import annotations

import json
import os
from datetime import datetime

import httpx

_BASE = "https://api.openweathermap.org/data/2.5"


class WeatherTool:
    def __init__(self) -> None:
        self._api_key = os.environ["OPENWEATHER_API_KEY"]

    def get_weather(self, city: str, country_code: str = "IN") -> str:
        params = {
            "q": f"{city},{country_code}",
            "appid": self._api_key,
            "units": "metric",
        }
        with httpx.Client(timeout=10, verify=False) as client:
            current_resp = client.get(f"{_BASE}/weather", params=params)
            if not current_resp.is_success:
                raise ValueError(
                    f"OpenWeatherMap error {current_resp.status_code}: {current_resp.text}"
                )
            current_data = current_resp.json()

            forecast_resp = client.get(f"{_BASE}/forecast", params={**params, "cnt": 9})
            if not forecast_resp.is_success:
                raise ValueError(
                    f"OpenWeatherMap forecast error {forecast_resp.status_code}: {forecast_resp.text}"
                )
            forecast_data = forecast_resp.json()

        current = {
            "city": current_data["name"],
            "timestamp": datetime.utcnow().isoformat(),
            "temp_c": current_data["main"]["temp"],
            "feels_like_c": current_data["main"]["feels_like"],
            "humidity_pct": current_data["main"]["humidity"],
            "wind_kph": round(current_data["wind"]["speed"] * 3.6, 1),
            "condition": current_data["weather"][0]["description"],
            "visibility_km": current_data.get("visibility", 10000) / 1000,
        }

        days: dict[str, list[float]] = {}
        for item in forecast_data["list"]:
            day = item["dt_txt"][:10]
            days.setdefault(day, []).append(item["main"]["temp"])

        forecast = [
            {
                "date": d,
                "avg_c": round(sum(t) / len(t), 1),
                "min_c": round(min(t), 1),
                "max_c": round(max(t), 1),
            }
            for d, t in list(days.items())[:3]
        ]

        temp = current["temp_c"]
        if temp > 38:
            advisory = "Extreme heat — carry water, avoid outdoor activity between 11 AM and 4 PM."
        elif temp > 32:
            advisory = "Hot — wear light clothing, sunscreen, and start sightseeing early."
        elif temp > 18:
            advisory = "Comfortable weather — great for sightseeing throughout the day."
        else:
            advisory = "Cool — carry a light jacket, especially in the evenings."

        return json.dumps(
            {"current": current, "forecast": forecast, "advisory": advisory},
            indent=2,
        )
