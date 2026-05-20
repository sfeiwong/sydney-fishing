# ============================================================
# services/tides.py — 潮汐服务（WorldTides + 本地估算回退）
# ============================================================

from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
import streamlit as st

from config import (
    LUNAR_DRIFT_PER_DAY,
    SEMI_DIURNAL_MINUTES,
    TIDE_REF_DAY,
    TIDE_REF_HOUR,
    TIDE_REF_MINUTE,
    TIDE_REF_MONTH,
    TIDE_REF_YEAR,
)

_REFERENCE_HIGH = datetime(
    TIDE_REF_YEAR, TIDE_REF_MONTH, TIDE_REF_DAY, TIDE_REF_HOUR, TIDE_REF_MINUTE
)

_WORLDTIDES_URL = "https://www.worldtides.info/api/v3"
_SYD_TZ = timezone(timedelta(hours=10))


def _estimate_tides_for_date(target_date: datetime, delay_minutes: int = 0) -> list[dict]:
    """天文近似算法：4 个潮汐事件（2 满潮 + 2 干潮）。"""
    days_since_ref = (target_date.date() - _REFERENCE_HIGH.date()).days
    total_drift = timedelta(minutes=days_since_ref * LUNAR_DRIFT_PER_DAY + delay_minutes)

    base = _REFERENCE_HIGH + total_drift
    base = base.replace(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
    )

    tides = []
    for i in range(4):
        t = base + timedelta(minutes=i * SEMI_DIURNAL_MINUTES)
        is_high = i % 2 == 0
        tides.append(
            {
                "time": t,
                "is_high": is_high,
                "label": "🟢 满潮" if is_high else "🔵 干潮",
            }
        )
    return tides


def _worldtides_key() -> str:
    try:
        return str(st.secrets.get("worldtides_api_key", "")).strip()
    except Exception:
        return ""


def _to_epoch_seconds(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_SYD_TZ)
    return int(dt.timestamp())


def _from_epoch_seconds(ts: int) -> datetime:
    return datetime.fromtimestamp(int(ts), tz=_SYD_TZ).replace(tzinfo=None)


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_worldtides_extremes(lat: float, lon: float, date_key: str) -> list[dict]:
    """仅请求 extremes，省额度。date_key 用于缓存分片。"""
    key = _worldtides_key()
    if not key:
        return []

    target = datetime.strptime(date_key, "%Y-%m-%d")
    start = datetime(target.year, target.month, target.day, tzinfo=_SYD_TZ) - timedelta(hours=12)
    end = start + timedelta(days=2)

    params = {
        "key": key,
        "lat": f"{lat:.6f}",
        "lon": f"{lon:.6f}",
        "start": _to_epoch_seconds(start),
        "end": _to_epoch_seconds(end),
        "extremes": "",
        "localtime": "true",
    }

    response = requests.get(_WORLDTIDES_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data.get("error"))

    parsed = []
    for item in data.get("extremes", []):
        dt = _from_epoch_seconds(item.get("dt"))
        typ = str(item.get("type", "")).lower()
        is_high = typ == "high"
        parsed.append(
            {
                "time": dt,
                "is_high": is_high,
                "label": "🟢 满潮" if is_high else "🔵 干潮",
            }
        )

    parsed.sort(key=lambda x: x["time"])
    return parsed


def _pick_four_events_for_date(all_events: list[dict], target_date: datetime) -> list[dict]:
    events = [e for e in all_events if e["time"].date() == target_date.date()]
    if len(events) >= 4:
        return events[:4]
    return events


def get_tides_for_date(
    target_date: datetime,
    delay_minutes: int = 0,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> list[dict]:
    """
    返回某天潮汐事件。优先 WorldTides，失败后回退到本地估算。

    参数：
        target_date    目标日期
        delay_minutes  仅在估算回退时生效（相对参考点偏移）
        lat/lon        可选，提供时才会尝试 WorldTides
    """
    if lat is not None and lon is not None and _worldtides_key():
        try:
            all_events = _fetch_worldtides_extremes(float(lat), float(lon), target_date.strftime("%Y-%m-%d"))
            picked = _pick_four_events_for_date(all_events, target_date)
            if len(picked) >= 2:
                return picked
        except Exception:
            pass

    return _estimate_tides_for_date(target_date, delay_minutes=delay_minutes)


def get_tide_accuracy_hint() -> str:
    """Return a short UX hint about current tide data confidence."""
    if _worldtides_key():
        return "潮汐精度：WorldTides 实时极值（通常约 ±5 分钟）"
    return "潮汐精度：天文估算（通常约 ±30–60 分钟）"
