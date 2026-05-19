# ============================================================
# services/fuel.py — NSW FuelCheck 实时油价服务
# ============================================================
# OAuth 2.0 client_credentials flow:
#   POST /api/oauth2/token  (Basic base64(key:secret))  → access_token
#   GET  /api/fuelpricecheck/v2/fuel/prices/all  (Bearer token)
# 凭证存放在 .streamlit/secrets.toml:
#   [fuelcheck]
#   consumer_key    = "..."
#   consumer_secret = "..."
# ============================================================

import math
import time
import base64
from typing import Optional
import requests
import streamlit as st

_BASE      = "https://api.onegov.nsw.gov.au"
_TOKEN_URL = f"{_BASE}/api/oauth2/token"
_PRICES_V2 = f"{_BASE}/api/fuelpricecheck/v2/fuel/prices/all"

# 模块级 token 缓存（每次 Streamlit 启动重置；token 有效期 ~12h）
_token_cache: dict = {}


def _get_credentials() -> Optional[tuple]:
    """从 st.secrets 读取凭证，不存在则返回 None。"""
    try:
        fc = st.secrets.get("fuelcheck", {})
        key    = fc.get("consumer_key", "")
        secret = fc.get("consumer_secret", "")
        if key and secret:
            return key, secret
    except Exception:
        pass
    return None


def _fetch_token(key: str, secret: str) -> Optional[str]:
    """用 Basic Auth 换取 Bearer access_token，失败返回 None。"""
    now = time.time()
    cached = _token_cache.get("token")
    if cached and now < _token_cache.get("expires_at", 0):
        return cached

    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    try:
        r = requests.post(
            _TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth}",
            },
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            expires_in = int(data.get("expires_in", 43200))
            _token_cache["token"] = token
            _token_cache["expires_at"] = now + expires_in - 60
            return token
    except Exception:
        pass
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_all_prices_cached(token: str) -> list[dict]:
    """获取全NSW油价列表，以 token 为缓存键（30分钟）。"""
    try:
        r = requests.get(
            _PRICES_V2,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("prices", [])
    except Exception:
        pass
    return []


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# 常用燃油类型优先级（钓鱼爱好者常用 95/98）
_FUEL_PRIORITY = ["P95", "P98", "E10", "U91"]


def get_nearby_fuel(lat: float, lon: float, radius_km: float = 5.0) -> list[dict]:
    """
    返回钓点附近最近的 3 个加油站（含油价）。
    每项格式：
        {"name": str, "brand": str, "address": str,
         "dist_km": float, "fuel_type": str, "price_cents": int}
    API 不可用时返回空列表。
    """
    creds = _get_credentials()
    if not creds:
        return []

    key, secret = creds
    token = _fetch_token(key, secret)
    if not token:
        return []

    prices = _fetch_all_prices_cached(token)
    if not prices:
        return []

    nearby: list[dict] = []
    for p in prices:
        try:
            slat = float(p.get("lat", 0) or 0)
            slon = float(p.get("lng", 0) or 0)
            if slat == 0 and slon == 0:
                continue
            dist = _haversine_km(lat, lon, slat, slon)
            if dist > radius_km:
                continue
            nearby.append({
                "name":         p.get("stationname", ""),
                "brand":        p.get("brand", ""),
                "address":      p.get("address", ""),
                "dist_km":      round(dist, 1),
                "fuel_type":    p.get("fueltype", ""),
                "price_cents":  int(p.get("price", 0) or 0),
            })
        except Exception:
            continue

    # 每个加油站只保留优先级最高的燃油
    by_station: dict[str, dict] = {}
    for item in nearby:
        key_s = (item["name"], item["address"])
        existing = by_station.get(key_s)
        if existing is None:
            by_station[key_s] = item
        else:
            # 优先级更高或价格相同时替换
            cur_pri = next((i for i, f in enumerate(_FUEL_PRIORITY) if f == existing["fuel_type"]), 99)
            new_pri = next((i for i, f in enumerate(_FUEL_PRIORITY) if f == item["fuel_type"]), 99)
            if new_pri < cur_pri:
                by_station[key_s] = item

    result = sorted(by_station.values(), key=lambda x: x["dist_km"])[:3]
    return result
