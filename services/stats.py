# ============================================================
# services/stats.py — 用户访问信息统计服务 (SQLite版)
# ============================================================

import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import streamlit as st


SYD_TZ = ZoneInfo("Australia/Sydney")
DB_PATH = Path(__file__).parent.parent / "data" / "stats.db"


def _init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
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
    
    conn.commit()
    conn.close()


def _get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def get_or_create_session_id() -> str:
    """获取或创建会话ID"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def record_visit_start():
    """记录访问开始"""
    _init_db()
    
    session_id = get_or_create_session_id()
    now = datetime.now(SYD_TZ)
    
    # 检查这次会话是否已经记录过开始
    if "visit_recorded" not in st.session_state:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        # 插入访问记录
        cursor.execute('''
            INSERT INTO visits (session_id, visit_date, start_time, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (
            session_id,
            now.date().isoformat(),
            now.isoformat(),
            st.context.headers.get("User-Agent", "") if hasattr(st.context, "headers") else ""
        ))
        
        st.session_state.visit_record_id = cursor.lastrowid
        st.session_state.visit_recorded = True
        st.session_state.visit_start_time = now
        
        conn.commit()
        conn.close()


def record_visit_end():
    """记录访问结束"""
    if "visit_record_id" in st.session_state and "visit_start_time" in st.session_state:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now(SYD_TZ)
        duration = int((now - st.session_state.visit_start_time).total_seconds())
        
        cursor.execute('''
            UPDATE visits 
            SET end_time = ?, duration_seconds = ?
            WHERE id = ?
        ''', (now.isoformat(), duration, st.session_state.visit_record_id))
        
        conn.commit()
        conn.close()


def get_daily_visits(date_str: str = None) -> int:
    """获取指定日期的访问量"""
    _init_db()
    
    if date_str is None:
        date_str = datetime.now(SYD_TZ).date().isoformat()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(DISTINCT session_id) 
        FROM visits 
        WHERE visit_date = ?
    ''', (date_str,))
    
    result = cursor.fetchone()[0]
    conn.close()
    
    return result


def get_average_duration(days: int = 1) -> float:
    """获取最近N天的平均使用时长（秒）"""
    _init_db()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    start_date = (datetime.now(SYD_TZ) - timedelta(days=days-1)).date().isoformat()
    
    cursor.execute('''
        SELECT AVG(duration_seconds) 
        FROM visits 
        WHERE visit_date >= ? AND duration_seconds IS NOT NULL
    ''', (start_date,))
    
    result = cursor.fetchone()[0]
    conn.close()
    
    return round(result, 1) if result else 0.0


def get_total_visitors() -> int:
    """获取总访客数"""
    _init_db()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(DISTINCT session_id) FROM visits')
    result = cursor.fetchone()[0]
    conn.close()
    
    return result


def get_weekly_stats() -> dict:
    """获取最近7天的统计数据"""
    _init_db()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now(SYD_TZ)
    weekly_data = {}
    
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.date().isoformat()
        
        cursor.execute('''
            SELECT COUNT(DISTINCT session_id), AVG(duration_seconds)
            FROM visits 
            WHERE visit_date = ?
        ''', (date_str,))
        
        visits, avg_duration = cursor.fetchone()
        weekly_data[date_str] = {
            "visits": visits or 0,
            "avg_duration": round(avg_duration, 1) if avg_duration else 0.0,
        }
    
    conn.close()
    return weekly_data


def format_duration(seconds: float) -> str:
    """格式化时长显示"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def render_stats_panel():
    """渲染统计面板"""
    st.markdown("---")
    st.markdown("## 📊 访问统计")
    
    today = datetime.now(SYD_TZ).date().isoformat()
    weekly_stats = get_weekly_stats()
    
    # 今日统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="今日访问量",
            value=str(get_daily_visits(today)),
            help="今日独立访客数"
        )
    
    with col2:
        avg_duration = get_average_duration(days=1)
        st.metric(
            label="今日平均使用时长",
            value=format_duration(avg_duration),
            help="今日用户的平均使用时长"
        )
    
    with col3:
        st.metric(
            label="总访客数",
            value=str(get_total_visitors()),
            help="累计访客数"
        )
    
    # 最近7天趋势
    st.markdown("### 📈 最近7天趋势")
    
    dates = list(weekly_stats.keys())
    visits = [weekly_stats[d]["visits"] for d in dates]
    durations = [weekly_stats[d]["avg_duration"] for d in dates]
    
    dates = dates[::-1]
    visits = visits[::-1]
    durations = durations[::-1]
    
    import plotly.graph_objects as go
    
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
