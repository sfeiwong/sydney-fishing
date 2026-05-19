# ============================================================
# app.py — 悉尼钓鱼助手 Pro+ 主程序
# ============================================================

import streamlit as st
from datetime import datetime, timedelta

import folium
from streamlit_folium import st_folium

from config import (
    ALL_METHODS, ALL_FISH,
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

    temp  = day_weather.get("temp") or 0
    wind  = day_weather.get("wind") or 0
    wave  = day_weather.get("wave") or 0
    swell = day_weather.get("swell_height") or 0
    swell_dir    = day_weather.get("swell_direction", "—")
    swell_period = day_weather.get("swell_period", "—")

    metrics = [
        ("🌡️", "最高气温", temp,  "°C",   "#1976D2"),
        ("💨", "最大风速", wind,  "km/h", _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)),
        ("🌊", "综合浪高", wave,  "m",    _val_color(wave,  SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)),
        ("🌀", "浪涌高度", swell, "m",    _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)),
    ]

    cols = st.columns(4)
    for col, (icon, label, val, unit, color) in zip(cols, metrics):
        col.markdown(f"""
        <div style="background:white;border-radius:14px;padding:18px 10px 14px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.07);text-align:center;
                    border-bottom:3px solid {color}">
            <div style="font-size:1.5em;line-height:1">{icon}</div>
            <div style="color:#999;font-size:0.8em;margin:7px 0 4px">{label}</div>
            <div style="font-size:1.75em;font-weight:800;color:{color};line-height:1.1">{val}</div>
            <div style="color:#bbb;font-size:0.78em;margin-top:4px">{unit}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;color:#666;font-size:0.88em;margin-top:12px;
                background:white;border-radius:10px;padding:9px 16px;
                box-shadow:0 1px 6px rgba(0,0,0,0.05)">
        🧭&nbsp; 涌向 <b>{swell_dir}°</b> &nbsp;&nbsp;|&nbsp;&nbsp; ⏱️&nbsp; 浪涌周期 <b>{swell_period}s</b>
    </div>
    """, unsafe_allow_html=True)


# ── 潮汐时间线 ────────────────────────────────────────────────────────────

def render_tide_panel(base_tides: list) -> None:
    now   = datetime.now()
    times = [t["time"] for t in base_tides]
    min_t = min(times)
    max_t = max(times)
    span  = (max_t - min_t).total_seconds()

    def to_pct(t: datetime) -> float:
        return max(2, min(98, (t - min_t).total_seconds() / span * 100)) if span > 0 else 50

    dots_html = ""
    for t in base_tides:
        pct     = to_pct(t["time"])
        is_high = t["is_high"]
        color   = "#1565C0" if is_high else "#EF6C00"
        label   = "满潮" if is_high else "干潮"
        size    = "16px" if is_high else "11px"
        dots_html += f"""
        <div style="position:absolute;left:{pct:.1f}%;transform:translateX(-50%);
                    top:0;text-align:center;width:64px;margin-left:-32px">
            <div style="font-size:0.72em;color:{color};font-weight:700;
                        white-space:nowrap">{t['time'].strftime('%H:%M')}</div>
            <div style="width:{size};height:{size};background:{color};border-radius:50%;
                        margin:4px auto;box-shadow:0 2px 8px rgba(0,0,0,0.18)"></div>
            <div style="font-size:0.68em;color:#888;white-space:nowrap">{label}</div>
        </div>
        """

    now_html = ""
    if min_t <= now <= max_t:
        pct = to_pct(now)
        now_html = f"""
        <div style="position:absolute;left:{pct:.1f}%;transform:translateX(-50%);top:-18px;
                    font-size:0.65em;color:#e53935;font-weight:700;white-space:nowrap">▼ 现在</div>
        <div style="position:absolute;left:{pct:.1f}%;transform:translateX(-50%);
                    top:-4px;bottom:-4px;width:2px;
                    background:linear-gradient(#e53935,rgba(229,57,53,0.2));border-radius:2px"></div>
        """

    st.markdown(f"""
    <div style="background:white;border-radius:14px;padding:16px 20px 22px;
                box-shadow:0 2px 12px rgba(0,0,0,0.07)">
        <div style="font-size:0.78em;color:#bbb;margin-bottom:18px">
            ⏰ Fort Denison 基准 &nbsp;·&nbsp; ±30~60 分钟误差
        </div>
        <div style="position:relative;height:76px;margin:0 24px">
            <div style="position:absolute;top:28px;left:0;right:0;height:2px;
                        background:#e8eef5;border-radius:2px"></div>
            {now_html}
            {dots_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


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

            fish_html = "".join(
                f'<span style="background:#e3f2fd;color:#1565c0;padding:3px 10px;'
                f'border-radius:12px;font-size:0.8em;margin:2px;display:inline-block">{f}</span>'
                for f in spot["fish_tags"]
            )
            st.markdown(f"**🐟 目标鱼种** &nbsp;{fish_html}", unsafe_allow_html=True)

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

    # 精选推荐区（绿色安全钓点，最多展示 3 个）
    top_safe = [
        (s, sa, sw)
        for s, sa, ti, sw in all_spot_data
        if sa["safe"] and sa["color"] == "green"
    ]
    if top_safe:
        label = "今天" if day_offset == 0 else ("明天" if day_offset == 1 else "后天")
        st.markdown(f"### 🏆 {label}精选推荐")
        top3 = top_safe[:3]
        cols = st.columns(len(top3))
        for col, (spot, safety, dw) in zip(cols, top3):
            render_hero_card(col, spot, safety, dw)
        st.markdown("")

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


# ── 地图 Tab ──────────────────────────────────────────────────────────────

def render_map_tab() -> None:
    st.subheader("🗺️ 悉尼钓点地图总览（今日安全评估）")
    st.caption("🟢 推荐 &nbsp; 🟠 谨慎 &nbsp; 🔴 危险/不建议 &nbsp;（点击标记查看钓点简介）")

    m = folium.Map(
        location=[-33.87, 151.21],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    for spot in spots:
        if not spot_matches(spot):
            continue
        w      = get_marine_forecast(spot["lat"], spot["lon"])
        safety = assess_safety(spot, w["days"][0])

        popup_html = (
            f"<b>{spot['name']}</b><br>"
            f"{safety['status']}<br>"
            f"🐟 {spot['active_fish']}<br>"
            f"⏱️ {spot['best_window']}"
        )
        folium.Marker(
            location=[spot["lat"], spot["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{spot['name']} ({safety['status']})",
            icon=folium.Icon(color=safety["color"], icon="info-sign"),
        ).add_to(m)

    st_folium(m, width=None, height=620, returned_objects=[])


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

# ── Tab 布局 ──────────────────────────────────────────────────────────────
today = datetime.now()
tab_labels = [
    f"📅 今天（{today.strftime('%m/%d')}）",
    f"📅 明天（{(today + timedelta(days=1)).strftime('%m/%d')}）",
    f"📅 后天（{(today + timedelta(days=2)).strftime('%m/%d')}）",
    "🗺️ 地图总览",
]
tabs = st.tabs(tab_labels)

for i, tab in enumerate(tabs[:3]):
    with tab:
        render_day_tab(i)

with tabs[3]:
    render_map_tab()

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
