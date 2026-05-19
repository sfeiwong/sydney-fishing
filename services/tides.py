# ============================================================
# services/tides.py — 潮汐推算服务
# ============================================================
# 当前实现：天文近似算法（基于 Fort Denison 参考满潮 + 月球漂移）
# 精度：±30~60 分钟，适合参考决策，不适合精确卡点。
#
# 升级建议（生产环境）：
#   方案 A（免费）：每日抓取 BOM 官方潮汐表
#                   http://www.bom.gov.au/oceanography/tides/
#   方案 B（付费）：WorldTides API，精度 ±5 分钟
#                   https://www.worldtides.info/api
# ============================================================

from datetime import datetime, timedelta
from config import (
    TIDE_REF_YEAR, TIDE_REF_MONTH, TIDE_REF_DAY,
    TIDE_REF_HOUR, TIDE_REF_MINUTE,
    SEMI_DIURNAL_MINUTES, LUNAR_DRIFT_PER_DAY,
)

_REFERENCE_HIGH = datetime(
    TIDE_REF_YEAR, TIDE_REF_MONTH, TIDE_REF_DAY,
    TIDE_REF_HOUR, TIDE_REF_MINUTE,
)


def get_tides_for_date(target_date: datetime, delay_minutes: int = 0) -> list[dict]:
    """
    推算某天的 4 个潮汐事件（2 满潮 + 2 干潮）。

    参数：
        target_date    — 目标日期
        delay_minutes  — 相对 Fort Denison 的时间偏差（钓点专属，可正可负）

    返回：list of dict，每项包含：
        time     — datetime 对象
        is_high  — bool，True 为满潮
        label    — 显示用中文标签（含 emoji）
    """
    days_since_ref = (target_date.date() - _REFERENCE_HIGH.date()).days
    total_drift = timedelta(minutes=days_since_ref * LUNAR_DRIFT_PER_DAY + delay_minutes)

    # 计算当天第一个满潮的基准时间
    base = _REFERENCE_HIGH + total_drift
    base = base.replace(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
    )

    tides = []
    for i in range(4):
        t = base + timedelta(minutes=i * SEMI_DIURNAL_MINUTES)
        is_high = (i % 2 == 0)
        tides.append({
            "time":    t,
            "is_high": is_high,
            "label":   "🟢 满潮" if is_high else "🔵 干潮",
        })
    return tides
