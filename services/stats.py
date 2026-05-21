# ============================================================
# services/stats.py — 用户访问信息统计服务 (SQLite版)
# ============================================================

import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import streamlit as st
import plotly.graph_objects as go


SYD_TZ = ZoneInfo("Australia/Sydney")
DB_PATH = Path(__file__).parent.parent / "data" / "stats.db"

# Session state keys
_SESSION_KEY_ID = "stats_session_id"
_SESSION_KEY_RECORD_ID = "stats_visit_record_id"
_SESSION_KEY_START_TIME = "stats_visit_start_time"


def _init_db():
    """初始化数据库（模块加载时调用一次）"""
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                visit_date DATE,
                start_time DATETIME,
                end_time DATETIME,
                duration_seconds INTEGER,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')


# 模块加载时初始化数据库
_init_db()


@contextmanager
def _db_cursor():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def _query_scalar(sql: str, params: tuple = ()):
    """执行标量查询并返回结果"""
    with _db_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()[0]


def get_or_create_session_id() -> str:
    """获取或创建会话ID"""
    if _SESSION_KEY_ID not in st.session_state:
        st.session_state[_SESSION_KEY_ID] = str(uuid.uuid4())
    return st.session_state[_SESSION_KEY_ID]


def record_visit_start():
    """记录访问开始"""
    if _SESSION_KEY_RECORD_ID in st.session_state:
        return
    
    session_id = get_or_create_session_id()
    now = datetime.now(SYD_TZ)
    user_agent = getattr(st.context, "headers", {}).get("User-Agent", "")
    
    with _db_cursor() as cursor:
        cursor.execute('''
            INSERT INTO visits (session_id, visit_date, start_time, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (session_id, now.date().isoformat(), now.isoformat(), user_agent))
        
        st.session_state[_SESSION_KEY_RECORD_ID] = cursor.lastrowid
        st.session_state[_SESSION_KEY_START_TIME] = now


def record_visit_end():
    """记录访问结束"""
    record_id = st.session_state.get(_SESSION_KEY_RECORD_ID)
    start_time = st.session_state.get(_SESSION_KEY_START_TIME)
    
    if record_id is None or start_time is None:
        return
    
    now = datetime.now(SYD_TZ)
    duration = int((now - start_time).total_seconds())
    
    with _db_cursor() as cursor:
        cursor.execute('''
            UPDATE visits 
            SET end_time = ?, duration_seconds = ?
            WHERE id = ?
        ''', (now.isoformat(), duration, record_id))


def get_daily_visits(date_str: str = None) -> int:
    """获取指定日期的访问量"""
    if date_str is None:
        date_str = datetime.now(SYD_TZ).date().isoformat()
    
    result = _query_scalar('''
        SELECT COUNT(DISTINCT session_id) 
        FROM visits 
        WHERE visit_date = ?
    ''', (date_str,))
    
    return result or 0


def get_average_duration(days: int = 1) -> float:
    """获取最近N天的平均使用时长（秒）"""
    start_date = (datetime.now(SYD_TZ) - timedelta(days=days)).date().isoformat()
    
    result = _query_scalar('''
        SELECT AVG(duration_seconds) 
        FROM visits 
        WHERE visit_date >= ? AND duration_seconds IS NOT NULL
    ''', (start_date,))
    
    return round(result, 1) if result else 0.0


def get_total_visitors() -> int:
    """获取总访客数"""
    result = _query_scalar('SELECT COUNT(DISTINCT session_id) FROM visits')
    return result or 0


def get_weekly_stats() -> dict:
    """获取最近7天的统计数据"""
    today = datetime.now(SYD_TZ)
    start_date = (today - timedelta(days=6)).date().isoformat()
    
    with _db_cursor() as cursor:
        cursor.execute('''
            SELECT visit_date, COUNT(DISTINCT session_id), AVG(duration_seconds)
            FROM visits 
            WHERE visit_date >= ?
            GROUP BY visit_date
            ORDER BY visit_date DESC
        ''', (start_date,))
        
        db_data = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    
    weekly_data = {}
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.date().isoformat()
        visits, avg_duration = db_data.get(date_str, (0, None))
        weekly_data[date_str] = {
            "visits": visits,
            "avg_duration": round(avg_duration, 1) if avg_duration else 0.0,
        }
    
    return weekly_data


def format_duration(seconds: float) -> str:
    """格式化时长显示"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}分钟"
    else:
        return f"{seconds / 3600:.1f}小时"


@st.cache_data(ttl=300)
def _get_cached_stats():
    """缓存统计数据（5分钟）"""
    today = datetime.now(SYD_TZ).date().isoformat()
    return {
        "daily_visits": get_daily_visits(today),
        "avg_duration": get_average_duration(days=1),
        "total_visitors": get_total_visitors(),
        "weekly_stats": get_weekly_stats(),
    }


def render_stats_panel():
    """渲染统计面板"""
    st.markdown("---")
    st.markdown("## 📊 访问统计")
    
    stats = _get_cached_stats()
    weekly_stats = stats["weekly_stats"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="今日访问量",
            value=str(stats["daily_visits"]),
            help="今日独立访客数"
        )
    
    with col2:
        st.metric(
            label="今日平均使用时长",
            value=format_duration(stats["avg_duration"]),
            help="今日用户的平均使用时长"
        )
    
    with col3:
        st.metric(
            label="总访客数",
            value=str(stats["total_visitors"]),
            help="累计访客数"
        )
    
    st.markdown("### 📈 最近7天趋势")
    
    dates = list(weekly_stats.keys())[::-1]
    visits = [weekly_stats[d]["visits"] for d in dates]
    durations = [weekly_stats[d]["avg_duration"] for d in dates]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=visits, name="访问量", yaxis="y", marker_color="#2a5fb0"))
    fig.add_trace(go.Scatter(x=dates, y=durations, name="平均时长（秒）", yaxis="y2", line=dict(color="#c69230", width=3)))
    
    fig.update_layout(
        title="访问趋势",
        xaxis_title="日期",
        yaxis=dict(title="访问量", side="left"),
        yaxis2=dict(title="平均时长（秒）", side="right", overlaying="y"),
        legend=dict(x=0.05, y=0.95),
        height=400,
    )
    
    st.plotly_chart(fig, use_container_width=True)
