# ============================================================
# services/weather.py — 天气与海况数据服务
# ============================================================
# 改进点：
#   1. 按钓点坐标获取对应区域天气（坐标精度 0.5° ≈ 55km）
#   2. 精度不同的区域数据独立缓存，不再全部用 CBD 一个点
#   3. 网络失败时明确标记 success=False，UI 层可显示警告

import streamlit as st
import requests
from datetime import datetime, timedelta
from config import WEATHER_CACHE_TTL


def _round_coord(val: float, precision: float = 0.5) -> float:
    """将坐标四舍五入到最近的格点，用作缓存键。"""
    return round(val / precision) * precision


@st.cache_data(ttl=WEATHER_CACHE_TTL, show_spinner=False)
def _fetch_forecast(lat: float, lon: float) -> dict:
    """
    从 Open-Meteo 获取指定坐标的 3 天天气 + 海况预报。
    参数为已取整的格点坐标，由缓存机制保证相同区域只调用一次。
    """
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,wind_speed_10m_max"
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

        # 若格点落在陆地，marine API 返回全 None；改用悉尼近海参考点补充
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

        days = []
        for i in range(3):
            days.append({
                "date":           w["daily"]["time"][i],
                "temp":           w["daily"]["temperature_2m_max"][i],
                "wind":           w["daily"]["wind_speed_10m_max"][i],
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
                "date":            (today + timedelta(days=i)).strftime("%Y-%m-%d"),
                "temp":           21.0,
                "wind":           12.0,
                "wave":            1.1,
                "swell_height":    0.9,
                "swell_direction":140,
                "swell_period":    8.5,
            }
            for i in range(3)
        ]
        return {"success": False, "days": fallback, "error": str(exc)}


def get_marine_forecast(lat: float, lon: float) -> dict:
    """
    对外接口：传入钓点坐标，返回 3 天预报。
    内部自动对坐标取整，相同区域共用缓存，减少 API 调用次数。
    """
    return _fetch_forecast(_round_coord(lat), _round_coord(lon))
