# ============================================================
# services/weather.py — 天气与海况数据服务
# ============================================================

import streamlit as st
import requests
from datetime import datetime, timedelta
from config import WEATHER_CACHE_TTL


def _round_coord(val: float, precision: float = 0.5) -> float:
    return round(val / precision) * precision


@st.cache_data(ttl=WEATHER_CACHE_TTL, show_spinner=False)
def _fetch_forecast(lat: float, lon: float) -> dict:
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,"
            f"wind_speed_10m_max,wind_direction_10m_dominant,"
            f"precipitation_sum,precipitation_probability_max"
            f"&timezone=Australia%2FSydney"
        )
        marine_url = (
            f"https://marine-api.open-meteo.com/v1/marine"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=wave_height_max,swell_wave_height_max,"
            f"swell_wave_direction_dominant,swell_wave_period_max"
            f"&timezone=Australia%2FSydney"
        )
        w = requests.get(weather_url, timeout=10).json()
        m = requests.get(marine_url, timeout=10).json()

        marine_daily = m.get("daily", {})
        if not any(v for v in (marine_daily.get("swell_wave_height_max") or [])):
            fallback_url = (
                "https://marine-api.open-meteo.com/v1/marine"
                "?latitude=-33.9&longitude=151.3"
                "&daily=wave_height_max,swell_wave_height_max,"
                "swell_wave_direction_dominant,swell_wave_period_max"
                "&timezone=Australia%2FSydney"
            )
            m = requests.get(fallback_url, timeout=10).json()
            marine_daily = m.get("daily", {})

        wd = w["daily"]
        days = []
        for i in range(3):
            days.append({
                "date":           wd["time"][i],
                "temp":           wd["temperature_2m_max"][i],
                "temp_min":       wd["temperature_2m_min"][i],
                "wind":           wd["wind_speed_10m_max"][i],
                "wind_direction": (wd.get("wind_direction_10m_dominant") or [None]*3)[i],
                "rain_prob":      (wd.get("precipitation_probability_max") or [0]*3)[i] or 0,
                "precipitation":  (wd.get("precipitation_sum") or [0]*3)[i] or 0,
                "wave":           (marine_daily.get("wave_height_max") or [None]*3)[i],
                "swell_height":   (marine_daily.get("swell_wave_height_max") or [None]*3)[i],
                "swell_direction":(marine_daily.get("swell_wave_direction_dominant") or [None]*3)[i],
                "swell_period":   (marine_daily.get("swell_wave_period_max") or [None]*3)[i],
            })
        return {"success": True, "days": days}

    except Exception as exc:
        today = datetime.now()
        fallback = [
            {
                "date":           (today + timedelta(days=i)).strftime("%Y-%m-%d"),
                "temp":           21.0,
                "temp_min":       15.0,
                "wind":           12.0,
                "wind_direction":  180,
                "rain_prob":       10,
                "precipitation":    0.0,
                "wave":            1.1,
                "swell_height":    0.9,
                "swell_direction": 140,
                "swell_period":    8.5,
            }
            for i in range(3)
        ]
        return {"success": False, "days": fallback, "error": str(exc)}


def get_marine_forecast(lat: float, lon: float) -> dict:
    return _fetch_forecast(_round_coord(lat), _round_coord(lon))
