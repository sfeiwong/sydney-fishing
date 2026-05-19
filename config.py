# ============================================================
# config.py — 全局常量与阈值配置
# ============================================================

# 安全阈值
OCEAN_SWELL_DANGER   = 1.3   # 外海钓点危险浪涌高度（米）
OCEAN_WIND_DANGER    = 20    # 外海钓点危险风速（km/h）
SHELTERED_SWELL_WARN = 1.4   # 内湾钓点预警浪涌高度（米）
SHELTERED_WIND_WARN  = 22    # 内湾钓点预警风速（km/h）

# 天气 API 缓存刷新间隔（秒）
WEATHER_CACHE_TTL = 3600  # 1 小时

# 潮汐推算参数（Fort Denison 基准，天文近似）
# 生产环境建议替换为 WorldTides API 或 BOM 潮汐数据
TIDE_REF_YEAR   = 2026
TIDE_REF_MONTH  = 1
TIDE_REF_DAY    = 1
TIDE_REF_HOUR   = 6   # 06:00 AEDT 参考满潮
TIDE_REF_MINUTE = 0
SEMI_DIURNAL_MINUTES = 745  # 12h 25min（半个潮汐周期）
LUNAR_DRIFT_PER_DAY  = 50   # 每天潮汐推迟约 50 分钟

# 筛选下拉框选项
ALL_METHODS = [
    "无铅漂钓",
    "Running Sinker (活铅沉底)",
    "路亚大物",
    "木虾抽鱿鱼",
    "重铅沉底",
    "全游动",
    "半游动",
    "活饵放流",
]

ALL_FISH = [
    "Bream (鳊鱼)",
    "Flathead (牛鳅)",
    "Whiting (沙尖)",
    "Squid (鱿鱼)",
    "Kingfish (黄尾师)",
    "Tailor (蓝鱼)",
    "Salmon (三文鱼)",
    "Drummer (黑毛)",
    "Jewfish (皇冠鲊)",
    "Leatherjacket (剥皮鱼)",
    "Blue Groper (蓝唇鱼)",
]
