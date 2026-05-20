# ============================================================
# data/loader.py — 钓点数据加载器
# ============================================================

import json
import os

from config import ALL_FISH, ALL_METHODS

_DATA_PATH = os.path.join(os.path.dirname(__file__), "spots.json")
_REQUIRED_FIELDS = {
    "name",
    "region",
    "type",
    "lat",
    "lon",
    "water_type",
    "tide_delay",
    "fish_tags",
    "best_window",
    "family_friendly",
    "supported_methods",
    "method_tips",
    "route",
    "parking",
}
_WATER_TYPES = {"ocean", "harbour", "brackish", "freshwater", "boat"}
_COORD_PAIRS = (
    ("fishing_lat", "fishing_lon"),
    ("map_lat", "map_lon"),
    ("nav_lat", "nav_lon"),
    ("weather_lat", "weather_lon"),
)


def validate_spots(spots: list[dict]) -> list[str]:
    """Return human-readable validation errors for the spot database."""
    errors = []
    fish_values = set(ALL_FISH)
    method_values = set(ALL_METHODS)

    for idx, spot in enumerate(spots):
        label = spot.get("name", f"spot #{idx + 1}")
        missing = sorted(_REQUIRED_FIELDS - set(spot))
        if missing:
            errors.append(f"{label}: missing fields {', '.join(missing)}")
            continue

        if spot.get("water_type") not in _WATER_TYPES:
            errors.append(f"{label}: invalid water_type {spot.get('water_type')!r}")

        if not isinstance(spot.get("lat"), (int, float)) or not isinstance(spot.get("lon"), (int, float)):
            errors.append(f"{label}: lat/lon must be numeric")

        for lat_key, lon_key in _COORD_PAIRS:
            has_lat = lat_key in spot
            has_lon = lon_key in spot
            if has_lat != has_lon:
                errors.append(f"{label}: {lat_key} and {lon_key} must be provided together")
            elif has_lat and (
                not isinstance(spot.get(lat_key), (int, float))
                or not isinstance(spot.get(lon_key), (int, float))
            ):
                errors.append(f"{label}: {lat_key}/{lon_key} must be numeric")

        unknown_fish = [fish for fish in spot.get("fish_tags", []) if fish not in fish_values]
        if unknown_fish:
            errors.append(f"{label}: unknown fish tags {', '.join(unknown_fish)}")

        unknown_methods = [
            method for method in spot.get("supported_methods", [])
            if method not in method_values
        ]
        if unknown_methods:
            errors.append(f"{label}: unknown methods {', '.join(unknown_methods)}")

        missing_tips = [
            method for method in spot.get("supported_methods", [])
            if method not in spot.get("method_tips", {})
        ]
        if missing_tips:
            errors.append(f"{label}: missing method_tips for {', '.join(missing_tips)}")

    return errors


def load_spots() -> list[dict]:
    """从 spots.json 加载所有钓点数据，返回 list[dict]。"""
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        spots = json.load(f)

    errors = validate_spots(spots)
    if errors:
        raise ValueError("Invalid spot database:\n" + "\n".join(errors))
    return spots
