# ============================================================
# services/fuel.py — NSW FuelCheck 实时油价服务
# ============================================================
# Step 1: GET /oauth/client_credential/accesstoken?grant_type=client_credentials
#         Header: Authorization: Basic base64(key:secret)
# Step 2: GET /FuelPriceCheck/v1/fuel/prices
#         Headers: Authorization: Bearer <token>
#                  apikey: <key>
#                  transactionid: <uuid>
#                  requesttimestamp: DD/MM/YYYY HH:MM:SS
# ============================================================

import math
import time
import uuid
import base64
from datetime import datetime
from typing import Optional
import requests
import streamlit as st

_BASE      = "https://api.onegov.nsw.gov.au"
_TOKEN_URL = f"{_BASE}/oauth/client_credential/accesstoken"
_PRICES_URL = f"{_BASE}/FuelPriceCheck/v1/fuel/prices"

_token_cache: dict = {}
_prices_cache: dict = {}
_last_error: str = ""

_FUEL_PRIORITY = ["P95", "P98", "E10", "U91", "PDL", "DL", "B20", "LPG"]
_EXCLUDE_FUEL  = {"EV", "H2"}  # 跳过电动/氢燃料


def _get_credentials() -> Optional[tuple]:
    global _last_error
    try:
        fc = st.secrets.get("fuelcheck", {})
        key    = fc.get("consumer_key", "")
        secret = fc.get("consumer_secret", "")
        if key and secret:
            _last_error = ""
            return key, secret
        _last_error = "FuelCheck credentials are not configured"
    except Exception as exc:
        _last_error = f"Unable to read FuelCheck credentials: {exc}"
    return None


def _fetch_token(key: str, secret: str) -> Optional[str]:
    global _last_error
    now = time.time()
    if _token_cache.get("token") and now < _token_cache.get("expires_at", 0):
        return _token_cache["token"]

    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    try:
        r = requests.get(
            _TOKEN_URL,
            params={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth}"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            if not token:
                _last_error = "FuelCheck token response did not include access_token"
                return None
            expires_in = int(data.get("expires_in", 43199))
            _token_cache["token"] = token
            _token_cache["expires_at"] = now + expires_in - 60
            _last_error = ""
            return token
        _last_error = f"FuelCheck token request failed with HTTP {r.status_code}"
    except Exception as exc:
        _last_error = f"FuelCheck token request failed: {exc}"
    return None


def _fetch_all_prices(key: str, token: str) -> tuple[list, dict]:
    """返回 (stations_list, prices_by_code)，缓存30分钟。"""
    global _last_error
    now = time.time()
    if _prices_cache.get("data") and now < _prices_cache.get("expires_at", 0):
        return _prices_cache["data"]

    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": key,
        "Content-Type": "application/json; charset=utf-8",
        "transactionid": str(uuid.uuid4()),
        "requesttimestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    try:
        r = requests.get(_PRICES_URL, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            stations = data.get("stations", [])
            prices = data.get("prices", [])

            # 建立 stationcode → station 映射
            station_map = {s["code"]: s for s in stations}
            # 建立 stationcode → {fueltype: price} 映射
            price_map: dict = {}
            for p in prices:
                code = p.get("stationcode", "")
                ft   = p.get("fueltype", "")
                pr   = p.get("price", 0)
                if code not in price_map:
                    price_map[code] = {}
                price_map[code][ft] = pr

            result = (station_map, price_map)
            _prices_cache["data"] = result
            _prices_cache["expires_at"] = now + 1800
            _last_error = ""
            return result
        _last_error = f"FuelCheck price request failed with HTTP {r.status_code}"
    except Exception as exc:
        _last_error = f"FuelCheck price request failed: {exc}"
    return {}, {}


def get_last_fuel_error() -> str:
    return _last_error


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def get_nearby_fuel(lat: float, lon: float, radius_km: float = 5.0) -> list:
    """
    返回钓点附近最近的3个加油站（含最优油价）。
    每项：{"brand": str, "name": str, "address": str,
           "dist_km": float, "fuel_type": str, "price": float}
    API 不可用时返回空列表。
    """
    creds = _get_credentials()
    if not creds:
        return []

    key, secret = creds
    token = _fetch_token(key, secret)
    if not token:
        return []

    station_map, price_map = _fetch_all_prices(key, token)
    if not station_map:
        return []

    nearby = []
    for code, station in station_map.items():
        loc = station.get("location", {})
        slat = loc.get("latitude", 0)
        slon = loc.get("longitude", 0)
        if not slat or not slon:
            continue
        dist = _haversine_km(lat, lon, slat, slon)
        if dist > radius_km:
            continue

        # 选优先级最高的燃油（排除 EV/H2，要求价格 > 0）
        fuels = price_map.get(code, {})
        best_ft = best_pr = None
        for ft in _FUEL_PRIORITY:
            if ft in fuels and fuels[ft] > 0:
                best_ft = ft
                best_pr = fuels[ft]
                break
        if best_ft is None:
            for ft, pr in fuels.items():
                if ft not in _EXCLUDE_FUEL and pr > 0:
                    best_ft = ft
                    best_pr = pr
                    break
        if best_ft is None:
            continue  # 纯 EV 站跳过

        nearby.append({
            "brand":    station.get("brand", ""),
            "name":     station.get("name", ""),
            "address":  station.get("address", ""),
            "dist_km":  round(dist, 1),
            "fuel_type": best_ft or "—",
            "price":    best_pr or 0,
        })

    nearby.sort(key=lambda x: x["dist_km"])
    return nearby[:3]
