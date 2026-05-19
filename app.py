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

# ── 页面配置 ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="悉尼钓鱼助手 Pro+",
    page_icon="🎣",
    layout="wide",
)

# ── 加载钓点数据 ─────────────────────────────────────────────────────────
spots = load_spots()

# ── 侧边栏：筛选器 ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎣 悉尼钓鱼助手")
    st.markdown("---")
    st.header("🔍 智能筛选")
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
    safe_only = st.checkbox("⚠️ 隐藏今天的危险钓点", value=False)
    st.markdown("---")
    st.caption(
        "📡 天气：Open-Meteo（缓存1小时）\n\n"
        "🌊 海况：按钓点坐标分区获取\n\n"
        "⏰ 潮汐：天文近似推算（±30-60分钟）\n\n"
        "升级精度 → [WorldTides API](https://www.worldtides.info/api)"
    )


# ── 工具函数 ────────────────────────────────────────────────────────────

def spot_matches(spot: dict) -> bool:
    """检查钓点是否满足当前筛选条件。"""
    if selected_methods and not any(m in spot["supported_methods"] for m in selected_methods):
        return False
    if selected_fish and not any(f in spot["fish_tags"] for f in selected_fish):
        return False
    return True


def assess_safety(spot: dict, day_weather: dict) -> dict:
    """
    根据当天天气评估钓点安全性。
    返回含 status / score / safe / advice / color 的字典。
    """
    swell = day_weather["swell_height"]
    wind  = day_weather["wind"]

    if not spot["sheltered"] and (swell > OCEAN_SWELL_DANGER or wind > OCEAN_WIND_DANGER):
        return {
            "status": "❌ 极度危险",
            "score":  "⭐",
            "safe":   False,
            "color":  "red",
            "advice": (
                f"🚨 外海浪涌预计 **{swell}m**，风速 **{wind}km/h**，"
                "该点属于完全暴露的外海地形，极其危险！请立刻转移到内湾避风钓点。"
            ),
        }
    if spot["sheltered"] and (swell > SHELTERED_SWELL_WARN or wind > SHELTERED_WIND_WARN):
        return {
            "status": "⚠️ 谨慎前往",
            "score":  "⭐⭐⭐",
            "safe":   True,
            "color":  "orange",
            "advice": (
                f"风速偏大（**{wind}km/h**），内湾虽可避浪，但顶风抛投体感较差，"
                "建议选背风位或大桥底部作钓。"
            ),
        }
    return {
        "status": "✅ 极力推荐",
        "score":  "⭐⭐⭐⭐⭐",
        "safe":   True,
        "color":  "green",
        "advice": "此日海况温和，非常符合出击条件，祝大鲫大鲈！🎉",
    }


def render_weather_panel(day_weather: dict, data_ok: bool) -> None:
    """渲染顶部天气概览面板。"""
    if not data_ok:
        st.warning(
            "⚠️ **天气数据加载失败**，以下显示估算值，仅供参考，出行前请以 BOM 官方预报为准。",
            icon="🛰️",
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ 最高气温",   f"{day_weather['temp']} °C")
    c2.metric("💨 最大风速",   f"{day_weather['wind']} km/h")
    c3.metric("🌊 综合浪高",   f"{day_weather['wave']} m")
    c4.metric("🌀 浪涌高度",   f"{day_weather['swell_height']} m")

    st.markdown(
        f"> **浪涌周期** `{day_weather['swell_period']}s` "
        f"&nbsp;|&nbsp; **涌向** `{day_weather['swell_direction']}°`"
    )


def render_tide_panel(base_tides: list) -> None:
    """渲染 Fort Denison 基准潮汐面板。"""
    cols = st.columns(4)
    for i, (col, t) in enumerate(zip(cols, base_tides)):
        with col:
            st.metric(
                label=t["label"],
                value=t["time"].strftime("%H:%M"),
            )
    st.caption("⏰ 以上为 Fort Denison 基准近似值（±30-60分钟），仅供参考。")


def render_spot_card(spot: dict, safety: dict, spot_tides: list, spot_weather: dict, day_offset: int) -> None:
    """渲染单个钓点的展开卡片。"""
    title = f"{safety['score']} &nbsp; {spot['name']} &nbsp;—&nbsp; {safety['status']}"
    with st.expander(title):
        left, right = st.columns([1.2, 0.8])

        with left:
            st.markdown(f"**🌍 区域** &nbsp; `{spot['region']}`")
            st.markdown(f"**📍 地形** &nbsp; `{spot['type']}`")
            st.markdown(f"**🐟 活跃鱼种** &nbsp; {spot['active_fish']}")
            st.markdown(f"**⏱️ 最佳窗口** &nbsp; {spot['best_window']}")

            tides_str = " &nbsp;|&nbsp; ".join(
                f"{t['label']} `{t['time'].strftime('%H:%M')}`"
                for t in spot_tides
            )
            st.markdown(f"**⏰ 专属潮汐** &nbsp; {tides_str}")

        with right:
            st.markdown(
                f"**🌊 当地浪涌** &nbsp; `{spot_weather['swell_height']}m` "
                f"&nbsp; **风速** &nbsp; `{spot_weather['wind']}km/h`"
            )
            st.markdown(f"**👨‍👩‍👧‍👦 家庭友好度**\n\n{spot['family_friendly']}")

        st.markdown("---")
        st.markdown("**💡 实战战术建议**")
        show_methods = (
            [m for m in selected_methods if m in spot["supported_methods"]]
            if selected_methods else spot["supported_methods"]
        )
        for method in show_methods:
            tip = spot["method_tips"].get(
                method,
                "此钓法在该钓点完全可行，建议现场根据流水微调线组铅重。"
            )
            st.markdown(f"> **{method}**：{tip}")

        st.markdown("---")
        st.markdown(f"**🚗 自驾路线** &nbsp; {spot['route']}")
        st.info(f"**🅿️ 停车方案** &nbsp; {spot['parking']}")
        st.warning(f"**⚠️ 海况安全提示** &nbsp; {safety['advice']}")


# ── 主 Tab 渲染：按日期 ──────────────────────────────────────────────────

def render_day_tab(day_offset: int) -> None:
    target_date = datetime.now() + timedelta(days=day_offset)

    # 悉尼 CBD 天气作为整体概览（坐标取整后与北部海岸外海区域共用缓存）
    overview_weather = get_marine_forecast(-33.8688, 151.2093)
    day_w = overview_weather["days"][day_offset]
    base_tides = get_tides_for_date(target_date)

    col_weather, col_tides = st.columns([1.3, 0.7])
    with col_weather:
        st.subheader("🌊 悉尼整体海况")
        render_weather_panel(day_w, overview_weather["success"])
    with col_tides:
        st.subheader("📅 Fort Denison 基准潮汐")
        render_tide_panel(base_tides)

    st.markdown("---")

    # 筛选后的钓点列表
    filtered = [s for s in spots if spot_matches(s)]
    st.subheader(f"📍 匹配钓点（{len(filtered)} / {len(spots)} 个）")

    visible = 0
    for spot in filtered:
        # 按钓点坐标获取当地天气（相同区域命中缓存，不额外发起请求）
        spot_forecast = get_marine_forecast(spot["lat"], spot["lon"])
        spot_day_w    = spot_forecast["days"][day_offset]
        safety        = assess_safety(spot, spot_day_w)

        if safe_only and not safety["safe"]:
            continue

        spot_tides = get_tides_for_date(target_date, spot["tide_delay"])
        render_spot_card(spot, safety, spot_tides, spot_day_w, day_offset)
        visible += 1

    if visible == 0:
        st.info("ℹ️ 当前筛选条件下没有匹配的钓点，请尝试减少筛选条件。")


# ── 地图 Tab ─────────────────────────────────────────────────────────────

def render_map_tab() -> None:
    st.subheader("🗺️ 悉尼钓点地图总览（今日安全评估）")
    st.caption("🟢 推荐 &nbsp; 🟠 谨慎 &nbsp; 🔴 危险/不建议 &nbsp;（点击标记查看钓点简介）")

    m = folium.Map(
        location=[-33.87, 151.21],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    today_offset = 0
    for spot in spots:
        if not spot_matches(spot):
            continue

        w      = get_marine_forecast(spot["lat"], spot["lon"])
        safety = assess_safety(spot, w["days"][today_offset])

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


# ── 页面标题 ─────────────────────────────────────────────────────────────
st.title("🎣 悉尼钓鱼助手 Pro+")
st.markdown("---")

# ── Tab 布局 ─────────────────────────────────────────────────────────────
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

# ── 页脚 ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "🚨 **安全提示**：外海矶钓请务必穿戴救生衣和防滑钉鞋，结伴同行，浪况不对立刻撤退。"
    "天气数据来自 Open-Meteo，潮汐为天文估算，出行前请参考 "
    "[BOM 官方预报](http://www.bom.gov.au/nsw/forecasts/sydney.shtml)。"
)
