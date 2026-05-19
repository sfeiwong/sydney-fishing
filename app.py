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

/* 展开详情 toggle — hide checkbox box, keep only the label text */
.main [data-testid="stCheckbox"] input[type="checkbox"] { display:none!important; }
.main [data-testid="stCheckbox"] label > div:not([data-testid]) { display:none!important; }
.main [data-testid="stCheckbox"] label > span { display:none!important; }
.main [data-testid="stCheckbox"] label {
    font-size:0.75em!important; color:#9ab0c2!important; cursor:pointer!important;
    padding:2px 8px!important; border-radius:6px!important;
    user-select:none!important; gap:0!important; padding-left:2px!important;
}
.main [data-testid="stCheckbox"] label:hover { color:#4a7090!important; background:#f0f5fa!important; }

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
    selected_methods = st.multiselect("钓法", ALL_METHODS, placeholder="选择钓法 · Method")
    selected_fish    = st.multiselect("目标鱼种", ALL_FISH, placeholder="选择鱼种 · Species")
    selected_region  = st.selectbox("区域", ["全部 · All Sydney", "内湾", "外海", "北区", "东区", "南区"])
    safe_only        = st.checkbox("隐藏危险钓点 ⚠", value=False)

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


def _parse_tag(tag: str) -> tuple:
    m = re.match(r'^(.+?)\s*[(\（](.+?)[)\）]$', tag.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return tag, ""


def spot_matches(spot: dict) -> bool:
    if selected_methods and not any(m in spot["supported_methods"] for m in selected_methods):
        return False
    if selected_fish and not any(f in spot["fish_tags"] for f in selected_fish):
        return False
    if selected_region and selected_region != "全部 · All Sydney":
        key = selected_region.split(" · ")[0] if " · " in selected_region else selected_region
        if key not in spot["region"]:
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
            "color":  "coral",
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
            "color":  "amber",
            "advice": (
                f"风速偏大（{wind}km/h），内湾虽可避浪，但顶风抛投体感较差，"
                "建议选背风位或大桥底部作钓。"
            ),
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

def render_weather_panel(day_weather: dict, data_ok: bool) -> None:
    if not data_ok:
        st.warning("⚠️ 天气数据加载失败，以下为估算值。")

    temp         = day_weather.get("temp") or 0
    temp_min     = day_weather.get("temp_min") or 0
    wind         = day_weather.get("wind") or 0
    wave         = day_weather.get("wave") or 0
    swell        = day_weather.get("swell_height") or 0
    rain_prob    = day_weather.get("rain_prob") or 0
    precipitation= day_weather.get("precipitation") or 0
    swell_dir    = day_weather.get("swell_direction", "—")
    swell_period = day_weather.get("swell_period", "—")

    def _tone(v, warn, danger):
        if v >= danger: return "metric-coral"
        if v >= warn:   return "metric-amber"
        return "metric-sage"

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.markdown('<div class="metric-sage">', unsafe_allow_html=True)
        st.metric("最高气温 · High temp", f"{temp} °C")
        st.markdown('</div>', unsafe_allow_html=True)
    with r1c2:
        st.markdown('<div class="metric-blue">', unsafe_allow_html=True)
        st.metric("最低气温 · Low temp", f"{temp_min} °C")
        st.markdown('</div>', unsafe_allow_html=True)
    with r1c3:
        tone = "metric-coral" if rain_prob >= 60 else ("metric-amber" if rain_prob >= 25 else "metric-sage")
        st.markdown(f'<div class="{tone}">', unsafe_allow_html=True)
        st.metric("降雨概率 · Rain prob", f"{int(rain_prob)} %")
        st.markdown('</div>', unsafe_allow_html=True)

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        st.markdown(f'<div class="{_tone(wind, SHELTERED_WIND_WARN, OCEAN_WIND_DANGER)}">', unsafe_allow_html=True)
        st.metric("最大风速 · Wind", f"{wind} km/h")
        st.markdown('</div>', unsafe_allow_html=True)
    with r2c2:
        st.markdown(f'<div class="{_tone(wave, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)}">', unsafe_allow_html=True)
        st.metric("综合浪高 · Wave", f"{wave} m")
        st.markdown('</div>', unsafe_allow_html=True)
    with r2c3:
        st.markdown(f'<div class="{_tone(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)}">', unsafe_allow_html=True)
        st.metric("浪涌高度 · Swell", f"{swell} m")
        st.markdown('</div>', unsafe_allow_html=True)

    rain_str = f"{precipitation:.1f} mm" if precipitation > 0 else "无降水"
    st.markdown(
        f'<div style="margin-top:10px;padding:10px 16px;background:var(--surface);'
        f'border-radius:10px;border:1px solid var(--line);display:flex;gap:20px;'
        f'flex-wrap:wrap;font-size:12.5px;color:var(--muted)">'
        f'<span><span style="color:var(--text);font-weight:500">预计降水</span> {rain_str}</span>'
        f'<span style="opacity:0.3">|</span>'
        f'<span><span style="color:var(--text);font-weight:500">涌向</span> {swell_dir}°</span>'
        f'<span style="opacity:0.3">|</span>'
        f'<span><span style="color:var(--text);font-weight:500">浪涌周期</span> {swell_period}s</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


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

def render_tide_panel(base_tides: list) -> None:
    now          = datetime.now()
    sorted_tides = sorted(base_tides, key=lambda x: x["time"])
    HIGH_M, LOW_M = 1.85, 0.15

    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    x_hours  = np.linspace(0, 24, 300)
    y_m      = []

    for xh in x_hours:
        t = midnight + timedelta(hours=float(xh))
        prev_td = next_td = None
        for td in sorted_tides:
            if td["time"] <= t:
                prev_td = td
            elif next_td is None:
                next_td = td
                break
        if prev_td is None:
            h = HIGH_M if sorted_tides[0]["is_high"] else LOW_M
        elif next_td is None:
            h = HIGH_M if sorted_tides[-1]["is_high"] else LOW_M
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
    if 0 <= now_h <= 24:
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
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    cols = st.columns(len(sorted_tides))
    for col, td in zip(cols, sorted_tides):
        is_high   = td["is_high"]
        dot_color = "#c69230" if is_high else "#8a9cb2"
        label     = "满潮" if is_high else "干潮"
        time_str  = td["time"].strftime("%H:%M")
        opacity   = "1" if td["time"] > now else "0.4"
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

    swell = day_weather.get("swell_height") or 0
    wind  = day_weather.get("wind") or 0
    sw_color = _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)
    wi_color = _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)
    time_window = _best_window_times(spot["best_window"], tides) if tides else "—"

    fish_html   = "".join(_pill(f, "blue") for f in spot["fish_tags"][:4])
    method_html = "".join(_pill(m, "violet") for m in spot["supported_methods"][:3])

    col.markdown(f"""
    <div style="background:white;border-radius:20px;padding:18px 20px 16px 24px;
                box-shadow:0 4px 24px rgba(24,66,112,0.10),0 1px 4px rgba(0,0,0,0.04);
                position:relative;overflow:hidden;min-height:230px;
                border:1px solid rgba(219,231,242,0.8)">
        <div style="position:absolute;left:0;top:0;bottom:0;width:5px;
                    background:{bar_grad};border-radius:20px 0 0 20px"></div>
        <div style="font-weight:800;font-size:1.0em;color:#102338;
                    line-height:1.35;margin-bottom:8px">{spot['name']}</div>
        <span style="background:{badge_bg};color:{border};padding:3px 12px;
                     border-radius:999px;font-size:0.78em;font-weight:700">
            {safety['status']}
        </span>
        <div style="color:#60758a;font-size:0.78em;margin:8px 0 10px">
            📍 {spot['region']} &nbsp;·&nbsp; {spot['type']}
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:12px">
            <div style="background:#f7fafc;border-radius:12px;padding:8px 10px;border:1px solid #edf3f8">
                <div style="color:#8fa3b1;font-size:0.66em;margin-bottom:3px">涌浪</div>
                <div style="font-size:1.05em;font-weight:800;color:{sw_color}">{swell}m</div>
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

    swell = spot_weather.get("swell_height") or 0
    wind  = spot_weather.get("wind") or 0
    sw_color    = _val_color(swell, SHELTERED_SWELL_WARN, OCEAN_SWELL_DANGER)
    wi_color    = _val_color(wind,  SHELTERED_WIND_WARN,  OCEAN_WIND_DANGER)
    time_window = _best_window_times(spot["best_window"], spot_tides)

    fish_chips   = "".join(_pill(f, "blue") for f in spot["fish_tags"])
    method_chips = "".join(_pill(m, "violet") for m in spot["supported_methods"][:5])

    st.markdown(f"""
    <div style="position:relative;background:white;border-radius:16px;
                box-shadow:0 2px 14px rgba(24,66,112,0.07),0 1px 3px rgba(0,0,0,0.04);
                border:1px solid rgba(219,231,242,0.85);
                margin-bottom:4px;padding:16px 18px 14px 24px;overflow:hidden">
        <div style="position:absolute;left:0;top:0;bottom:0;width:5px;
                    background:{bar_grad};border-radius:16px 0 0 16px"></div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap">
            <div style="font-size:1.02em;font-weight:800;color:#102338">{spot['name']}</div>
            <span style="background:{badge_bg};color:{badge_txt};border:1px solid {border};
                         padding:2px 10px;border-radius:999px;font-size:0.76em;font-weight:700">
                {safety['status']}
            </span>
            <span style="color:#9ab0c0;font-size:0.78em">{spot['region']} · {spot['type']}</span>
        </div>
        <div style="display:flex;gap:10px;margin-bottom:10px;flex-wrap:wrap">
            <div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:76px">
                <div style="font-size:0.66em;color:#bbb;margin-bottom:2px">🌊 浪涌</div>
                <div style="font-size:1.08em;font-weight:800;color:{sw_color}">{swell}m</div>
            </div>
            <div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:76px">
                <div style="font-size:0.66em;color:#bbb;margin-bottom:2px">💨 风速</div>
                <div style="font-size:1.08em;font-weight:800;color:{wi_color}">{wind}km/h</div>
            </div>
            <div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:110px">
                <div style="font-size:0.66em;color:#bbb;margin-bottom:2px">⏱️ 黄金时段</div>
                <div style="font-size:0.98em;font-weight:800;color:#1565C0">{time_window}</div>
            </div>
            <div style="background:#f4f8fc;border-radius:10px;padding:7px 14px;text-align:center;min-width:72px">
                <div style="font-size:0.66em;color:#bbb;margin-bottom:2px">👨‍👩‍👧 家庭</div>
                <div style="font-size:0.9em;font-weight:700;color:#555">{spot['family_friendly'][:2]}</div>
            </div>
        </div>
        <div style="margin-bottom:4px">{fish_chips}</div>
        <div>{method_chips}</div>
    </div>
    """, unsafe_allow_html=True)

    safe_key = (
        f"det_{day_offset}_"
        + spot["name"].replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
    )
    show_detail = st.checkbox("▾ 展开详情", key=safe_key, value=False)
    if show_detail:
        st.markdown(f"""
        <div style="background:{badge_bg};border-left:4px solid {border};
                    padding:10px 16px;border-radius:8px;margin:8px 0 12px;
                    color:{badge_txt};font-size:0.92em">
            <b>{safety['status']}</b> &nbsp;—&nbsp; {safety['advice']}
        </div>
        """, unsafe_allow_html=True)

        tides_str = " &nbsp;|&nbsp; ".join(
            f"{t['label']} `{t['time'].strftime('%H:%M')}`" for t in spot_tides
        )
        st.markdown(f"**⏰ 专属潮汐** &nbsp;{tides_str}")
        st.markdown("---")

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

    if red_n > 0:
        v2_band, v2_kicker = "var(--coral)", "DANGER SPOTS"
        v2_title, v2_body  = f"{red_n}", f"个外海点极危险 · 请勿前往"
    elif orange_n > 0:
        v2_band, v2_kicker = "var(--amber)", "CAUTION SPOTS"
        v2_title, v2_body  = f"{orange_n}", f"个点需谨慎 · 选背风位"
    else:
        v2_band, v2_kicker = "var(--sage)", "ALL CLEAR"
        v2_title, v2_body  = "0", "危险点 · 所有钓点均安全"

    sorted_tides = sorted(base_tides, key=lambda t: t["time"])
    highs        = [t for t in sorted_tides if t["is_high"]]
    if highs:
        h = highs[0]["time"]
        v3_win = f"{(h - timedelta(hours=1.5)).strftime('%H:%M')}–{(h + timedelta(hours=1.5)).strftime('%H:%M')}"
        v3_sub = f"满潮 {h.strftime('%H:%M')} 前后 1.5h"
    else:
        v3_win, v3_sub = "—", "参考各钓点潮汐"

    if green_n > 0:
        v4_text = f"今日最佳选择：优先内湾或避风点，{v3_win} 黄金时段出击，建议携带 Running Sinker 线组。"
    else:
        v4_text = f"建议等待明日或后天的预报窗口，或前往内湾避风点以极轻线组试探。"

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
    v2.markdown(_verdict_card(v2_band, v2_kicker, v2_title, v2_body,
                              f"font-family:var(--serif-en);font-size:40px;color:{v2_band}"), unsafe_allow_html=True)
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
    STATUS_COLOR = {"sage": "#c69230", "amber": "#d99540", "coral": "#cc5e54"}

    col_map, col_detail = st.columns([3, 2])

    with col_map:
        m = folium.Map(
            location=[-33.86, 151.22], zoom_start=11,
            tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
            attr="© OpenStreetMap · CARTO",
        )

        for spot, safety, _, _ in all_spot_data:
            color = STATUS_COLOR.get(safety["color"], "#8a9cb2")
            folium.CircleMarker(
                location=[spot["lat"], spot["lon"]],
                radius=7, color="#ffffff", weight=1.5,
                fill=True, fill_color=color, fill_opacity=1.0,
                tooltip=spot["name"],
                popup=spot["name"],
            ).add_to(m)

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
    base_tides = get_tides_for_date(target_date)

    section_head("OVERALL CONDITIONS · SYDNEY", "悉尼整体海况", "Open-Meteo · 缓存 1 小时")
    left_col, right_col = st.columns([1.6, 1])
    with left_col:
        render_weather_panel(day_w, overview_weather["success"])
    with right_col:
        with st.container(border=True):
            st.markdown(
                '<div style="font-family:var(--mono);font-size:11px;letter-spacing:2px;'
                'color:var(--subtle);text-transform:uppercase;margin-bottom:6px">'
                '基准潮汐</div>'
                '<div style="font-family:var(--serif-zh);font-size:18px;font-weight:600;'
                'margin-bottom:8px">今日潮汐 '
                '<span style="font-family:var(--serif-en);font-style:italic;color:var(--muted);'
                'font-size:15px;font-weight:400">Tide curve</span></div>',
                unsafe_allow_html=True,
            )
            render_tide_panel(base_tides)

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    filtered = [s for s in spots if spot_matches(s)]
    all_spot_data = []
    for spot in filtered:
        forecast   = get_marine_forecast(spot["lat"], spot["lon"])
        spot_day_w = forecast["days"][day_offset]
        safety     = assess_safety(spot, spot_day_w)
        tides      = get_tides_for_date(target_date, spot["tide_delay"])
        all_spot_data.append((spot, safety, tides, spot_day_w))

    section_head(f"{label.upper()} · GO / NO-GO", f"{label}出钓决策", "根据实时海况自动生成")
    render_decision_panel(all_spot_data, day_w, base_tides, label)

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    top_safe = [(s, sa, ti, sw) for s, sa, ti, sw in all_spot_data if sa["safe"] and sa["color"] == "sage"]
    section_head(f"TOP PICK · {label.upper()}", f"{label}精选推荐", "海况 × 潮汐综合评分最优")
    if top_safe:
        top3 = top_safe[:3]
        cols = st.columns(len(top3))
        for col, (spot, safety, tides, dw) in zip(cols, top3):
            render_hero_card(col, spot, safety, dw, tides)
    else:
        st.markdown(
            '<div style="background:linear-gradient(90deg,#fbf3e1 0%,#fdf8eb 60%,#fff 100%);'
            'border-radius:14px;padding:20px 24px;border:1px solid #f0e3c0;'
            'border-left:4px solid var(--gold)">'
            '<div style="font-family:var(--serif-zh);font-size:17px;font-weight:600;margin-bottom:6px">'
            f'今日海况不佳，暂无满分推荐点</div>'
            '<div style="font-size:13px;color:var(--muted);line-height:1.55">'
            '涌浪或风速超出安全阈值。调整侧边栏筛选条件、改去内湾试试手气。</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    section_head("MAP · 30 SPOTS", "钓点地图", "点击标记查看详情")
    render_map_section(day_offset, all_spot_data)

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    section_head(
        f"MATCHED SPOTS · {len(filtered)} / {len(spots)}",
        "匹配钓点", "按今日海况评分排序"
    )
    visible = 0
    for spot, safety, spot_tides, spot_day_w in all_spot_data:
        if safe_only and not safety["safe"]:
            continue
        render_spot_card(spot, safety, spot_tides, spot_day_w, day_offset)
        visible += 1
    if visible == 0:
        st.info("ℹ️ 当前筛选条件下没有匹配的钓点，请尝试减少筛选条件。")


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
