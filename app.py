# ============================================================
# app.py — 悉尼钓鱼助手 Pro+ 主程序
# ============================================================

import math
import re
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

import folium
from streamlit_folium import st_folium

from config import (
    ALL_METHODS, ALL_FISH,
    OCEAN_SWELL_DANGER, OCEAN_WIND_DANGER,
    SHELTERED_SWELL_WARN, SHELTERED_WIND_WARN,
    REGION_FILTER_MAP, FISH_LEGAL_SIZE,
)
from services.weather import get_marine_forecast
from services.tides import get_tides_for_date
from services.fuel import get_nearby_fuel
from data.loader import load_spots

st.set_page_config(
    page_title="悉尼钓鱼助手 Pro+",
    page_icon="🎣",
    layout="wide",
)

spots = load_spots()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;500;600&family=Noto+Serif+SC:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root {
  --bg:#f1f4f7; --surface:#ffffff; --surface2:#f7f9fb;
  --line:rgba(15,30,50,0.09); --line-strong:rgba(15,30,50,0.18);
  --text:#0f2240; --muted:#5b6e87; --subtle:#8a9cb2;
  --text-on-dark:#eaf1f8; --muted-on-dark:rgba(234,241,248,0.65);
  --primary:#2a5fb0; --primary-dk:#1f4a8d;
  --gold:#c69230; --coral:#cc5e54; --amber:#d99540; --sage:#4f9b76;
  --serif-zh:'Noto Serif SC','Songti SC',serif;
  --serif-en:'Source Serif 4',Georgia,serif;
  --ui-zh:'Noto Sans SC','PingFang SC',sans-serif;
  --ui:'Inter',-apple-system,sans-serif;
  --mono:'IBM Plex Mono',monospace;
}
.stApp { background:var(--bg); }
body,.stApp * { font-family:var(--ui-zh),var(--ui); color:var(--text); }
header[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.2rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:var(--serif-zh)!important; font-weight:600!important; color:var(--text); }
h2 { font-size:22px!important; }

/* Sidebar */
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0e253f 0%,#163a60 100%); }
section[data-testid="stSidebar"] * { color:var(--text-on-dark); }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label {
  color:var(--text-on-dark)!important; font-size:12px!important; font-weight:500;
}
section[data-testid="stSidebar"] [data-baseweb="select"]>div,
section[data-testid="stSidebar"] [data-baseweb="input"]>div {
  background:rgba(255,255,255,0.06)!important; border:1px solid rgba(255,255,255,0.12)!important;
  border-radius:8px!important; color:var(--text-on-dark)!important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] input { color:var(--text-on-dark)!important; }
section[data-testid="stSidebar"] [data-baseweb="tag"] { background:rgba(198,146,48,0.25)!important; color:var(--gold)!important; border-radius:999px!important; }
section[data-testid="stSidebar"] [data-testid="stCheckbox"] label { font-size:13px!important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--line); background:transparent; padding:0; border-radius:0; box-shadow:none; }
.stTabs [data-baseweb="tab"] { background:transparent!important; border:none!important; border-bottom:2px solid transparent!important; border-radius:0!important; padding:12px 20px!important; color:var(--muted)!important; font-size:15px!important; }
.stTabs [aria-selected="true"] { border-bottom:2px solid var(--primary)!important; color:var(--text)!important; font-weight:600!important; background:transparent!important; }

/* Buttons */
.stButton>button { border-radius:8px; border:1px solid var(--line-strong); background:var(--surface); color:var(--text); font-size:13px; padding:7px 14px; transition:all 120ms ease; }
.stButton>button:hover { background:var(--surface2); border-color:var(--muted); }

/* Metrics */
[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:14px 16px; box-shadow:0 2px 6px rgba(15,30,50,0.025); }
[data-testid="stMetricLabel"] { font-size:12.5px!important; font-weight:500; }
[data-testid="stMetricValue"] { font-family:var(--serif-en)!important; font-size:30px!important; font-weight:400!important; letter-spacing:-0.5px; line-height:1!important; }
[data-testid="stMetricDelta"] { font-family:var(--mono)!important; font-size:12px!important; }
.metric-sage [data-testid="stMetricValue"] { color:var(--sage)!important; }
.metric-coral [data-testid="stMetricValue"] { color:var(--coral)!important; }
.metric-amber [data-testid="stMetricValue"] { color:var(--amber)!important; }
.metric-blue [data-testid="stMetricValue"] { color:var(--primary)!important; }

/* Containers */
div[data-testid="stVerticalBlockBorderWrapper"] { background:var(--surface); border:1px solid var(--line)!important; border-radius:14px!important; box-shadow:0 2px 6px rgba(15,30,50,0.025); }

/* Info/alert */
[data-testid="stAlert"] { border-radius:12px!important; border:none!important; }

/* 展开详情 toggle button — pill chip */
.main .stButton button[kind="secondary"] {
    background:var(--surface2)!important;
    border:1px solid var(--line)!important;
    border-radius:999px!important;
    box-shadow:none!important;
    color:var(--muted)!important;
    font-size:11.5px!important;
    padding:3px 14px!important;
    min-height:auto!important;
    height:auto!important;
    line-height:1.5!important;
    transition:all 100ms ease!important;
}
.main .stButton button[kind="secondary"]:hover {
    background:var(--line)!important;
    border-color:var(--muted)!important;
    color:var(--text)!important;
}

/* hr */
hr { border:none; border-top:1px solid var(--line); margin:1.2rem 0; }
</style>
""", unsafe_allow_html=True)


# ── 侧边栏 ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="display:flex;gap:12px;align-items:center;padding:20px 0 16px">'
        '<div style="width:42px;height:42px;border-radius:10px;background:rgba(255,255,255,0.08);'
        'border:1px solid rgba(255,255,255,0.12);display:flex;align-items:center;'
        'justify-content:center;font-size:22px">🎣</div>'
        '<div><div style="font-family:var(--serif-zh);font-size:18px;font-weight:600;'
        'color:var(--text-on-dark)">悉尼钓鱼助手</div>'
        '<div style="margin-top:4px">'
        '<span style="font-family:var(--mono);font-size:10px;letter-spacing:1.5px;'
        'color:var(--gold);background:rgba(198,146,48,0.18);padding:2px 7px;border-radius:4px">'
        'PRO+</span> '
        '<span style="font-size:11px;color:var(--muted-on-dark)">v3.0</span>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:11px;font-family:var(--mono);letter-spacing:2px;'
        'color:var(--gold);opacity:0.8;margin-bottom:8px">智能筛选</div>',
        unsafe_allow_html=True,
    )
    selected_methods = st.multiselect("钓法", ALL_METHODS, key="sel_methods", placeholder="选择钓法 · Method")
    selected_fish    = st.multiselect("目标鱼种", ALL_FISH, key="sel_fish", placeholder="选择鱼种 · Species")
    selected_region  = st.selectbox(
        "地理区域",
        ["全部 · All Sydney"] + list(REGION_FILTER_MAP.keys()),
    )
    water_type       = st.selectbox("水域类型", ["全部 · All", "🌊 外海 Ocean", "⚓ 内湾 Harbour", "🔀 咸淡水 Brackish", "🏞️ 淡水 Freshwater"])
    safe_only        = st.checkbox("隐藏危险钓点 ⚠", value=False)
    family_only      = st.checkbox("仅看家庭友好 👨‍👩‍👧 (⭐⭐⭐⭐+)", value=False)

    if st.button("↺ 重置所有筛选", use_container_width=True):
        st.session_state["sel_methods"] = []
        st.session_state["sel_fish"] = []
        st.rerun()

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="border:1px solid rgba(255,255,255,0.1);border-radius:10px;'
        'padding:10px 12px;font-size:11.5px;color:var(--muted-on-dark);line-height:1.7">'
        '🎫 <b style="color:var(--text-on-dark)">NSW 钓鱼执照</b><br>'
        '16 岁以上须持有免费<br>休闲钓鱼凭证（RFL）<br>'
        '<a href="https://www.dpi.nsw.gov.au/fishing/recreational/fishing-rules-and-regulations/recreational-fishing-fee" '
        'target="_blank" style="color:var(--gold)">立即免费登记 →</a>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:11px;font-family:var(--mono);letter-spacing:2px;'
        'color:rgba(234,241,248,0.5);margin-bottom:10px">DATA SOURCES</div>'
        '<div style="font-size:12px;line-height:1.8;color:var(--muted-on-dark)">'
        '🛰 <b style="color:var(--text-on-dark)">天气</b> · Open-Meteo'
        '<span style="opacity:0.6;font-size:11px"> (缓存 1 小时)</span><br>'
        '🌊 <b style="color:var(--text-on-dark)">海况</b> · 坐标分区'
        '<span style="opacity:0.6;font-size:11px"> (动态获取)</span><br>'
        '⏱ <b style="color:var(--text-on-dark)">潮汐</b> · 天文推算'
        '<span style="opacity:0.6;font-size:11px"> (±30–60 min)</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="border:1px dashed rgba(198,146,48,0.35);border-radius:10px;'
        'padding:12px 14px;font-size:12px;color:var(--muted-on-dark)">'
        '升级潮汐精度 →<br>'
        '<a href="https://www.worldtides.info/api" target="_blank" '
        'style="color:var(--gold);text-decoration:none">WorldTides API ↗</a>'
        '<span style="font-size:11px;opacity:0.6"> (±5 分钟)</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-family:var(--mono);font-size:10px;color:rgba(234,241,248,0.3);'
        'margin-top:20px;text-align:center">© 2026 · Built with Streamlit</div>',
        unsafe_allow_html=True,
    )


# ── 工具函数 ──────────────────────────────────────────────────────────────

def section_head(kicker: str, title: str, accent: str = "") -> None:
    st.markdown(
        f'<div style="margin:4px 0 14px">'
        f'<div style="font-family:var(--mono);font-size:11px;color:var(--subtle);'
        f'letter-spacing:2px;text-transform:uppercase;margin-bottom:4px">{kicker}</div>'
        f'<div style="display:flex;align-items:baseline;gap:10px">'
        f'<h2 style="margin:0;font-family:var(--serif-zh);font-weight:600;font-size:22px;color:var(--text)">{title}</h2>'
        f'<span style="font-size:13px;color:var(--muted)">{accent}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _pill(text: str, tone: str = "blue", sm: bool = True) -> str:
    size_css = "padding:2px 9px;font-size:11.5px" if sm else "padding:4px 11px;font-size:12.5px"
    colors = {
        "blue":   ("background:#e6efff", "color:#2a5fb0"),
        "gold":   ("background:#fbf3e1", "color:#a37618"),
        "coral":  ("background:#fbeae8", "color:#b1453b"),
        "amber":  ("background:#fcf2e0", "color:#a06c20"),
        "sage":   ("background:#e7f3ec", "color:#3a7f5d"),
        "violet": ("background:#efeaff", "color:#6e4ebe"),
    }
    bg, fg = colors.get(tone, colors["blue"])
    return (f'<span style="{bg};{fg};{size_css};border-radius:999px;'
            f'font-weight:500;margin:2px;display:inline-flex;align-items:center;gap:4px">'
            f'{text}</span>')


def _deg_to_swell_dir(deg) -> str:
    try:
        d = float(deg) % 360
    except (TypeError, ValueError):
        return "—"
    dirs = ["北浪", "东北浪", "东浪", "东南浪", "南浪", "西南浪", "西浪", "西北浪"]
    return dirs[int((d + 22.5) / 45) % 8]


def _deg_to_wind_dir(deg) -> str:
    try:
        d = float(deg) % 360
    except (TypeError, ValueError):
        return "—"
    dirs = ["北风", "东北风", "东风", "东南风", "南风", "西南风", "西风", "西北风"]
    return dirs[int((d + 22.5) / 45) % 8]


def _beaufort(kmh: float) -> str:
    if kmh < 1:   return "0级·无风"
    if kmh < 6:   return "1级·软风"
    if kmh < 12:  return "2级·轻风"
    if kmh < 20:  return "3级·微风"
    if kmh < 29:  return "4级·和风"
    if kmh < 39:  return "5级·劲风"
    if kmh < 50:  return "6级·强风"
    if kmh < 62:  return "7级·疾风"
    if kmh < 75:  return "8级·大风"
    return "9+级·烈风"

def _parse_tag(tag: str) -> tuple:
    m = re.match(r'^(.+?)\s*[(\（](.+?)[)\）]$', tag.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return tag, ""


_WT_LABEL = {"ocean": "🌊 外海", "harbour": "⚓ 内湾", "brackish": "🔀 咸淡水", "freshwater": "🏞️ 淡水"}
_WT_PILL  = {"ocean": "blue", "harbour": "blue", "brackish": "violet", "freshwater": "sage"}
_WT_EMOJI = {"ocean": "🌊", "harbour": "⚓", "brackish": "🔀", "freshwater": "🏞️"}


def _wt_pill(spot: dict, sm: bool = True) -> str:
    wt = spot.get("water_type", "harbour")
    return _pill(_WT_LABEL.get(wt, wt), _WT_PILL.get(wt, "blue"), sm=sm)


def _freshwater_season_pill() -> str:
    month = datetime.now().month
    if 4 <= month <= 10:
        return _pill("🎯 旺季", "sage")
    return _pill("☀️ 淡季", "amber")


# 咸水鱼种旺季（月份列表）
_FISH_PEAK_MONTHS = {
    "Kingfish (黄尾师)":   [10, 11, 12, 1, 2, 3],   # 夏季回游
    "Tailor (蓝鱼)":       [3, 4, 5, 6, 7, 8, 9],    # 秋冬
    "Salmon (三文鱼)":     [3, 4, 5, 6, 7, 8],        # 秋冬
    "Drummer (黑毛)":      [4, 5, 6, 7, 8, 9, 10],    # 凉季
    "Jewfish (皇冠鲊)":    [10, 11, 12, 1, 2],        # 夏季
    "Squid (鱿鱼)":        [3, 4, 5, 6, 7, 8, 9, 10], # 秋冬春
    "Australian Bass (澳洲鲈鱼)": [4, 5, 6, 7, 8, 9, 10],
    "Golden Perch (黄金鲈)": [4, 5, 6, 7, 8, 9],
}

def _saltwater_season_pills(fish_tags: list) -> str:
    month = datetime.now().month
    in_season = [t for t in fish_tags if month in _FISH_PEAK_MONTHS.get(t, [])]
    if not in_season:
        return ""
    en_names = [_parse_tag(t)[0] for t in in_season[:2]]
    label = "·".join(en_names) + " 旺季"
    return _pill(f"🎯 {label}", "sage")


def _moon_phase(target_date: datetime) -> tuple:
    """Return (emoji, name_zh, fishing_tip) for the moon phase on target_date."""
    # Synodic period ≈ 29.53 days; reference new moon: 2000-01-06
    ref = datetime(2000, 1, 6)
    days = (target_date.replace(tzinfo=None) - ref).days % 29.53
    if days < 1.85:
        return "🌑", "新月", "潮差最大·鱼类进食最活跃"
    elif days < 7.38:
        return "🌒", "上弦前", "潮汐渐强·适合出击"
    elif days < 9.22:
        return "🌓", "上弦月", "潮汐适中"
    elif days < 14.77:
        return "🌔", "渐盈凸月", "潮汐渐强"
    elif days < 16.61:
        return "🌕", "满月", "潮差最大·夜钓黄金期"
    elif days < 22.15:
        return "🌖", "渐亏凸月", "潮汐渐弱"
    elif days < 23.99:
        return "🌗", "下弦月", "潮汐适中"
    else:
        return "🌘", "残月", "潮汐偏弱·选内湾佳"


def _legal_sizes_html(fish_tags: list) -> str:
    rows = []
    for tag in fish_tags:
        info = FISH_LEGAL_SIZE.get(tag, {})
        size = info.get("size")
        bag  = info.get("bag")
        note = info.get("note", "")
        _, cn = _parse_tag(tag)
        label = cn or tag

        if "禁捕" in note or "保护" in note:
            size_str = '<span style="color:#cc5e54;font-weight:700">⚠️ 禁捕</span>'
        elif "有害" in note:
            size_str = '<span style="color:#d99540;font-weight:700">须就地处理</span>'
        elif size:
            size_str = f'<span style="color:#2a5fb0;font-weight:700">≥ {size} cm</span>'
        else:
            size_str = '<span style="color:#8a9cb2">无限制</span>'

        bag_str = ""
        if bag is not None and bag > 0:
            bag_str = f' <span style="color:#8a9cb2;font-size:10px">袋限 {bag} 条</span>'
        elif bag == 0:
            bag_str = ""

        rows.append(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:4px 0;border-bottom:1px solid var(--line)">'
            f'<span style="font-size:11.5px;color:var(--text)">{label}</span>'
            f'<span style="font-size:11.5px">{size_str}{bag_str}</span>'
            f'</div>'
        )
    return "".join(rows)


def spot_matches(spot: dict) -> bool:
    if selected_methods and not any(m in spot["supported_methods"] for m in selected_methods):
        return False
    if selected_fish and not any(f in spot["fish_tags"] for f in selected_fish):
        return False
    if selected_region and selected_region != "全部 · All Sydney":
        keywords = REGION_FILTER_MAP.get(selected_region, [selected_region])
        if not any(kw in spot["region"] for kw in keywords):
            return False
    wt_map = {
        "🌊 外海 Ocean":       "ocean",
        "⚓ 内湾 Harbour":     "harbour",
        "🔀 咸淡水 Brackish":  "brackish",
        "🏞️ 淡水 Freshwater": "freshwater",
    }
    if water_type in wt_map and spot.get("water_type") != wt_map[water_type]:
        return False
    if family_only:
        stars = spot["family_friendly"].count("⭐")
        if stars < 4:
            return False
    return True


def assess_safety(spot: dict, day_weather: dict) -> dict:
    wt   = spot.get("water_type", "harbour")
    wind = day_weather.get("wind") or 0.0

    if wt == "freshwater":
        if wind > SHELTERED_WIND_WARN:
            return {
                "status": "⚠️ 谨慎前往",
                "score":  "⭐⭐⭐",
                "safe":   True,
                "color":  "amber",
                "advice": (
                    f"风速偏大（{wind}km/h），建议在河岸树林背风处作钓，"
                    "浮漂容易飘偏，适当加重线组。"
                ),
            }
        return {
            "status": "✅ 极力推荐",
            "score":  "⭐⭐⭐⭐⭐",
            "safe":   True,
            "color":  "sage",
            "advice": "淡水河湖天气良好，非常适合出击，祝大鱼大获！🎉",
        }

    swell = day_weather.get("swell_height") or 0.0

    if wt == "ocean":
        if swell > OCEAN_SWELL_DANGER or wind > OCEAN_WIND_DANGER:
            return {
                "status": "❌ 极度危险",
                "score":  "⭐",
                "safe":   False,
                "color":  "coral",
                "advice": (
                    f"外海浪涌预计 {swell}m，风速 {wind}km/h，"
                    "该点属于完全暴露的外海地形，极其危险！请转移到内湾避风钓点。"
                ),
            }
    else:  # harbour or brackish
        if swell > SHELTERED_SWELL_WARN or wind > SHELTERED_WIND_WARN:
            advice_detail = (
                "咸淡水区域受地形保护，但风浪仍偏大，抛投受影响，建议选背风岸边作钓。"
                if wt == "brackish" else
                "内湾虽可避浪，但顶风抛投体感较差，建议选背风位或大桥底部作钓。"
            )
            return {
                "status": "⚠️ 谨慎前往",
                "score":  "⭐⭐⭐",
                "safe":   True,
                "color":  "amber",
                "advice": f"风速偏大（{wind}km/h），{advice_detail}",
            }

    return {
        "status": "✅ 极力推荐",
        "score":  "⭐⭐⭐⭐⭐",
        "safe":   True,
        "color":  "sage",
        "advice": "此日海况温和，非常适合出击，祝大鲫大鲈！🎉",
    }


def _val_color(value: float, warn: float, danger: float) -> str:
    if value >= danger: return "#cc5e54"
    if value >= warn:   return "#d99540"
    return "#4f9b76"


# ── 天气面板 ──────────────────────────────────────────────────────────────

def render_weather_panel(day_weather: dict, data_ok: bool, next_day: dict = None) -> None:
    if not data_ok:
        st.warning("⚠️ 天气数据加载失败，以下为估算值。")

    temp         = day_weather.get("temp") or 0
    temp_min     = day_weather.get("temp_min") or 0
    wind         = day_weather.get("wind") or 0
    swell        = day_weather.get("swell_height") or 0
    rain_prob    = day_weather.get("rain_prob") or 0
    precipitation= day_weather.get("precipitation") or 0
    swell_dir    = day_weather.get("swell_direction", "—")
    swell_period = day_weather.get("swell_period", "—")
    wind_dir     = day_weather.get("wind_direction", "—")

    swell_dir_text = _deg_to_swell_dir(swell_dir)
    wind_dir_text  = _deg_to_wind_dir(wind_dir)
    beaufort_text  = _beaufort(float(wind) if wind else 0)
    rain_str  = f"{precipitation:.1f} mm" if precipitation > 0 else "无降水"

    t_hi  = "#4f9b76"
    t_lo  = "#2a5fb0"
    r_col = "#cc5e54" if rain_prob >= 60 else ("#d99540" if rain_prob >= 25 else "#4f9b76")
    w_col = _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)
    s_col = _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)

    def _trend(cur, nxt, label="明天"):
        if nxt is None: return ""
        ratio = nxt / cur if cur > 0 else 1
        if ratio < 0.85:
            return f'<span style="font-size:11px;color:#4f9b76;font-weight:600">↓ {label}改善</span>'
        if ratio > 1.15:
            return f'<span style="font-size:11px;color:#cc5e54;font-weight:600">↑ {label}恶化</span>'
        return f'<span style="font-size:11px;color:#8a9cb2">→ {label}持平</span>'

    nd_wind  = (next_day.get("wind") or 0)  if next_day else None
    nd_swell = (next_day.get("swell_height") or 0) if next_day else None
    wind_trend  = _trend(wind,  nd_wind)
    swell_trend = _trend(swell, nd_swell)

    def _card(label, body_html):
        return (
            f'<div style="background:var(--surface);border:1px solid var(--line);'
            f'border-radius:14px;padding:18px 20px;box-shadow:0 2px 6px rgba(15,30,50,0.025);height:100%">'
            f'<div style="font-family:var(--mono);font-size:10.5px;color:var(--subtle);'
            f'letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px">{label}</div>'
            f'{body_html}'
            f'</div>'
        )

    row1_c1, row1_c2 = st.columns(2)
    row2_c1, row2_c2 = st.columns(2)

    row1_c1.markdown(_card("气温 · TEMPERATURE", f"""
        <div style="display:flex;gap:28px;align-items:baseline">
            <div>
                <div style="font-family:var(--serif-en);font-size:36px;font-weight:400;
                            color:{t_hi};line-height:1">{temp}°</div>
                <div style="font-size:11.5px;color:var(--muted);margin-top:4px">最高</div>
            </div>
            <div>
                <div style="font-family:var(--serif-en);font-size:36px;font-weight:400;
                            color:{t_lo};line-height:1">{temp_min}°</div>
                <div style="font-size:11.5px;color:var(--muted);margin-top:4px">最低</div>
            </div>
        </div>
    """), unsafe_allow_html=True)

    row1_c2.markdown(_card("降水 · PRECIPITATION", f"""
        <div style="display:flex;gap:28px;align-items:baseline">
            <div>
                <div style="font-family:var(--serif-en);font-size:36px;font-weight:400;
                            color:{r_col};line-height:1">{int(rain_prob)}%</div>
                <div style="font-size:11.5px;color:var(--muted);margin-top:4px">降雨概率</div>
            </div>
            <div>
                <div style="font-family:var(--serif-en);font-size:28px;font-weight:400;
                            color:var(--text);line-height:1">{rain_str}</div>
                <div style="font-size:11.5px;color:var(--muted);margin-top:4px">预计降水</div>
            </div>
        </div>
    """), unsafe_allow_html=True)

    row2_c1.markdown(_card("风 · WIND", f"""
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
            <div>
                <div style="font-family:var(--serif-en);font-size:36px;font-weight:400;
                            color:{w_col};line-height:1">{wind}</div>
                <div style="font-size:11.5px;color:var(--muted);margin-top:4px">风速 km/h</div>
            </div>
            <div style="text-align:right;padding-top:4px">{wind_trend}</div>
        </div>
        <div style="font-size:12.5px;color:var(--muted);line-height:1.8">
            <span style="color:var(--text);font-weight:500">{wind_dir_text}</span>
            <span style="opacity:0.35;margin:0 6px">·</span>
            <span style="color:var(--text);font-weight:500">{beaufort_text}</span>
        </div>
    """), unsafe_allow_html=True)

    row2_c2.markdown(_card("浪涌 · SWELL", f"""
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
            <div>
                <div style="font-family:var(--serif-en);font-size:36px;font-weight:400;
                            color:{s_col};line-height:1">{swell}</div>
                <div style="font-size:11.5px;color:var(--muted);margin-top:4px">浪高 m</div>
            </div>
            <div style="text-align:right;padding-top:4px">{swell_trend}</div>
        </div>
        <div style="font-size:12.5px;color:var(--muted);line-height:1.8">
            <span style="color:var(--text);font-weight:500">{swell_dir_text}</span>
            <span style="opacity:0.35;margin:0 6px">·</span>
            周期 <span style="color:var(--text);font-weight:500">{swell_period}s</span>
        </div>
    """), unsafe_allow_html=True)


# ── 最佳时段推算 ──────────────────────────────────────────────────────────

def _best_window_times(best_window: str, tides: list) -> str:
    text = best_window

    explicit = re.findall(r'\d{1,2}:\d{2}[–\-]\d{1,2}:\d{2}', text)
    if explicit:
        return explicit[0]

    sorted_tides = sorted(tides, key=lambda t: t["time"])

    hrs_match = re.search(r'(\d+(?:\.\d+)?)[\s]*小时', text)
    offset_h  = float(hrs_match.group(1)) if hrs_match else 1.5

    def fmt_window(center, before_h, after_h):
        start = center - timedelta(hours=before_h)
        end   = center + timedelta(hours=after_h)
        return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"

    if "满潮" in text or "涨潮" in text or "高潮" in text:
        highs = [t for t in sorted_tides if t["is_high"]]
        if highs:
            return fmt_window(highs[0]["time"], offset_h, offset_h)

    if "干潮" in text or "落潮" in text or "低潮" in text:
        lows = [t for t in sorted_tides if not t["is_high"]]
        if lows:
            return fmt_window(lows[0]["time"], offset_h, offset_h)

    if "破晓" in text or "黎明" in text or "日出" in text:
        return "05:30–08:00"
    if "黄昏" in text or "日落" in text:
        return "17:00–19:30"
    if "夜间" in text or "夜晚" in text:
        return "20:00–23:00"
    if "白天" in text or "正午" in text:
        return "09:00–16:00"

    return "—"


# ── 潮汐面板（Plotly） ────────────────────────────────────────────────────

def render_tide_panel(base_tides: list, chart_key: str = "tide", target_date: datetime = None) -> None:
    now          = datetime.now()
    sorted_tides = sorted(base_tides, key=lambda x: x["time"])
    is_today     = target_date is None or target_date.date() == now.date()
    HIGH_M, LOW_M = 1.85, 0.15

    ref_day  = target_date if target_date is not None else now
    midnight = ref_day.replace(hour=0, minute=0, second=0, microsecond=0)

    # Extend with adjacent days so interpolation works across the full 24h window
    prev_tides = get_tides_for_date(ref_day - timedelta(days=1))
    next_tides = get_tides_for_date(ref_day + timedelta(days=1))
    all_tides  = sorted(prev_tides + base_tides + next_tides, key=lambda x: x["time"])

    x_hours  = np.linspace(0, 24, 300)
    y_m      = []

    for xh in x_hours:
        t = midnight + timedelta(hours=float(xh))
        prev_td = next_td = None
        for td in all_tides:
            if td["time"] <= t:
                prev_td = td
            elif next_td is None:
                next_td = td
                break
        if prev_td is None:
            h = HIGH_M if all_tides[0]["is_high"] else LOW_M
        elif next_td is None:
            h = HIGH_M if all_tides[-1]["is_high"] else LOW_M
        else:
            ph = HIGH_M if prev_td["is_high"] else LOW_M
            nh = HIGH_M if next_td["is_high"] else LOW_M
            period  = (next_td["time"] - prev_td["time"]).total_seconds()
            elapsed = (t - prev_td["time"]).total_seconds()
            frac    = elapsed / period if period > 0 else 0
            h = ph + (nh - ph) * (1 - math.cos(math.pi * frac)) / 2
        y_m.append(h)

    now_h = now.hour + now.minute / 60

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_hours, y=y_m, mode="lines",
        line=dict(color="#2a5fb0", width=2),
        fill="tozeroy", fillcolor="rgba(42,95,176,0.18)",
        hovertemplate="%{x:.1f}h · %{y:.2f}m<extra></extra>",
    ))
    if is_today and 0 <= now_h <= 24:
        idx = int(now_h / 24 * (len(y_m) - 1))
        fig.add_vline(x=now_h, line=dict(color="#c69230", width=1.2, dash="dash"))
        fig.add_trace(go.Scatter(
            x=[now_h], y=[y_m[idx]], mode="markers",
            marker=dict(size=10, color="#c69230", line=dict(width=1.5, color="#fff")),
            hoverinfo="skip", showlegend=False,
        ))
    fig.update_layout(
        template="plotly_white", height=180,
        margin=dict(l=32, r=8, t=8, b=28), showlegend=False,
        xaxis=dict(
            range=[0, 24],
            tickvals=[0, 6, 12, 18, 24],
            ticktext=["00:00", "06:00", "12:00", "18:00", "24:00"],
            tickfont=dict(family="IBM Plex Mono", size=10, color="#8a9cb2"),
            gridcolor="rgba(15,30,50,0.06)",
        ),
        yaxis=dict(
            tickfont=dict(family="IBM Plex Mono", size=10, color="#8a9cb2"),
            gridcolor="rgba(15,30,50,0.06)",
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=chart_key)

    cols = st.columns(len(sorted_tides))
    for col, td in zip(cols, sorted_tides):
        is_high   = td["is_high"]
        dot_color = "#c69230" if is_high else "#8a9cb2"
        label     = "满潮" if is_high else "干潮"
        time_str  = td["time"].strftime("%H:%M")
        opacity   = "1" if (not is_today or td["time"] > now) else "0.4"
        col.markdown(
            f'<div style="text-align:center;opacity:{opacity}">'
            f'<div style="width:8px;height:8px;border-radius:50%;background:{dot_color};'
            f'margin:0 auto 3px"></div>'
            f'<div style="font-family:IBM Plex Mono;font-size:11px;color:{dot_color};font-weight:500">'
            f'{time_str}</div>'
            f'<div style="font-size:10.5px;color:#8a9cb2">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── 精选推荐英雄卡 ────────────────────────────────────────────────────────

def render_hero_card(col, spot: dict, safety: dict, day_weather: dict, tides: list = None) -> None:
    color_map = {"sage": "#4f9b76", "amber": "#d99540", "coral": "#cc5e54"}
    bg_map    = {"sage": "#e7f3ec", "amber": "#fcf2e0", "coral": "#fbeae8"}
    bar_map   = {"sage": "linear-gradient(180deg,#6bc995,#4f9b76)",
                 "amber": "linear-gradient(180deg,#f0b85a,#d99540)",
                 "coral": "linear-gradient(180deg,#e07a72,#cc5e54)"}

    border   = color_map.get(safety["color"], "#4f9b76")
    badge_bg = bg_map.get(safety["color"], "#e7f3ec")
    bar_grad = bar_map.get(safety["color"], bar_map["sage"])

    is_fw    = spot.get("water_type") == "freshwater"
    swell    = day_weather.get("swell_height") or 0
    wind     = day_weather.get("wind") or 0
    sw_color = "#8a9cb2" if is_fw else _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)
    wi_color = _val_color(wind, SHELTERED_WIND_WARN, OCEAN_WIND_DANGER)
    swell_val_html = "淡水" if is_fw else f"{swell}m"
    swell_label    = "水域" if is_fw else "涌浪"
    time_window = _best_window_times(spot["best_window"], tides) if tides else "—"

    fish_html   = "".join(_pill(f, "blue") for f in spot["fish_tags"][:4])
    method_html = "".join(_pill(m, "violet") for m in spot["supported_methods"][:3])
    wt_html     = _wt_pill(spot)
    season_html = _freshwater_season_pill() if is_fw else _saltwater_season_pills(spot["fish_tags"])

    # 三天预报 dots
    _dc = {"sage": "#4f9b76", "amber": "#d99540", "coral": "#cc5e54"}
    _fc = get_marine_forecast(spot["lat"], spot["lon"])
    _hero_dots = "".join(
        f'<div style="text-align:center;line-height:1.2">'
        f'<div style="font-size:9px;color:#aaa">{lb}</div>'
        f'<div style="width:8px;height:8px;border-radius:50%;'
        f'background:{_dc[assess_safety(spot,_fc["days"][di])["color"]]};margin:2px auto"></div>'
        f'</div>'
        for di, lb in enumerate(["今","明","后"])
    )
    hero_dots_html = (
        f'<div style="display:flex;gap:3px;align-items:center;'
        f'background:#f4f8fc;border-radius:7px;padding:3px 7px">{_hero_dots}</div>'
    )

    col.markdown(f"""
    <div style="background:white;border-radius:20px;padding:18px 20px 16px 24px;
                box-shadow:0 4px 24px rgba(24,66,112,0.10),0 1px 4px rgba(0,0,0,0.04);
                position:relative;overflow:hidden;min-height:230px;
                border:1px solid rgba(219,231,242,0.8)">
        <div style="position:absolute;left:0;top:0;bottom:0;width:5px;
                    background:{bar_grad};border-radius:20px 0 0 20px"></div>
        <div style="font-weight:800;font-size:1.0em;color:#102338;
                    line-height:1.35;margin-bottom:8px">{spot['name']}</div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px">
            <span style="background:{badge_bg};color:{border};padding:3px 12px;
                         border-radius:999px;font-size:0.78em;font-weight:700">
                {safety['status']}
            </span>
            {wt_html}{season_html}{hero_dots_html}
        </div>
        <div style="color:#60758a;font-size:0.78em;margin:4px 0 10px">
            📍 {spot['region']} &nbsp;·&nbsp; {spot['type']}
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:12px">
            <div style="background:#f7fafc;border-radius:12px;padding:8px 10px;border:1px solid #edf3f8">
                <div style="color:#8fa3b1;font-size:0.66em;margin-bottom:3px">{swell_label}</div>
                <div style="font-size:1.05em;font-weight:800;color:{sw_color}">{swell_val_html}</div>
            </div>
            <div style="background:#f7fafc;border-radius:12px;padding:8px 10px;border:1px solid #edf3f8">
                <div style="color:#8fa3b1;font-size:0.66em;margin-bottom:3px">风速</div>
                <div style="font-size:1.05em;font-weight:800;color:{wi_color}">{wind}km/h</div>
            </div>
            <div style="background:#f7fafc;border-radius:12px;padding:8px 10px;border:1px solid #edf3f8">
                <div style="color:#8fa3b1;font-size:0.66em;margin-bottom:3px">最佳时段</div>
                <div style="font-size:0.85em;font-weight:800;color:#1565c0">{time_window}</div>
            </div>
        </div>
        <div style="margin-bottom:6px">{fish_html}</div>
        <div>{method_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ── 钓点详情卡片 ──────────────────────────────────────────────────────────

def render_spot_card(spot: dict, safety: dict, spot_tides: list, spot_weather: dict, day_offset: int) -> None:
    color_map = {"sage": "#4f9b76", "amber": "#d99540", "coral": "#cc5e54"}
    bg_map    = {"sage": "#e7f3ec", "amber": "#fcf2e0", "coral": "#fbeae8"}
    bar_map   = {"sage": "linear-gradient(180deg,#6bc995,#4f9b76)",
                 "amber": "linear-gradient(180deg,#f0b85a,#d99540)",
                 "coral": "linear-gradient(180deg,#e07a72,#cc5e54)"}
    text_map  = {"sage": "#3a7f5d", "amber": "#a06c20", "coral": "#b1453b"}

    border    = color_map.get(safety["color"], "#4f9b76")
    badge_bg  = bg_map.get(safety["color"], "#e7f3ec")
    bar_grad  = bar_map.get(safety["color"], bar_map["sage"])
    badge_txt = text_map.get(safety["color"], "#3a7f5d")

    is_fw = spot.get("water_type") == "freshwater"
    swell = spot_weather.get("swell_height") or 0
    wind  = spot_weather.get("wind") or 0
    sw_color    = "#8a9cb2" if is_fw else _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)
    wi_color    = _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)
    swell_val_html  = "淡水" if is_fw else f"{swell}m"
    swell_label_str = "🏞️ 水域" if is_fw else "🌊 浪涌"
    time_window = _best_window_times(spot["best_window"], spot_tides)

    fish_chips   = "".join(_pill(f, "blue") for f in spot["fish_tags"])
    method_chips = "".join(_pill(m, "violet") for m in spot["supported_methods"][:5])
    wt_badge     = _wt_pill(spot)
    season_badge = _freshwater_season_pill() if is_fw else _saltwater_season_pills(spot["fish_tags"])

    # 三天安全预报小圆点
    _dot_c = {"sage": "#4f9b76", "amber": "#d99540", "coral": "#cc5e54"}
    _day_fc = get_marine_forecast(spot["lat"], spot["lon"])
    _day_labels = ["今", "明", "后"]
    _dots_parts = []
    for _di, _lbl in enumerate(_day_labels):
        _ds = assess_safety(spot, _day_fc["days"][_di])
        _c  = _dot_c[_ds["color"]]
        _dots_parts.append(
            f'<div style="text-align:center;line-height:1.2">'
            f'<div style="font-size:9px;color:#aaa">{_lbl}</div>'
            f'<div style="width:9px;height:9px;border-radius:50%;background:{_c};margin:1px auto"></div>'
            f'</div>'
        )
    three_day_dots = (
        '<div style="display:flex;gap:4px;align-items:center;'
        'background:#f4f8fc;border-radius:8px;padding:4px 7px">'
        + "".join(_dots_parts) + "</div>"
    )

    # Safety advice — only shown inline for amber/coral; sage is self-explanatory
    advice_html = ""
    if safety["color"] != "sage":
        advice_html = (
            f'<div style="background:{badge_bg};border-left:3px solid {border};'
            f'border-radius:0 8px 8px 0;padding:7px 12px;margin:10px 0 4px;'
            f'font-size:11.5px;color:{badge_txt};line-height:1.5">'
            f'{safety["advice"]}'
            f'</div>'
        )

    st.markdown(
        f'<div style="position:relative;background:white;border-radius:16px;'
        f'box-shadow:0 2px 14px rgba(24,66,112,0.07),0 1px 3px rgba(0,0,0,0.04);'
        f'border:1px solid rgba(219,231,242,0.85);'
        f'margin-bottom:4px;padding:16px 18px 14px 24px;overflow:hidden">'

        f'<div style="position:absolute;left:0;top:0;bottom:0;width:5px;'
        f'background:{bar_grad};border-radius:16px 0 0 16px"></div>'

        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap">'
        f'<div style="font-size:1.02em;font-weight:800;color:#102338">{spot["name"]}</div>'
        f'<span style="background:{badge_bg};color:{badge_txt};border:1px solid {border};'
        f'padding:2px 10px;border-radius:999px;font-size:0.76em;font-weight:700">'
        f'{safety["status"]}</span>'
        f'{wt_badge}{season_badge}'
        f'{three_day_dots}'
        f'<span style="color:#9ab0c0;font-size:0.78em">{spot["region"]} · {spot["type"]}</span>'
        f'</div>'

        f'<div style="display:flex;gap:10px;margin-bottom:10px;flex-wrap:wrap">'
        f'<div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:76px">'
        f'<div style="font-size:0.66em;color:#bbb;margin-bottom:2px">{swell_label_str}</div>'
        f'<div style="font-size:1.08em;font-weight:800;color:{sw_color}">{swell_val_html}</div>'
        f'</div>'
        f'<div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:76px">'
        f'<div style="font-size:0.66em;color:#bbb;margin-bottom:2px">💨 风速</div>'
        f'<div style="font-size:1.08em;font-weight:800;color:{wi_color}">{wind}km/h</div>'
        f'</div>'
        f'<div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:110px">'
        f'<div style="font-size:0.66em;color:#bbb;margin-bottom:2px">⏱️ 黄金时段</div>'
        f'<div style="font-size:0.98em;font-weight:800;color:#1565C0">{time_window}</div>'
        f'</div>'
        f'<div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:72px">'
        f'<div style="font-size:0.66em;color:#bbb;margin-bottom:2px">👨‍👩‍👧 家庭</div>'
        f'<div style="font-size:0.9em;font-weight:700;color:#555">{spot["family_friendly"][:2]}</div>'
        f'</div>'
        f'</div>'

        f'{advice_html}'

        f'<div style="margin-bottom:4px">{fish_chips}</div>'
        f'<div>{method_chips}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    toggle_key = (
        f"det_{day_offset}_"
        + spot["name"].replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
    )
    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = False
    is_open = st.session_state[toggle_key]

    if st.button("▴ 收起详情" if is_open else "▾ 展开详情", key=toggle_key + "_btn"):
        st.session_state[toggle_key] = not is_open
        st.rerun()

    if is_open:
        show_methods = (
            [m for m in selected_methods if m in spot["supported_methods"]]
            if selected_methods else spot["supported_methods"]
        )

        # ── Tide rows ────────────────────────────────────────
        wt = spot.get("water_type", "harbour")
        if wt == "freshwater":
            tide_rows = (
                '<div style="display:flex;flex-direction:column;justify-content:center;'
                'height:100%;text-align:center;padding:12px 0;gap:6px">'
                '<div style="font-size:20px">🏞️</div>'
                '<div style="font-size:11px;color:var(--muted);line-height:1.6">'
                '淡水钓点<br>无潮汐影响</div>'
                '</div>'
            )
        else:
            tide_rows = ""
            for td in spot_tides:
                dot = "#c69230" if td["is_high"] else "#8a9cb2"
                lbl = "满潮" if td["is_high"] else "干潮"
                tide_rows += (
                    f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;'
                    f'border-bottom:1px solid var(--line)">'
                    f'<div style="width:7px;height:7px;border-radius:50%;background:{dot};flex-shrink:0"></div>'
                    f'<span style="font-family:var(--mono);font-size:12px;color:{dot};font-weight:600">'
                    f'{td["time"].strftime("%H:%M")}</span>'
                    f'<span style="font-size:11.5px;color:var(--muted)">{lbl}</span>'
                    f'</div>'
                )
            if wt == "brackish":
                tide_rows += (
                    '<div style="margin-top:6px;font-size:10.5px;color:var(--amber);line-height:1.5">'
                    '⚠️ 咸淡水区域受上游来水影响，实际潮时可能偏晚，仅供参考'
                    '</div>'
                )

        # ── Legal sizes ──────────────────────────────────────
        legal_html = _legal_sizes_html(spot["fish_tags"])

        # ── Method rows ───────────────────────────────────────
        method_rows = ""
        tip_icons = {"🎯": "#2a5fb0", "👍": "#4f9b76", "⚠": "#d99540"}
        for method in show_methods:
            tip = spot["method_tips"].get(method, "此钓法在该钓点完全可行，建议现场根据流水微调线组铅重。")
            icon_color = next((c for k, c in tip_icons.items() if k in tip), "#8a9cb2")
            short_name = method.split("(")[0].strip()
            method_rows += (
                f'<div style="padding:8px 0;border-bottom:1px solid var(--line)">'
                f'<div style="font-size:12px;font-weight:700;color:{icon_color};margin-bottom:3px">'
                f'{short_name}</div>'
                f'<div style="font-size:12px;color:var(--muted);line-height:1.55">{tip}</div>'
                f'</div>'
            )

        st.markdown(
            f'<div style="background:var(--surface);border:1px solid var(--line);border-radius:14px;'
            f'border-top:3px solid {border};margin-top:4px;overflow:hidden">'

            f'<div style="display:grid;grid-template-columns:1fr 1.6fr;gap:0">'

            f'<div style="padding:14px 16px;border-right:1px solid var(--line)">'
            f'<div style="font-family:var(--mono);font-size:10px;letter-spacing:1.5px;'
            f'color:var(--subtle);text-transform:uppercase;margin-bottom:8px">专属潮汐</div>'
            f'{tide_rows}'
            f'</div>'

            f'<div style="padding:14px 16px">'
            f'<div style="font-family:var(--mono);font-size:10px;letter-spacing:1.5px;'
            f'color:var(--subtle);text-transform:uppercase;margin-bottom:4px">钓法攻略</div>'
            f'{method_rows}'
            f'</div>'

            f'</div>'

            f'<div style="border-top:1px solid var(--line);padding:10px 16px">'
            f'<div style="font-family:var(--mono);font-size:10px;letter-spacing:1.5px;'
            f'color:var(--subtle);text-transform:uppercase;margin-bottom:6px">'
            f'⚖️ NSW 法定尺寸 · Legal Size</div>'
            f'{legal_html}'
            f'</div>'

            f'<div style="border-top:1px solid var(--line);padding:12px 18px;'
            f'background:var(--surface2);display:grid;grid-template-columns:1fr 1fr;gap:12px">'
            f'<div>'
            f'<div style="font-family:var(--mono);font-size:10px;letter-spacing:1.5px;'
            f'color:var(--subtle);text-transform:uppercase;margin-bottom:4px">🚗 自驾路线</div>'
            f'<div style="font-size:12px;color:var(--text);line-height:1.55">{spot["route"]}</div>'
            f'<a href="https://www.google.com/maps?q={spot["lat"]},{spot["lon"]}" target="_blank" '
            f'style="display:inline-block;margin-top:6px;font-size:11.5px;color:#2a5fb0;'
            f'text-decoration:none;font-weight:600">📍 Google Maps 导航 →</a>'
            f'</div>'
            f'<div>'
            f'<div style="font-family:var(--mono);font-size:10px;letter-spacing:1.5px;'
            f'color:var(--subtle);text-transform:uppercase;margin-bottom:4px">🅿️ 停车方案</div>'
            f'<div style="font-size:12px;color:var(--text);line-height:1.55">{spot["parking"]}</div>'
            f'</div>'
            f'</div>'

            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(_fuel_html(spot), unsafe_allow_html=True)


# ── 今日决策面板 ──────────────────────────────────────────────────────────

def render_decision_panel(all_spot_data: list, day_w: dict, base_tides: list, label: str) -> None:
    green_list  = [x for x in all_spot_data if x[1]["color"] == "sage"]
    orange_list = [x for x in all_spot_data if x[1]["color"] == "amber"]
    red_list    = [x for x in all_spot_data if x[1]["color"] == "coral"]
    green_n, orange_n, red_n = len(green_list), len(orange_list), len(red_list)
    total = len(all_spot_data) or 1

    if green_n >= total * 0.4:
        v1_band, v1_kicker = "var(--sage)", "✓ GO · OVERALL"
        v1_title, v1_body  = "适合出门", f"{green_n} 个钓点达推荐标准，海况温和"
    elif green_n > 0:
        v1_band, v1_kicker = "var(--amber)", "△ CAUTION · OVERALL"
        v1_title, v1_body  = "优先内湾钓点", f"{green_n} 个内湾钓点可安全前往"
    else:
        v1_band, v1_kicker = "var(--coral)", "⊘ NO-GO · OVERALL"
        v1_title, v1_body  = "暂不建议出行", "浪涌与风速均超安全阈值，建议改期"

    protected_ok   = sum(1 for s, sa, _, _ in all_spot_data if s.get("water_type") != "ocean" and sa["color"] != "coral")
    protected_best = sum(1 for s, sa, _, _ in all_spot_data if s.get("water_type") != "ocean" and sa["color"] == "sage")
    ocean_safe     = sum(1 for s, sa, _, _ in all_spot_data if s.get("water_type") == "ocean" and sa["color"] == "sage")
    swell_val = day_w.get("swell_height") or 0
    wind_val  = day_w.get("wind") or 0
    ocean_danger = swell_val > OCEAN_SWELL_DANGER or wind_val > OCEAN_WIND_DANGER
    if ocean_danger:
        v2_band, v2_kicker = "var(--coral)", "SPOT TYPE · ADVICE"
        v2_title = "避开外海"
        if protected_ok > 0:
            v2_body = f"外海危险，{protected_ok} 个内湾/咸淡水点可前往（{protected_best} 个极佳）"
        else:
            v2_body = "今日海况全面恶化，建议改期或极轻装置内湾试探"
    elif protected_ok + ocean_safe == 0:
        v2_band, v2_kicker = "var(--coral)", "SPOT TYPE · ADVICE"
        v2_title = "暂缓出行"
        v2_body  = "当前海况超安全阈值，建议改期"
    elif ocean_safe >= protected_ok:
        v2_band, v2_kicker = "var(--sage)", "SPOT TYPE · ADVICE"
        v2_title = "内外均可"
        v2_body  = f"外海 {ocean_safe} 点 · 内湾/咸淡水 {protected_ok} 点均可前往"
    else:
        v2_band, v2_kicker = "var(--amber)", "SPOT TYPE · ADVICE"
        v2_title = "优先内湾"
        v2_body  = f"内湾/咸淡水 {protected_ok} 点可前往，外海 {ocean_safe} 点可选"

    sorted_tides = sorted(base_tides, key=lambda t: t["time"])
    highs        = [t for t in sorted_tides if t["is_high"]]
    if highs:
        h = highs[0]["time"]
        v3_win = f"{(h - timedelta(hours=1.5)).strftime('%H:%M')}–{(h + timedelta(hours=1.5)).strftime('%H:%M')}"
        v3_sub = f"满潮 {h.strftime('%H:%M')} 前后 1.5h"
    else:
        v3_win, v3_sub = "—", "参考各钓点潮汐"

    fw_n  = sum(1 for s, _, _, _ in all_spot_data if s.get("water_type") == "freshwater")
    sea_n = len(all_spot_data) - fw_n
    month = datetime.now().month

    if green_n > 0:
        if fw_n > 0 and sea_n == 0:
            season_tip = "旺季（4–10月）Bass 活跃度极高" if 4 <= month <= 10 else "淡季，建议早晚时段出击"
            v4_text = f"今日淡水出钓：{season_tip}，携带软饵路亚或活铅沉底线组最为稳妥。"
        elif fw_n > 0:
            v4_text = (
                f"今日海水与淡水点均可出击。{v3_win} 黄金时段优先；"
                "海水点带 Running Sinker，淡水点带软饵路亚。"
            )
        elif ocean_danger:
            v4_text = (
                f"外海今日危险，优先内湾或咸淡水钓点；"
                f"{v3_win} 黄金时段出击，建议携带无铅漂或 Running Sinker 线组。"
            )
        else:
            v4_text = f"今日最佳：{v3_win} 黄金时段出击，外海/内湾均可；建议携带 Running Sinker 或路亚线组。"
    else:
        if fw_n > 0:
            v4_text = "淡水点风速偏大，建议在背风河岸处作钓，或等待风速回落后再出发。"
        else:
            v4_text = "建议等待明日或后天预报窗口，或前往内湾避风点以极轻线组试探。"

    def _verdict_card(band_color, kicker_text, big, body, big_style=""):
        return f"""
        <div style="background:var(--surface);border:1px solid var(--line);border-radius:14px;
                    border-left:4px solid {band_color};padding:18px 18px 16px;height:100%;
                    box-shadow:0 2px 6px rgba(15,30,50,0.025)">
            <div style="font-family:var(--mono);font-size:10.5px;letter-spacing:1.5px;
                        color:var(--subtle);text-transform:uppercase;margin-bottom:8px">{kicker_text}</div>
            <div style="font-family:var(--serif-zh);font-size:20px;font-weight:600;
                        color:var(--text);line-height:1.25;margin-bottom:6px;{big_style}">{big}</div>
            <div style="font-size:12.5px;color:var(--muted);line-height:1.5">{body}</div>
        </div>"""

    def _window_card(band_color, kicker_text, big, body):
        return f"""
        <div style="background:var(--surface);border:1px solid var(--line);border-radius:14px;
                    border-left:4px solid {band_color};padding:18px 18px 16px;height:100%;
                    box-shadow:0 2px 6px rgba(15,30,50,0.025)">
            <div style="font-family:var(--mono);font-size:10.5px;letter-spacing:1.5px;
                        color:var(--subtle);text-transform:uppercase;margin-bottom:8px">{kicker_text}</div>
            <div style="font-family:var(--serif-en);font-size:22px;font-weight:600;
                        color:var(--primary);line-height:1.2;margin-bottom:6px">{big}</div>
            <div style="font-size:12.5px;color:var(--muted);line-height:1.5">{body}</div>
        </div>"""

    v1, v2, v3, v4 = st.columns([1.2, 1, 1, 1.4])
    v1.markdown(_verdict_card(v1_band, v1_kicker, v1_title, v1_body), unsafe_allow_html=True)
    v2.markdown(_verdict_card(v2_band, v2_kicker, v2_title, v2_body), unsafe_allow_html=True)
    v3.markdown(_window_card("var(--primary)", "WINDOW · BEST TIME", v3_win, v3_sub), unsafe_allow_html=True)
    v4.markdown(
        f'<div style="background:var(--surface2);border:1px solid var(--line);border-radius:14px;'
        f'padding:18px 18px 16px;height:100%;box-shadow:0 2px 6px rgba(15,30,50,0.025)">'
        f'<div style="font-family:var(--mono);font-size:10.5px;letter-spacing:1.5px;'
        f'color:var(--subtle);text-transform:uppercase;margin-bottom:8px">AI MATE · ADVICE</div>'
        f'<div style="font-size:13px;color:var(--text);line-height:1.6">{v4_text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── 加油站 HTML 片段 ──────────────────────────────────────────────────────

def _fuel_html(spot: dict) -> str:
    stations = get_nearby_fuel(spot["lat"], spot["lon"])
    fuelcheck_url = "https://www.fuelcheck.nsw.gov.au/app"
    link = (
        f'<a href="{fuelcheck_url}" target="_blank" '
        f'style="display:inline-block;margin-top:6px;background:#fff3e0;color:#e65100;'
        f'padding:3px 10px;border-radius:8px;font-size:0.74em;font-weight:600;'
        f'text-decoration:none">⛽ 更多油价 →</a>'
    )
    if stations:
        rows = ""
        for s in stations:
            price_str = f"{s['price']:.1f}¢/L" if s["price"] else "—"
            rows += (
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:4px 0;border-bottom:1px solid #f5f5f5;font-size:0.77em">'
                f'<div>'
                f'<span style="font-weight:600;color:#333">{s["brand"] or s["name"]}</span>'
                f'<span style="color:#aaa;margin-left:5px">{s["dist_km"]}km</span>'
                f'</div>'
                f'<div>'
                f'<span style="background:#fff3e0;color:#e65100;padding:1px 6px;'
                f'border-radius:6px;font-size:0.9em;font-weight:700">{s["fuel_type"]}</span>'
                f'&nbsp;<span style="color:#1f8f53;font-weight:800">{price_str}</span>'
                f'</div>'
                f'</div>'
            )
        return (
            f'<div style="border-top:1px solid #f0f4f8;padding-top:8px;margin-top:6px">'
            f'<div style="font-size:0.74em;font-weight:700;color:#888;margin-bottom:5px">'
            f'⛽ 附近加油站（实时）</div>'
            f'{rows}'
            f'{link}'
            f'</div>'
        )
    gas = spot.get("nearby_gas", "")
    return (
        f'<div style="border-top:1px solid #f0f4f8;padding-top:8px;margin-top:6px;'
        f'font-size:0.77em;color:#555">'
        + (f'⛽ {gas}<br>' if gas else "")
        + link
        + '</div>'
    )


# ── 钓点详情（地图右侧内联）────────────────────────────────────────────────

def _render_map_spot_detail(spot: dict, safety: dict, tides: list, weather: dict) -> None:
    c_border = {"sage": "#4f9b76", "amber": "#d99540", "coral": "#cc5e54"}
    c_bg     = {"sage": "#e7f3ec", "amber": "#fcf2e0", "coral": "#fbeae8"}
    border   = c_border.get(safety["color"], "#888")
    badge_bg = c_bg.get(safety["color"], "#f5f5f5")

    wt       = spot.get("water_type", "harbour")
    is_fw    = wt == "freshwater"
    swell    = weather.get("swell_height") or 0
    wind     = weather.get("wind") or 0
    sw_color = "#8a9cb2" if is_fw else _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)
    wi_color = _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)
    swell_icon_html = (
        f'🏞️ <b style="color:{sw_color}">淡水</b>'
        if is_fw else
        f'🌊 <b style="color:{sw_color}">{swell}m</b>'
    )

    fish_html = "".join(
        f'<span style="background:#e3f2fd;color:#1565c0;padding:2px 8px;border-radius:10px;'
        f'font-size:0.76em;margin:2px 2px 0;display:inline-block">{f}</span>'
        for f in spot["fish_tags"]
    )
    method_html = "".join(
        f'<span style="background:#f3e5f5;color:#6a1b9a;padding:2px 8px;border-radius:10px;'
        f'font-size:0.75em;margin:2px 2px 0;display:inline-block">{m}</span>'
        for m in spot["supported_methods"][:4]
    )
    if wt == "freshwater":
        tides_html = "🏞️ 淡水钓点 · 无潮汐影响"
    else:
        tides_html = " &nbsp;|&nbsp; ".join(
            f"{t['label']} <b>{t['time'].strftime('%H:%M')}</b>" for t in tides
        )
        if wt == "brackish":
            tides_html += ' &nbsp;<span style="color:#d99540;font-size:0.88em">⚠ 咸淡水·时间仅供参考</span>'

    maps_url = f"https://www.google.com/maps?q={spot['lat']},{spot['lon']}"

    first_method = spot["supported_methods"][0] if spot["supported_methods"] else ""
    tip_raw      = spot["method_tips"].get(first_method, "")
    tip_text     = tip_raw[:100] + "…" if len(tip_raw) > 100 else tip_raw
    tip_block    = (
        f'<div style="background:#f9f9f9;border-radius:8px;padding:8px 10px;'
        f'font-size:0.78em;color:#555;margin-bottom:10px">💡 {tip_text}</div>'
        if tip_text else ""
    )

    st.html(f"""
    <div style="background:white;border-radius:14px;border-top:4px solid {border};
                box-shadow:0 2px 12px rgba(0,0,0,0.08);padding:16px 18px;
                max-height:430px;overflow-y:auto;font-family:sans-serif">

        <div style="font-size:1.02em;font-weight:700;color:#1a1a2e;
                    margin-bottom:8px;line-height:1.4">{spot['name']}</div>

        <span style="background:{badge_bg};color:{border};padding:2px 12px;
                     border-radius:16px;font-size:0.8em;font-weight:600">
            {safety['status']}
        </span>

        <div style="background:{badge_bg};border-left:3px solid {border};border-radius:6px;
                    padding:8px 12px;margin:10px 0;font-size:0.81em;color:{border}">
            {safety['advice']}
        </div>

        <div style="font-size:0.79em;color:#888;margin-bottom:8px">
            📍 {spot['region']} &nbsp;·&nbsp; {spot['type']}
        </div>

        <div style="background:#f8fafc;border-radius:8px;padding:8px 12px;margin-bottom:10px;
                    font-size:0.88em">
            {swell_icon_html}
            &emsp; 💨 <b style="color:{wi_color}">{wind}km/h</b>
            &emsp; 👨‍👩‍👧‍👦 {spot['family_friendly'].split()[0]}
        </div>

        <div style="font-size:0.79em;color:#555;margin-bottom:4px">
            ⏱️ <b>最佳时段</b>&nbsp; {spot['best_window']}
            <span style="background:#e3f2fd;color:#1565c0;padding:1px 8px;border-radius:10px;
                         font-size:0.9em;margin-left:6px;font-weight:600">
                今日 {_best_window_times(spot['best_window'], tides)}
            </span>
        </div>
        <div style="font-size:0.79em;color:#555;margin-bottom:10px">
            🌊 <b>专属潮汐</b>&nbsp; {tides_html}
        </div>

        <div style="font-size:0.8em;color:#444;margin-bottom:4px">🐟 目标鱼种</div>
        <div style="margin-bottom:10px">{fish_html}</div>

        <div style="font-size:0.8em;color:#444;margin-bottom:4px">🎣 推荐钓法</div>
        <div style="margin-bottom:8px">{method_html}</div>

        {tip_block}

        <div style="border-top:1px solid #f0f4f8;padding-top:10px;
                    font-size:0.77em;color:#888;line-height:1.7">
            🚗 {spot['route']}<br>
            🅿️ {spot['parking']}<br>
            <a href="{maps_url}" target="_blank"
               style="display:inline-block;margin-top:5px;color:#1565c0;font-weight:600;
                      text-decoration:none;font-size:0.9em">📍 Google Maps 导航 →</a>
        </div>
        {_fuel_html(spot)}
    </div>
    """)


# ── 地图 + 点击详情 ───────────────────────────────────────────────────────

def render_map_section(day_offset: int, all_spot_data: list) -> None:
    STATUS_COLOR = {"sage": "#c69230", "amber": "#d99540", "coral": "#cc5e54"}

    col_map, col_detail = st.columns([3, 2])

    with col_map:
        m = folium.Map(
            location=[-33.86, 151.22], zoom_start=11,
            tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
            attr="© OpenStreetMap · CARTO",
        )

        for spot, safety, _, _ in all_spot_data:
            bg    = STATUS_COLOR.get(safety["color"], "#8a9cb2")
            emoji = _WT_EMOJI.get(spot.get("water_type", "harbour"), "📍")
            icon  = folium.DivIcon(
                html=(
                    f'<div style="background:{bg};border:2px solid white;border-radius:50%;'
                    f'width:24px;height:24px;display:flex;align-items:center;justify-content:center;'
                    f'font-size:11px;box-shadow:0 1px 5px rgba(0,0,0,0.35);cursor:pointer">'
                    f'{emoji}</div>'
                ),
                icon_size=(24, 24),
                icon_anchor=(12, 12),
            )
            folium.Marker(
                location=[spot["lat"], spot["lon"]],
                icon=icon,
                tooltip=spot["name"],
                popup=spot["name"],
            ).add_to(m)

        legend_html = """
        <div style="position:absolute;bottom:28px;right:10px;z-index:9999;
                    background:white;border-radius:10px;padding:8px 12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.18);font-size:11px;line-height:1.8">
          <div style="font-weight:700;color:#333;margin-bottom:3px">图例 Legend</div>
          <div>🌊 外海 &nbsp; ⚓ 内湾 &nbsp; 🔀 咸淡水 &nbsp; 🏞️ 淡水</div>
          <div style="display:flex;gap:8px;margin-top:3px;align-items:center">
            <span style="background:#4f9b76;width:10px;height:10px;border-radius:50%;display:inline-block"></span>推荐
            <span style="background:#d99540;width:10px;height:10px;border-radius:50%;display:inline-block"></span>谨慎
            <span style="background:#cc5e54;width:10px;height:10px;border-radius:50%;display:inline-block"></span>危险
          </div>
        </div>"""
        m.get_root().html.add_child(folium.Element(legend_html))

        map_data = st_folium(
            m, use_container_width=True, height=430,
            returned_objects=["last_object_clicked"],
            key=f"map_{day_offset}",
        )

    with col_detail:
        clicked = (map_data or {}).get("last_object_clicked")

        if not clicked:
            st.html("""
            <div style="height:430px;display:flex;flex-direction:column;
                        align-items:center;justify-content:center;
                        background:white;border-radius:14px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.07);
                        color:#ccc;text-align:center;padding:20px">
                <div style="font-size:2.4em;margin-bottom:14px">🗺️</div>
                <div style="font-size:0.95em;font-weight:600;color:#bbb">点击地图标记</div>
                <div style="font-size:0.82em;margin-top:6px;color:#ccc">查看钓点详细信息</div>
            </div>
            """)
        else:
            clat, clng = clicked["lat"], clicked["lng"]
            spot, safety, tides, weather = min(
                all_spot_data,
                key=lambda x: abs(x[0]["lat"] - clat) + abs(x[0]["lon"] - clng),
            )
            _render_map_spot_detail(spot, safety, tides, weather)


# ── 日期 Tab 渲染 ─────────────────────────────────────────────────────────

def render_day_tab(day_offset: int) -> None:
    target_date = datetime.now() + timedelta(days=day_offset)
    label = "今天" if day_offset == 0 else ("明天" if day_offset == 1 else "后天")

    overview_weather = get_marine_forecast(-33.8688, 151.2093)
    day_w      = overview_weather["days"][day_offset]
    next_day_w = overview_weather["days"][day_offset + 1] if day_offset < 2 else None
    base_tides = get_tides_for_date(target_date)

    section_head("OVERALL CONDITIONS · SYDNEY", "悉尼整体海况", "Open-Meteo · 缓存 1 小时")
    left_col, right_col = st.columns([1.6, 1])
    with left_col:
        render_weather_panel(day_w, overview_weather["success"], next_day=next_day_w)
    with right_col:
        with st.container(border=True):
            moon_emoji, moon_name, moon_tip = _moon_phase(target_date)
            st.markdown(
                '<div style="font-family:var(--mono);font-size:11px;letter-spacing:2px;'
                'color:var(--subtle);text-transform:uppercase;margin-bottom:6px">'
                '基准潮汐</div>'
                '<div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px">'
                '<div style="font-family:var(--serif-zh);font-size:18px;font-weight:600">潮汐表 '
                '<span style="font-family:var(--serif-en);font-style:italic;color:var(--muted);'
                'font-size:15px;font-weight:400">Tide curve</span></div>'
                f'<div style="display:flex;align-items:center;gap:5px;'
                f'background:var(--surface2);border:1px solid var(--line);border-radius:999px;'
                f'padding:2px 10px">'
                f'<span style="font-size:16px">{moon_emoji}</span>'
                f'<div><div style="font-size:11px;font-weight:600;color:var(--text)">{moon_name}</div>'
                f'<div style="font-size:10px;color:var(--muted)">{moon_tip}</div>'
                f'</div></div>'
                '</div>',
                unsafe_allow_html=True,
            )
            render_tide_panel(base_tides, chart_key=f"tide_{day_offset}", target_date=target_date)

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    filtered = [s for s in spots if spot_matches(s)]
    all_spot_data = []
    for spot in filtered:
        forecast   = get_marine_forecast(spot["lat"], spot["lon"])
        spot_day_w = forecast["days"][day_offset]
        safety     = assess_safety(spot, spot_day_w)
        tides      = get_tides_for_date(target_date, spot["tide_delay"])
        all_spot_data.append((spot, safety, tides, spot_day_w))

    # 按安全状态排序：推荐 → 谨慎 → 危险
    _safety_order = {"sage": 0, "amber": 1, "coral": 2}
    all_spot_data.sort(key=lambda x: _safety_order.get(x[1]["color"], 3))

    section_head(f"{label.upper()} · GO / NO-GO", f"{label}出钓决策", "根据实时海况自动生成")
    render_decision_panel(all_spot_data, day_w, base_tides, label)

    # ── 三天最佳出钓日横幅 ──────────────────────────────────────────────────
    day_safe_counts = []
    for _di in range(3):
        _cnt = sum(
            1 for spot in filtered
            if assess_safety(spot, get_marine_forecast(spot["lat"], spot["lon"])["days"][_di])["color"] == "sage"
        )
        day_safe_counts.append(_cnt)
    best_di   = day_safe_counts.index(max(day_safe_counts))
    day_names = ["今天", "明天", "后天"]
    if best_di != day_offset:
        diff = day_safe_counts[best_di] - day_safe_counts[day_offset]
        st.markdown(
            f'<div style="background:linear-gradient(90deg,#e8f5e9,#f1f8e9);'
            f'border-radius:12px;padding:10px 18px;border-left:4px solid #4f9b76;'
            f'display:flex;align-items:center;gap:12px;margin-bottom:8px">'
            f'<span style="font-size:20px">💡</span>'
            f'<div><span style="font-size:13px;color:#2e7d32;font-weight:600">'
            f'{day_names[best_di]}出钓更佳</span>'
            f'<span style="font-size:12px;color:#555;margin-left:8px">'
            f'比{label}多 {diff} 个推荐钓点（共 {day_safe_counts[best_di]} 个✅）'
            f' → 切换到「{day_names[best_di]}」标签查看</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="background:#e8f5e9;border-radius:12px;padding:8px 18px;'
            f'border-left:4px solid #4f9b76;font-size:12.5px;color:#2e7d32;'
            f'font-weight:600;margin-bottom:8px">'
            f'✅ {label}是未来三天最佳出钓日（{day_safe_counts[day_offset]} 个推荐钓点）'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    top_sage  = [(s, sa, ti, sw) for s, sa, ti, sw in all_spot_data if sa["color"] == "sage"]
    top_amber = [(s, sa, ti, sw) for s, sa, ti, sw in all_spot_data if sa["color"] == "amber"]
    top_safe  = top_sage or top_amber
    is_amber_fallback = not top_sage and bool(top_amber)
    pick_accent = "海况温和，综合评分最优" if not is_amber_fallback else "无满分点，以下为谨慎可前往钓点"
    section_head(f"TOP PICK · {label.upper()}", f"{label}精选推荐", pick_accent)
    if top_safe:
        top3 = top_safe[:3]
        cols = st.columns(len(top3))
        for col, (spot, safety, tides, dw) in zip(cols, top3):
            render_hero_card(col, spot, safety, dw, tides)
        if is_amber_fallback:
            st.markdown(
                '<div style="background:#fcf2e0;border-radius:10px;padding:10px 16px;'
                'border-left:3px solid var(--amber);font-size:12.5px;color:#7a5010;margin-top:6px">'
                '⚠️ 当日无满分推荐钓点，以上为谨慎可前往的内湾钓点，出行请注意风浪变化。'
                '</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="background:linear-gradient(90deg,#fbf3e1 0%,#fdf8eb 60%,#fff 100%);'
            'border-radius:14px;padding:20px 24px;border:1px solid #f0e3c0;'
            'border-left:4px solid var(--gold)">'
            '<div style="font-family:var(--serif-zh);font-size:17px;font-weight:600;margin-bottom:6px">'
            f'当日海况不佳，暂无推荐钓点</div>'
            '<div style="font-size:13px;color:var(--muted);line-height:1.55">'
            '涌浪或风速超出安全阈值。调整侧边栏筛选条件、改去内湾试试手气。</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    section_head(f"MAP · {len(all_spot_data)} SPOTS", "钓点地图", "点击标记查看详情")
    render_map_section(day_offset, all_spot_data)

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    visible_list = [(s, sa, ti, sw) for s, sa, ti, sw in all_spot_data
                    if not (safe_only and not sa["safe"])]
    section_head(
        f"MATCHED SPOTS · {len(visible_list)} / {len(spots)}",
        "匹配钓点", "按当日海况评分排序"
    )
    visible = 0
    for spot, safety, spot_tides, spot_day_w in visible_list:
        render_spot_card(spot, safety, spot_tides, spot_day_w, day_offset)
        visible += 1
    if visible == 0:
        active_filters = []
        if selected_methods: active_filters.append(f"钓法 ({len(selected_methods)} 种)")
        if selected_fish:    active_filters.append(f"鱼种 ({len(selected_fish)} 种)")
        if selected_region != "全部 · All Sydney": active_filters.append(f"区域「{selected_region}」")
        if water_type != "全部 · All": active_filters.append(f"水域「{water_type}」")
        if safe_only:   active_filters.append("隐藏危险钓点")
        if family_only: active_filters.append("仅家庭友好")
        hint = "、".join(active_filters) if active_filters else "未知条件"
        st.info(f"ℹ️ 当前筛选「{hint}」无匹配钓点，点击「↺ 重置所有筛选」或放宽条件。")


# ── 主页面 ────────────────────────────────────────────────────────────────

today = datetime.now()
date_str = f"{today.year} 年 {today.month} 月 {today.day} 日"
weekdays = ["周一","周二","周三","周四","周五","周六","周日"]
weekday  = weekdays[today.weekday()]

st.markdown(
    f'<div class="hero" style="position:relative;border-radius:14px;overflow:hidden;'
    f'padding:28px 32px;background:linear-gradient(110deg,#1f4a8d 0%,#2a5fb0 55%,#3479c9 100%);'
    f'color:#fff;margin-bottom:16px">'
    f'<div style="font-family:IBM Plex Mono;font-size:11px;letter-spacing:2px;'
    f'color:rgba(255,255,255,0.7);text-transform:uppercase;margin-bottom:8px">'
    f'实时海况 · 潮汐推算 · 智能推荐</div>'
    f'<h1 style="font-family:Noto Serif SC,serif;font-size:32px;font-weight:600;'
    f'color:#fff;margin:0 0 6px">悉尼钓鱼助手 '
    f'<span style="font-family:Source Serif 4,Georgia,serif;font-style:italic;'
    f'color:#c69230;font-weight:400">Pro+</span></h1>'
    f'<div style="font-size:14px;color:rgba(255,255,255,0.8)">'
    f'{date_str} · {weekday} · 悉尼</div>'
    f'</div>',
    unsafe_allow_html=True,
)

today_obj = datetime.now()
tab1, tab2, tab3 = st.tabs([
    f"今天  {today_obj.strftime('%m/%d')}  Today",
    f"明天  {(today_obj + timedelta(days=1)).strftime('%m/%d')}  Tomorrow",
    f"后天  {(today_obj + timedelta(days=2)).strftime('%m/%d')}  Day after",
])
with tab1: render_day_tab(0)
with tab2: render_day_tab(1)
with tab3: render_day_tab(2)

st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#8a9cb2;font-size:0.82em;padding:4px 0 16px">
    🚨 <b>安全提示</b>：外海矶钓请务必穿戴救生衣和防滑钉鞋，结伴同行，浪况不对立刻撤退。<br>
    天气数据来自
    <a href="https://open-meteo.com/" target="_blank" style="color:#2a5fb0">Open-Meteo</a>，
    潮汐为天文估算，出行前请参考
    <a href="http://www.bom.gov.au/nsw/forecasts/sydney.shtml" target="_blank"
       style="color:#2a5fb0">BOM 官方预报</a>。
</div>
""", unsafe_allow_html=True)
