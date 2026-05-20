from config import (
    OCEAN_SWELL_DANGER,
    OCEAN_WIND_DANGER,
    SHELTERED_SWELL_WARN,
    SHELTERED_WIND_WARN,
)


def assess_safety(spot: dict, day_weather: dict) -> dict:
    wt = spot.get("water_type", "harbour")
    sheltered = bool(spot.get("sheltered"))
    wind = day_weather.get("wind") or 0.0

    if wt == "freshwater":
        if wind > SHELTERED_WIND_WARN:
            return {
                "status": "⚠️ 谨慎前往",
                "score": "⭐⭐⭐",
                "safe": True,
                "color": "amber",
                "advice": (
                    f"风速偏大（{wind}km/h），建议在河岸树林背风处作钓，"
                    "浮漂容易飘偏，适当加重线组。"
                ),
            }
        return {
            "status": "✅ 极力推荐",
            "score": "⭐⭐⭐⭐⭐",
            "safe": True,
            "color": "sage",
            "advice": "淡水河湖天气良好，非常适合出击，祝大鱼大获！🎉",
        }

    swell = day_weather.get("swell_height") or 0.0

    is_exposed_ocean = wt == "ocean" or (wt == "boat" and not sheltered)

    if is_exposed_ocean:
        if swell > OCEAN_SWELL_DANGER or wind > OCEAN_WIND_DANGER:
            return {
                "status": "❌ 极度危险",
                "score": "⭐",
                "safe": False,
                "color": "coral",
                "advice": (
                    f"外海浪涌预计 {swell}m，风速 {wind}km/h，"
                    "该点属于高暴露海域，极其危险！请转移到内湾避风钓点。"
                ),
            }
    else:
        if swell > SHELTERED_SWELL_WARN or wind > SHELTERED_WIND_WARN:
            if wt == "brackish":
                advice_detail = "咸淡水区域受地形保护，但风浪仍偏大，抛投受影响，建议选背风岸边作钓。"
            elif wt == "boat":
                advice_detail = "该船钓点位于内湾避风水域，但风浪仍偏大，建议贴岸慢漂并降低船速。"
            else:
                advice_detail = "内湾虽可避浪，但顶风抛投体感较差，建议选背风位或大桥底部作钓。"
            return {
                "status": "⚠️ 谨慎前往",
                "score": "⭐⭐⭐",
                "safe": True,
                "color": "amber",
                "advice": f"风速偏大（{wind}km/h），{advice_detail}",
            }

    return {
        "status": "✅ 极力推荐",
        "score": "⭐⭐⭐⭐⭐",
        "safe": True,
        "color": "sage",
        "advice": "此日海况温和，非常适合出击，祝大鲫大鲈！🎉",
    }
