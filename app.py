# ============================================================
# app.py — 悉尼钓鱼助手 Pro+ 主程序
# ============================================================

import math
import streamlit as st
from datetime import datetime, timedelta
import os

import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

from config import (
    ALL_METHODS, ALL_FISH, FISH_COOKING_RECIPES,
    OCEAN_SWELL_DANGER, OCEAN_WIND_DANGER,
    SHELTERED_SWELL_WARN, SHELTERED_WIND_WARN,
)
from services.weather import get_marine_forecast
from services.tides import get_tides_for_date
from data.loader import load_spots

# ── 页面配置 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="悉尼钓鱼助手 Pro+",
    page_icon="🎣",
    layout="wide",
)

# ── 加载钓点数据 ──────────────────────────────────────────────────────────
spots = load_spots()

# ── 自定义 CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 全局背景 */
.stApp { background: #f0f6fb; }

/* 页面内边距缩小 */
.block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

/* Tab 样式 */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: white;
    border-radius: 12px;
    padding: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 6px 18px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #0d4a6b !important;
    color: white !important;
}

/* Expander 卡片化 */
[data-testid="stExpander"] {
    background: white;
    border-radius: 14px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07) !important;
    border: 1px solid rgba(0,0,0,0.05) !important;
    margin-bottom: 10px;
    overflow: hidden;
}

/* 侧边栏背景 */
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0a3d5c 0%, #1565a8 100%);
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stCheckbox label {
    color: rgba(255,255,255,0.92) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border-color: rgba(255,255,255,0.25) !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: rgba(255,255,255,0.2) !important;
}

/* 分隔线 */
hr { border: none; border-top: 1px solid #dde8f0; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ── 侧边栏：筛选器 ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:24px 0 12px">
        <div style="font-size:2.8em">🎣</div>
        <div style="font-size:1.25em;font-weight:700;color:white;margin-top:8px">悉尼钓鱼助手</div>
        <div style="font-size:0.8em;color:rgba(255,255,255,0.65);margin-top:3px;letter-spacing:2px">PRO+</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**🔍 智能筛选**")
    selected_methods = st.multiselect(
        "钓法（可多选）",
        ALL_METHODS,
        help="不选则展示所有钓法的钓点",
    )
    selected_fish = st.multiselect(
        "目标鱼种（可多选）",
        ALL_FISH,
        help="不选则展示所有鱼种的钓点",
    )
    st.markdown("---")
    safe_only = st.checkbox("⚠️ 隐藏危险钓点", value=False)
    st.markdown("---")
    st.caption(
        "📡 天气：Open-Meteo（缓存1小时）\n\n"
        "🌊 海况：按钓点坐标分区获取\n\n"
        "⏰ 潮汐：天文近似推算（±30-60分钟）\n\n"
        "升级精度 → [WorldTides API](https://www.worldtides.info/api)"
    )


# ── 工具函数 ──────────────────────────────────────────────────────────────

def spot_matches(spot: dict) -> bool:
    if selected_methods and not any(m in spot["supported_methods"] for m in selected_methods):
        return False
    if selected_fish and not any(f in spot["fish_tags"] for f in selected_fish):
        return False
    return True


def assess_safety(spot: dict, day_weather: dict) -> dict:
    swell = day_weather.get("swell_height") or 0.0
    wind  = day_weather.get("wind") or 0.0

    if not spot["sheltered"] and (swell > OCEAN_SWELL_DANGER or wind > OCEAN_WIND_DANGER):
        return {
            "status": "❌ 极度危险",
            "score":  "⭐",
            "safe":   False,
            "color":  "red",
            "advice": (
                f"外海浪涌预计 {swell}m，风速 {wind}km/h，"
                "该点属于完全暴露的外海地形，极其危险！请转移到内湾避风钓点。"
            ),
        }
    if spot["sheltered"] and (swell > SHELTERED_SWELL_WARN or wind > SHELTERED_WIND_WARN):
        return {
            "status": "⚠️ 谨慎前往",
            "score":  "⭐⭐⭐",
            "safe":   True,
            "color":  "orange",
            "advice": (
                f"风速偏大（{wind}km/h），内湾虽可避浪，但顶风抛投体感较差，"
                "建议选背风位或大桥底部作钓。"
            ),
        }
    return {
        "status": "✅ 极力推荐",
        "score":  "⭐⭐⭐⭐⭐",
        "safe":   True,
        "color":  "green",
        "advice": "此日海况温和，非常适合出击，祝大鲫大鲈！🎉",
    }


def _val_color(value: float, warn: float, danger: float) -> str:
    if value >= danger: return "#dc3545"
    if value >= warn:   return "#fd7e14"
    return "#28a745"


# ── 天气面板（彩色指标卡） ─────────────────────────────────────────────────

def render_weather_panel(day_weather: dict, data_ok: bool) -> None:
    if not data_ok:
        st.warning("⚠️ **天气数据加载失败**，以下为估算值，出行前请以 BOM 官方预报为准。", icon="🛰️")

    temp         = day_weather.get("temp") or 0
    temp_min     = day_weather.get("temp_min") or 0
    wind         = day_weather.get("wind") or 0
    wave         = day_weather.get("wave") or 0
    swell        = day_weather.get("swell_height") or 0
    rain_prob    = day_weather.get("rain_prob") or 0
    precipitation= day_weather.get("precipitation") or 0
    swell_dir    = day_weather.get("swell_direction", "—")
    swell_period = day_weather.get("swell_period", "—")

    def rain_color(p):
        if p >= 60: return "#dc3545"
        if p >= 25: return "#fd7e14"
        return "#28a745"

    def _card(icon, label, val, unit, color):
        return f"""
        <div style="background:white;border-radius:12px;padding:14px 8px 12px;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07);text-align:center;
                    border-bottom:3px solid {color}">
            <div style="font-size:1.3em;line-height:1">{icon}</div>
            <div style="color:#aaa;font-size:0.72em;margin:5px 0 3px">{label}</div>
            <div style="font-size:1.55em;font-weight:800;color:{color};line-height:1.1">{val}</div>
            <div style="color:#ccc;font-size:0.72em;margin-top:3px">{unit}</div>
        </div>"""

    row1 = st.columns(3)
    row1[0].markdown(_card("🌡️", "最高气温", temp,      "°C",   "#1976D2"), unsafe_allow_html=True)
    row1[1].markdown(_card("🌡️", "最低气温", temp_min,  "°C",   "#42a5f5"), unsafe_allow_html=True)
    row1[2].markdown(_card("🌧️", "降雨概率", f"{int(rain_prob)}%", "",
                           rain_color(rain_prob)), unsafe_allow_html=True)

    row2 = st.columns(3)
    row2[0].markdown(_card("💨", "最大风速", wind,  "km/h",
                           _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)), unsafe_allow_html=True)
    row2[1].markdown(_card("🌊", "综合浪高", wave,  "m",
                           _val_color(wave,  SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)), unsafe_allow_html=True)
    row2[2].markdown(_card("🌀", "浪涌高度", swell, "m",
                           _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)), unsafe_allow_html=True)

    rain_str = f"{precipitation:.1f} mm" if precipitation > 0 else "无降水"
    st.markdown(f"""
    <div style="text-align:center;color:#666;font-size:0.84em;margin-top:10px;
                background:white;border-radius:10px;padding:8px 14px;
                box-shadow:0 1px 6px rgba(0,0,0,0.05)">
        🌂&nbsp; 预计降水 <b>{rain_str}</b>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        🧭&nbsp; 涌向 <b>{swell_dir}°</b>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        ⏱️&nbsp; 浪涌周期 <b>{swell_period}s</b>
    </div>
    """, unsafe_allow_html=True)


# ── 最佳时段推算 ──────────────────────────────────────────────────────────

def _best_window_times(best_window: str, tides: list) -> str:
    """根据描述关键词 + 当日潮汐，推算今日参考时间段（返回如 '13:00–15:30'）。"""
    import re

    text = best_window

    # 提取文本中明确写出的时间段（如 (19:30-23:00)）
    explicit = re.findall(r'\d{1,2}:\d{2}[–\-]\d{1,2}:\d{2}', text)
    if explicit:
        return explicit[0]

    sorted_tides = sorted(tides, key=lambda t: t["time"])

    # 从文本提取小时数，如 "1.5小时" → 1.5，"2小时" → 2.0，默认 1.5
    hrs_match = re.search(r'(\d+(?:\.\d+)?)[\s]*小时', text)
    offset_h  = float(hrs_match.group(1)) if hrs_match else 1.5

    def fmt_window(center, before_h, after_h):
        start = center - timedelta(hours=before_h)
        end   = center + timedelta(hours=after_h)
        return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"

    # 优先匹配满潮
    if "满潮" in text or "涨潮" in text or "高潮" in text:
        highs = [t for t in sorted_tides if t["is_high"]]
        if highs:
            return fmt_window(highs[0]["time"], offset_h, offset_h)

    # 干潮 / 落潮
    if "干潮" in text or "落潮" in text or "低潮" in text:
        lows = [t for t in sorted_tides if not t["is_high"]]
        if lows:
            return fmt_window(lows[0]["time"], offset_h, offset_h)

    # 静态时段
    if "破晓" in text or "黎明" in text or "日出" in text:
        return "05:30–08:00"
    if "黄昏" in text or "日落" in text:
        return "17:00–19:30"
    if "夜间" in text or "夜晚" in text:
        return "20:00–23:00"
    if "白天" in text or "正午" in text:
        return "09:00–16:00"

    return "—"


# ── 潮汐时间线 ────────────────────────────────────────────────────────────

def render_tide_panel(base_tides: list) -> None:
    now          = datetime.now()
    sorted_tides = sorted(base_tides, key=lambda x: x["time"])
    times        = [t["time"] for t in sorted_tides]
    min_t, max_t = min(times), max(times)
    span_s       = (max_t - min_t).total_seconds()

    # 余弦插值生成平滑潮汐曲线
    NUM = 150
    heights = []
    for i in range(NUM + 1):
        t = min_t + timedelta(seconds=span_s * i / NUM)
        prev_td = next_td = None
        for td in sorted_tides:
            if td["time"] <= t:
                prev_td = td
            elif next_td is None:
                next_td = td
                break
        if prev_td is None:
            h = 1.0 if sorted_tides[0]["is_high"] else 0.0
        elif next_td is None:
            h = 1.0 if sorted_tides[-1]["is_high"] else 0.0
        else:
            ph = 1.0 if prev_td["is_high"] else 0.0
            nh = 1.0 if next_td["is_high"] else 0.0
            period  = (next_td["time"] - prev_td["time"]).total_seconds()
            elapsed = (t - prev_td["time"]).total_seconds()
            frac    = elapsed / period if period > 0 else 0
            h = ph + (nh - ph) * (1 - math.cos(math.pi * frac)) / 2
        heights.append(h)

    # SVG 布局常量
    VW, VH       = 600, 148
    PX, PT, PB   = 10, 40, 30
    CW, CH       = VW - 2 * PX, VH - PT - PB

    def sx(i):  return PX + i / NUM * CW
    def sy(h):  return PT + (1 - h) * CH

    # 波浪路径
    path_d = "M " + " L ".join(f"{sx(i):.1f},{sy(h):.1f}" for i, h in enumerate(heights))
    ybot   = PT + CH
    fill_d = f"{path_d} L {sx(NUM):.1f},{ybot:.1f} L {sx(0):.1f},{ybot:.1f} Z"

    # "现在"竖线
    now_svg = ""
    if min_t <= now <= max_t:
        nx = PX + (now - min_t).total_seconds() / span_s * CW
        now_svg = (
            f'<line x1="{nx:.1f}" y1="{PT}" x2="{nx:.1f}" y2="{ybot}"'
            f' stroke="#e53935" stroke-width="1.8" stroke-dasharray="5,3"/>'
            f'<rect x="{nx-14:.1f}" y="{PT-17}" width="28" height="14" rx="4" fill="#e53935"/>'
            f'<text x="{nx:.1f}" y="{PT-6}" text-anchor="middle"'
            f' font-size="9.5" fill="white" font-weight="700">现在</text>'
        )

    # 潮汐事件标记
    markers_svg = ""
    for td in sorted_tides:
        x     = PX + (td["time"] - min_t).total_seconds() / span_s * CW
        is_hi = td["is_high"]
        yc    = sy(1.0 if is_hi else 0.0)
        color = "#1565C0" if is_hi else "#EF6C00"
        label = "满潮" if is_hi else "干潮"
        ts    = td["time"].strftime("%H:%M")
        ty, ly = (yc - 22, yc - 11) if is_hi else (yc + 27, yc + 16)
        markers_svg += (
            f'<circle cx="{x:.1f}" cy="{yc:.1f}" r="5.5" fill="{color}"'
            f' stroke="white" stroke-width="2.5"/>'
            f'<text x="{x:.1f}" y="{ty:.1f}" text-anchor="middle"'
            f' font-size="11" fill="{color}" font-weight="700">{ts}</text>'
            f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle"'
            f' font-size="9.5" fill="{color}" opacity="0.85">{label}</text>'
        )

    components.html(f"""
    <style>body{{margin:0;background:transparent}}</style>
    <div style="background:white;border-radius:14px;padding:14px 16px 12px;
                box-shadow:0 2px 12px rgba(0,0,0,0.07)">
        <div style="font-size:0.75em;color:#bbb;margin-bottom:8px">
            ⏰ Fort Denison 基准 &nbsp;·&nbsp; ±30~60 分钟误差
        </div>
        <svg viewBox="0 0 {VW} {VH}" style="width:100%;display:block;overflow:visible">
            <defs>
                <linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#1976D2" stop-opacity="0.28"/>
                    <stop offset="100%" stop-color="#42a5f5" stop-opacity="0.04"/>
                </linearGradient>
            </defs>
            <path d="{fill_d}" fill="url(#wg)"/>
            <path d="{path_d}" fill="none" stroke="#1976D2" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round"/>
            {now_svg}
            {markers_svg}
        </svg>
    </div>
    """, height=210, scrolling=False)


# ── 精选推荐英雄卡 ────────────────────────────────────────────────────────

def render_hero_card(col, spot: dict, safety: dict, day_weather: dict) -> None:
    color_map = {"green": "#2e7d32", "orange": "#e65100", "red": "#c62828"}
    bg_map    = {"green": "#e8f5e9", "orange": "#fff3e0", "red": "#ffebee"}

    border   = color_map.get(safety["color"], "#2e7d32")
    badge_bg = bg_map.get(safety["color"], "#e8f5e9")

    fish_html = "".join(
        f'<span style="background:#e3f2fd;color:#1565c0;padding:2px 9px;border-radius:10px;'
        f'font-size:0.75em;margin:2px 1px;display:inline-block">{f}</span>'
        for f in spot["fish_tags"][:4]
    )
    swell = day_weather.get("swell_height", "—")
    wind  = day_weather.get("wind", "—")

    col.markdown(f"""
    <div style="background:white;border-radius:16px;padding:18px 20px;
                box-shadow:0 4px 20px rgba(0,0,0,0.10);border-top:4px solid {border};
                min-height:210px">
        <div style="font-weight:700;font-size:1.0em;margin-bottom:10px;
                    color:#1a1a2e;line-height:1.3">{spot['name']}</div>
        <span style="background:{badge_bg};color:{border};padding:3px 12px;
                     border-radius:20px;font-size:0.82em;font-weight:600">
            {safety['status']}
        </span>
        <div style="color:#777;font-size:0.82em;margin:10px 0 6px">
            📍 {spot['region']} &nbsp;·&nbsp; {spot['type']}
        </div>
        <div style="color:#444;font-size:0.86em;margin:6px 0">
            🌊 <b>{swell}m</b> &nbsp;&nbsp; 💨 <b>{wind}km/h</b>
        </div>
        <div style="margin:10px 0 6px">{fish_html}</div>
        <div style="color:#666;font-size:0.79em;border-top:1px solid #f0f4f8;
                    padding-top:8px;margin-top:8px">
            ⏱️ {spot['best_window']}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── 钓点详情卡片 ──────────────────────────────────────────────────────────

def render_spot_card(spot: dict, safety: dict, spot_tides: list, spot_weather: dict, day_offset: int) -> None:
    color_map = {"green": "#2e7d32", "orange": "#e65100", "red": "#c62828"}
    bg_map    = {"green": "#e8f5e9", "orange": "#fff3e0", "red": "#ffebee"}
    text_map  = {"green": "#1b5e20", "orange": "#bf360c", "red": "#b71c1c"}

    border    = color_map.get(safety["color"], "#2e7d32")
    badge_bg  = bg_map.get(safety["color"], "#e8f5e9")
    badge_txt = text_map.get(safety["color"], "#1b5e20")

    title = f"{safety['score']}  {spot['name']}  —  {safety['status']}"

    with st.expander(title):
        # 安全状态横幅
        st.markdown(f"""
        <div style="background:{badge_bg};border-left:4px solid {border};
                    padding:10px 16px;border-radius:8px;margin-bottom:16px;
                    color:{badge_txt};font-size:0.92em">
            <b>{safety['status']}</b> &nbsp;—&nbsp; {safety['advice']}
        </div>
        """, unsafe_allow_html=True)

        left, right = st.columns([1.2, 0.8])

        with left:
            st.markdown(
                f"**🌍 区域** &nbsp;`{spot['region']}`"
                f"&emsp;**📍 地形** &nbsp;`{spot['type']}`"
            )
            st.markdown(f"**⏱️ 最佳窗口** &nbsp;{spot['best_window']}")

            tides_str = " &nbsp;|&nbsp; ".join(
                f"{t['label']} `{t['time'].strftime('%H:%M')}`" for t in spot_tides
            )
            st.markdown(f"**⏰ 专属潮汐** &nbsp;{tides_str}")

            # 目标鱼种标签 + 烹饪做法展开
            st.markdown("**🐟 目标鱼种**", unsafe_allow_html=True)
            
            # 为每种鱼创建可点击的标签按钮
            for fish in spot["fish_tags"]:
                recipe = FISH_COOKING_RECIPES.get(fish, {})
                legal_size = recipe.get("legal_size", "—")
                
                # 用 expander label 直接显示所有信息（最稳定）
                expander_label = f"🐟 {fish}  📏 Legal: {legal_size}  🍳"
                photo_url = recipe.get("photo_url", "")
                
                with st.expander(expander_label, expanded=False):
                    photo_path = recipe.get("photo_path", "")
                    has_photo = photo_path and os.path.exists(photo_path) and os.path.getsize(photo_path) > 1000
                    
                    if has_photo:
                        # 有图片时用双列布局
                        col_a, col_b = st.columns([0.3, 0.7])
                        with col_a:
                            st.image(photo_path, use_column_width=True)
                        with col_b:
                            st.markdown(
                                f'<h5 style="margin:0 0 8px 0;padding:0;font-size:1.1em;font-weight:700">🍳 {fish} 烹饪指南</h5>'
                                f'<p style="margin:0;color:#666;font-size:0.85em">📏 法定尺寸：{legal_size}</p>',
                                unsafe_allow_html=True
                            )
                    else:
                        # 无图片时单列布局
                        st.markdown(
                            f'<h5 style="margin:0 0 8px 0;padding:0;font-size:1.1em;font-weight:700">🍳 {fish} 烹饪指南</h5>'
                            f'<p style="margin:0;color:#666;font-size:0.85em">📏 法定尺寸：{legal_size}</p>',
                            unsafe_allow_html=True
                        )
                    
                    st.markdown('<hr style="margin:8px 0 12px 0;border:0;border-top:1px solid #e0e0e0">', unsafe_allow_html=True)
                    
                    # 推荐做法
                    if recipe.get("methods"):
                        st.markdown("**🥘 推荐做法**")
                        for method in recipe["methods"]:
                            st.markdown(f'- {method}')
                    
                    # 小贴士
                    if recipe.get("tips"):
                        st.markdown("\n**💡 烹饪小贴士**")
                        st.info(recipe["tips"])
                    
                    # 参考视频
                    if recipe.get("videos"):
                        st.markdown("\n**🎬 参考视频**")
                        for i, video in enumerate(recipe["videos"], 1):
                            st.markdown(f'- [视频教程 {i}]({video})')

        with right:
            swell = spot_weather.get("swell_height") or 0
            wind  = spot_weather.get("wind") or 0
            sw_color = _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)
            wi_color = _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)

            st.markdown(f"""
            <div style="background:#f8fafc;border-radius:12px;padding:16px 18px">
                <div style="font-size:0.9em;margin-bottom:10px">
                    🌊 浪涌
                    <span style="font-weight:800;color:{sw_color};font-size:1.15em">
                        &nbsp;{swell}m
                    </span>
                    &emsp;
                    💨 风速
                    <span style="font-weight:800;color:{wi_color};font-size:1.15em">
                        &nbsp;{wind}km/h
                    </span>
                </div>
                <div style="font-size:0.86em;color:#555;line-height:1.5">
                    👨‍👩‍👧‍👦 {spot['family_friendly']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 钓法标签 + 战术建议
        method_html = "".join(
            f'<span style="background:#f3e5f5;color:#6a1b9a;padding:3px 10px;'
            f'border-radius:12px;font-size:0.8em;margin:2px;display:inline-block">{m}</span>'
            for m in spot["supported_methods"]
        )
        st.markdown(f"**💡 支持钓法** &nbsp;{method_html}", unsafe_allow_html=True)
        st.markdown("")

        show_methods = (
            [m for m in selected_methods if m in spot["supported_methods"]]
            if selected_methods else spot["supported_methods"]
        )
        for method in show_methods:
            tip = spot["method_tips"].get(
                method, "此钓法在该钓点完全可行，建议现场根据流水微调线组铅重。"
            )
            st.markdown(f"> **{method}**：{tip}")

        st.markdown("---")
        st.markdown(f"**🚗 自驾路线** &nbsp;{spot['route']}")
        st.info(f"🅿️ **停车方案** &nbsp;{spot['parking']}")


# ── 主 Tab 渲染：按日期 ───────────────────────────────────────────────────

def render_day_tab(day_offset: int) -> None:
    target_date = datetime.now() + timedelta(days=day_offset)

    overview_weather = get_marine_forecast(-33.8688, 151.2093)
    day_w      = overview_weather["days"][day_offset]
    base_tides = get_tides_for_date(target_date)

    col_weather, col_tides = st.columns([1.35, 0.65])
    with col_weather:
        st.subheader("🌊 悉尼整体海况")
        render_weather_panel(day_w, overview_weather["success"])
    with col_tides:
        st.subheader("📅 Fort Denison 基准潮汐")
        render_tide_panel(base_tides)

    st.markdown("---")

    # 一次性计算所有钓点（避免重复 API 调用）
    filtered = [s for s in spots if spot_matches(s)]
    all_spot_data = []
    for spot in filtered:
        forecast   = get_marine_forecast(spot["lat"], spot["lon"])
        spot_day_w = forecast["days"][day_offset]
        safety     = assess_safety(spot, spot_day_w)
        tides      = get_tides_for_date(target_date, spot["tide_delay"])
        all_spot_data.append((spot, safety, tides, spot_day_w))

    # 精选推荐区（始终显示，无推荐时给出说明）
    label = "今天" if day_offset == 0 else ("明天" if day_offset == 1 else "后天")
    top_safe = [
        (s, sa, sw)
        for s, sa, ti, sw in all_spot_data
        if sa["safe"] and sa["color"] == "green"
    ]
    st.markdown(f"### 🏆 {label}精选推荐")
    if top_safe:
        top3 = top_safe[:3]
        cols = st.columns(len(top3))
        for col, (spot, safety, dw) in zip(cols, top3):
            render_hero_card(col, spot, safety, dw)
        st.markdown("")
    else:
        st.markdown("""
        <div style="background:#fff8e1;border-left:4px solid #f9a825;border-radius:10px;
                    padding:14px 20px;color:#795548;font-size:0.92em">
            ⚠️ <b>今日海况不佳，暂无推荐出钓点。</b><br>
            <span style="font-size:0.88em;opacity:0.85">
            涌浪或风速超出安全阈值，建议在家休息或改去内湾试试手气。
            可查看明天/后天的预报，或调整侧边栏筛选条件。
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    render_map_section(day_offset, all_spot_data)

    st.markdown("---")
    st.subheader(f"📍 匹配钓点（{len(filtered)} / {len(spots)} 个）")

    visible = 0
    for spot, safety, spot_tides, spot_day_w in all_spot_data:
        if safe_only and not safety["safe"]:
            continue
        render_spot_card(spot, safety, spot_tides, spot_day_w, day_offset)
        visible += 1

    if visible == 0:
        st.info("ℹ️ 当前筛选条件下没有匹配的钓点，请尝试减少筛选条件。")


# ── 加油站 HTML 片段 ──────────────────────────────────────────────────────

def _fuel_html(spot: dict) -> str:
    gas = spot.get("nearby_gas", "")
    fuelcheck_url = "https://www.fuelcheck.nsw.gov.au/app"
    link = (
        f'<a href="{fuelcheck_url}" target="_blank" '
        f'style="display:inline-block;margin-top:5px;background:#fff3e0;color:#e65100;'
        f'padding:3px 10px;border-radius:8px;font-size:0.76em;font-weight:600;'
        f'text-decoration:none">⛽ 查看实时油价 →</a>'
    )
    if gas:
        return (
            f'<div style="border-top:1px solid #f0f4f8;padding-top:8px;margin-top:4px;'
            f'font-size:0.77em;color:#555">'
            f'⛽ <b style="color:#e65100">加油站</b>&nbsp; {gas}<br>'
            f'{link}'
            f'</div>'
        )
    return (
        f'<div style="border-top:1px solid #f0f4f8;padding-top:8px;margin-top:4px">'
        f'{link}'
        f'</div>'
    )


# ── 钓点详情（地图右侧内联）────────────────────────────────────────────────

def _render_map_spot_detail(spot: dict, safety: dict, tides: list, weather: dict) -> None:
    c_border = {"green": "#2e7d32", "orange": "#e65100", "red": "#c62828"}
    c_bg     = {"green": "#e8f5e9", "orange": "#fff3e0", "red": "#ffebee"}
    border   = c_border.get(safety["color"], "#888")
    badge_bg = c_bg.get(safety["color"], "#f5f5f5")

    swell    = weather.get("swell_height") or 0
    wind     = weather.get("wind") or 0
    sw_color = _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)
    wi_color = _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)

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
    tides_html = " &nbsp;|&nbsp; ".join(
        f"{t['label']} <b>{t['time'].strftime('%H:%M')}</b>" for t in tides
    )

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
            🌊 <b style="color:{sw_color}">{swell}m</b>
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
            🅿️ {spot['parking']}
        </div>
        {_fuel_html(spot)}
    </div>
    """)


# ── 地图 + 点击详情 ───────────────────────────────────────────────────────

def render_map_section(day_offset: int, all_spot_data: list) -> None:
    day_label = ["今天", "明天", "后天"][day_offset]

    st.markdown(
        f"**🗺️ 钓点地图** &nbsp;<span style='font-size:0.8em;color:#aaa'>"
        f"{day_label}安全评估 · 点击标记查看详情</span>",
        unsafe_allow_html=True,
    )
    leg_a, leg_b, leg_c, _ = st.columns([1, 1, 1, 4])
    leg_a.markdown("⭐ **推荐**")
    leg_b.markdown("🟠 **谨慎**")
    leg_c.markdown("🔴 **危险**")

    col_map, col_detail = st.columns([3, 2])

    with col_map:
        m = folium.Map(location=[-33.87, 151.21], zoom_start=11, tiles="CartoDB positron")

        for spot, safety, _, _ in all_spot_data:
            is_rec = safety["safe"] and safety["color"] == "green"
            tooltip = (
                f"⭐ {day_label}推荐 | {spot['name']}"
                if is_rec else
                f"{spot['name']} ({safety['status']})"
            )
            if is_rec:
                # 固定尺寸 DivIcon，anchor 精确对准圆心，不含可变宽度文字
                icon_html = (
                    '<div style="width:26px;height:26px;background:#2e7d32;border-radius:50%;'
                    'border:3px solid white;box-shadow:0 0 0 3px rgba(46,125,50,0.4),'
                    '0 2px 8px rgba(46,125,50,0.5);display:flex;align-items:center;'
                    'justify-content:center;color:white;font-size:14px">⭐</div>'
                )
                icon = folium.DivIcon(html=icon_html, icon_size=(26, 26), icon_anchor=(13, 13))
                folium.Marker(
                    location=[spot["lat"], spot["lon"]],
                    tooltip=tooltip,
                    icon=icon,
                ).add_to(m)
            else:
                # CircleMarker：纯矢量，缩放永不漂移
                hex_c = {"orange": "#ef6c00", "red": "#c62828"}.get(safety["color"], "#888")
                folium.CircleMarker(
                    location=[spot["lat"], spot["lon"]],
                    radius=7,
                    color="white",
                    weight=2,
                    fill=True,
                    fill_color=hex_c,
                    fill_opacity=0.9,
                    tooltip=tooltip,
                ).add_to(m)

        map_data = st_folium(
            m, width=None, height=430,
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


# ── 页面主标题 ────────────────────────────────────────────────────────────
today_str = datetime.now().strftime("%Y年%m月%d日")
st.markdown(f"""
<div style="background:linear-gradient(135deg, #0a3d5c 0%, #1565C0 100%);
            color:white;padding:22px 32px;border-radius:18px;margin-bottom:20px;
            box-shadow:0 6px 28px rgba(10,61,92,0.35)">
    <div style="display:flex;align-items:center;gap:18px">
        <div style="font-size:2.8em;line-height:1">🎣</div>
        <div>
            <div style="font-size:1.55em;font-weight:800;letter-spacing:0.3px">
                悉尼钓鱼助手 Pro+
            </div>
            <div style="font-size:0.88em;opacity:0.8;margin-top:5px">
                实时海况 · 潮汐推算 · 智能推荐 &nbsp;|&nbsp; {today_str}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tab 布局（仅日期分析）────────────────────────────────────────────────
today = datetime.now()
tab_labels = [
    f"📅 今天（{today.strftime('%m/%d')}）",
    f"📅 明天（{(today + timedelta(days=1)).strftime('%m/%d')}）",
    f"📅 后天（{(today + timedelta(days=2)).strftime('%m/%d')}）",
]
tabs = st.tabs(tab_labels)

for i, tab in enumerate(tabs):
    with tab:
        render_day_tab(i)

# ── 页脚 ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#aaa;font-size:0.82em;padding:4px 0 16px">
    🚨 <b>安全提示</b>：外海矶钓请务必穿戴救生衣和防滑钉鞋，结伴同行，浪况不对立刻撤退。<br>
    天气数据来自
    <a href="https://open-meteo.com/" target="_blank" style="color:#1976D2">Open-Meteo</a>，
    潮汐为天文估算，出行前请参考
    <a href="http://www.bom.gov.au/nsw/forecasts/sydney.shtml" target="_blank"
       style="color:#1976D2">BOM 官方预报</a>。
</div>
""", unsafe_allow_html=True)
