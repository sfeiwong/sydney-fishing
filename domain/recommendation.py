import re
from datetime import date, datetime
from typing import Optional

from config import (
    OCEAN_SWELL_DANGER,
    OCEAN_WIND_DANGER,
    SHELTERED_SWELL_WARN,
    SHELTERED_WIND_WARN,
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _risk_ratio(spot: dict, day_weather: dict) -> float:
    wt = spot.get("water_type", "harbour")
    wind = day_weather.get("wind") or 0.0

    if wt == "freshwater":
        return wind / SHELTERED_WIND_WARN if SHELTERED_WIND_WARN else 0.0

    swell = day_weather.get("swell_height") or 0.0
    exposed = wt == "ocean" or (wt == "boat" and not spot.get("sheltered"))
    if exposed:
        return max(
            swell / OCEAN_SWELL_DANGER if OCEAN_SWELL_DANGER else 0.0,
            wind / OCEAN_WIND_DANGER if OCEAN_WIND_DANGER else 0.0,
        )
    return max(
        swell / SHELTERED_SWELL_WARN if SHELTERED_SWELL_WARN else 0.0,
        wind / SHELTERED_WIND_WARN if SHELTERED_WIND_WARN else 0.0,
    )


def _best_window_bonus(best_window: str, tides: list[dict]) -> float:
    text = best_window or ""
    score = 0.0

    if re.search(r"破晓|黎明|日出|清晨|黄昏|日落|夜间|夜晚", text):
        score += 4.0
    if re.search(r"\d{1,2}:\d{2}\s*[–\-~至到]\s*\d{1,2}:\d{2}", text):
        score += 2.0

    wants_high = "满潮" in text or "涨潮" in text or "高潮" in text
    wants_low = "干潮" in text or "落潮" in text or "低潮" in text
    if wants_high and any(t.get("is_high") for t in tides):
        score += 3.0
    if wants_low and any(not t.get("is_high") for t in tides):
        score += 3.0

    return min(score, 7.0)


def editorial_reputation_score(spot: dict) -> float:
    """Estimate long-term spot reputation from curated local notes."""
    tips = " ".join((spot.get("method_tips") or {}).values())
    active_fish = spot.get("active_fish") or ""
    text = f"{tips} {active_fish} {spot.get('best_window', '')}"

    score = 0.0
    score += min(6.0, text.count("🎯") * 2.0)
    score += min(3.0, text.count("👍") * 0.8)

    strong_terms = (
        "顶级推荐",
        "最佳",
        "核心",
        "圣地",
        "高产",
        "稳定",
        "密度高",
        "频繁",
        "常年",
        "出产",
        "纪录",
        "不稀奇",
    )
    score += min(6.0, sum(1 for term in strong_terms if term in text) * 1.0)

    caution_terms = ("极其危险", "强烈不建议", "谨慎", "易挂底", "停车难")
    score -= min(4.0, sum(1 for term in caution_terms if term in text) * 1.0)
    return round(_clamp(score, -4.0, 12.0), 2)


def log_reputation_score(entries: list[dict], today: Optional[date] = None) -> float:
    """Score first-party angler feedback from catch logs without inventing ratings."""
    if not entries:
        return 0.0

    today = today or datetime.now().date()
    score = min(7.0, len(entries) * 1.4)

    authors = {e.get("author") for e in entries if e.get("author")}
    score += min(3.0, len(authors) * 0.8)

    fish_mentions = sum(len(e.get("fish_caught") or []) for e in entries)
    score += min(5.0, fish_mentions * 0.7)

    photo_entries = sum(1 for e in entries if e.get("photos"))
    score += min(3.0, photo_entries * 0.9)

    note_entries = sum(1 for e in entries if len(e.get("notes") or "") >= 20)
    score += min(2.0, note_entries * 0.5)

    recent_count = 0
    for entry in entries:
        try:
            fish_date = datetime.fromisoformat(str(entry.get("fish_date"))).date()
        except ValueError:
            continue
        if 0 <= (today - fish_date).days <= 90:
            recent_count += 1
    score += min(4.0, recent_count * 1.0)

    return round(_clamp(score, 0.0, 18.0), 2)


def recommendation_score(
    spot: dict,
    safety: dict,
    day_weather: dict,
    tides: list[dict],
    selected_methods: tuple[str, ...] = (),
    selected_fish: tuple[str, ...] = (),
    reputation_score: float = 0.0,
) -> float:
    """Return a continuous rank score while preserving safety as the hard gate."""
    color_base = {"sage": 100.0, "amber": 55.0, "coral": -100.0}
    score = color_base.get(safety.get("color"), 0.0)

    risk = _risk_ratio(spot, day_weather)
    score += 22.0 * (1.0 - _clamp(risk, 0.0, 1.0))
    if risk > 1.0:
        score -= min(25.0, (risk - 1.0) * 35.0)

    rain_prob = day_weather.get("rain_prob") or 0.0
    uv = day_weather.get("uv") or 0.0
    score -= _clamp(rain_prob / 10.0, 0.0, 10.0)
    score -= _clamp((uv - 6.0) * 0.8, 0.0, 5.0)

    wt = spot.get("water_type", "harbour")
    if spot.get("sheltered") or wt in {"harbour", "brackish", "freshwater"}:
        score += 3.0 if risk >= 0.75 else 1.0

    family_stars = (spot.get("family_friendly") or "").count("⭐")
    score += min(6.0, family_stars * 1.2)

    spot_methods = set(spot.get("supported_methods") or [])
    spot_fish = set(spot.get("fish_tags") or [])
    if selected_methods:
        score += 4.0 * len(spot_methods.intersection(selected_methods))
    else:
        score += min(4.0, len(spot_methods) * 0.4)
    if selected_fish:
        score += 3.0 * len(spot_fish.intersection(selected_fish))

    score += _best_window_bonus(spot.get("best_window", ""), tides)
    score += editorial_reputation_score(spot)
    score += _clamp(reputation_score, 0.0, 18.0)

    return round(score, 2)
