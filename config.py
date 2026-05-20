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

# 区域筛选关键词映射（纯地理分区，不与水域类型重叠）
REGION_FILTER_MAP = {
    "Northern Beaches / Manly": ["Northern Beaches", "Manly", "Narrabeen"],
    "Hawkesbury / Brooklyn":    ["Hawkesbury", "Brooklyn", "Berowra"],
    "Middle Harbour / Ku-ring-gai": ["Middle Harbour", "Ku-ring-gai"],
    "内港 Inner Harbour": ["Mosman", "North Sydney", "Walsh Bay", "Seaforth", "Woolwich",
                           "Darling Point", "Rose Bay", "Vaucluse", "Balmain",
                           "Iron Cove", "Drummoyne"],
    "南区 Southern": ["Botany Bay", "St George", "Blakehurst", "Cronulla", "Kurnell",
                      "La Perouse", "Randwick", "Royal National", "Port Hacking",
                      "Bundeena", "Sutherland Shire", "Grays Point"],
    "西区 Western": ["Penrith", "Western Sydney", "Parramatta", "Cabarita", "Ryde", "Windsor"],
}

# NSW DPI 法定最小尺寸 & 持鱼限额（total length，cm）
FISH_LEGAL_SIZE = {
    "Bream (鳊鱼)":                {"size": 25,   "bag": 20,  "note": ""},
    "Flathead (牛鳅)":             {"size": 36,   "bag": 10,  "note": "Dusky Flathead TL"},
    "Whiting (沙尖)":              {"size": 27,   "bag": 20,  "note": ""},
    "Squid (鱿鱼)":                {"size": None, "bag": None,"note": "无限制"},
    "Kingfish (黄尾师)":           {"size": 60,   "bag": 5,   "note": ""},
    "Tailor (蓝鱼)":               {"size": 30,   "bag": 20,  "note": ""},
    "Salmon (三文鱼)":             {"size": None, "bag": 20,  "note": "无最小尺寸"},
    "Drummer (黑毛)":              {"size": None, "bag": None,"note": "无限制"},
    "Jewfish (皇冠鲊)":            {"size": 45,   "bag": 2,   "note": ""},
    "Leatherjacket (剥皮鱼)":      {"size": None, "bag": None,"note": "无限制"},
    "Blue Groper (蓝唇鱼)":        {"size": None, "bag": 0,   "note": "⚠️ 受保护·禁捕"},
    "Australian Bass (澳洲鲈鱼)":  {"size": 25,   "bag": 2,   "note": ""},
    "Golden Perch (黄金鲈)":       {"size": 30,   "bag": 5,   "note": ""},
    "Carp (锦鲤)":                 {"size": None, "bag": None,"note": "有害物种·须就地处理"},
    "Catfish (鲶鱼)":              {"size": 20,   "bag": None,"note": ""},
    "Snapper (真鲷)":              {"size": 30,   "bag": 10,  "note": ""},
    "Trevally (鲹鱼)":             {"size": None, "bag": 20,  "note": "无最小尺寸"},
    "Bonito (鲣鱼)":               {"size": None, "bag": None,"note": "无限制"},
    "Mackerel (鲭鱼)":             {"size": None, "bag": None,"note": "无限制"},
    "Tuna (金枪鱼)":               {"size": None, "bag": None,"note": "无限制"},
    "Garfish (针鱼)":              {"size": None, "bag": 40,  "note": "无最小尺寸"},
}

# 鱼种烹饪建议（按家庭实用口味）
FISH_COOKING = {
    "Bream (鳊鱼)": "清蒸 / 盐烤整鱼",
    "Flathead (牛鳅)": "香煎鱼柳 / 炸鱼薯条",
    "Whiting (沙尖)": "薄粉酥炸 / 黄油煎",
    "Squid (鱿鱼)": "蒜香快炒 / 椒盐圈",
    "Kingfish (黄尾师)": "刺身 / 柚子胡椒炙烤",
    "Tailor (蓝鱼)": "烟熏 / 香料烤",
    "Salmon (三文鱼)": "香煎 / 味噌烤",
    "Drummer (黑毛)": "姜葱清蒸 / 红烧",
    "Jewfish (皇冠鲊)": "鱼排香煎 / 黄油烤",
    "Leatherjacket (剥皮鱼)": "奶油煎 / 清蒸",
    "Blue Groper (蓝唇鱼)": "受保护物种，不建议烹饪",
    "Australian Bass (澳洲鲈鱼)": "香煎 / 纸包烤",
    "Golden Perch (黄金鲈)": "清蒸 / 豆豉蒸",
    "Carp (锦鲤)": "不建议食用",
    "Catfish (鲶鱼)": "香煎 / 咖喱炖",
    "Snapper (真鲷)": "清蒸 / 烤箱整鱼",
    "Trevally (鲹鱼)": "刺身 / 盐烤",
    "Bonito (鲣鱼)": "炙烧 / 烟熏",
    "Mackerel (鲭鱼)": "味噌煮 / 香煎",
    "Tuna (金枪鱼)": "刺身 / 低温煎封",
    "Garfish (针鱼)": "香煎 / 炸制",
}

# 筛选下拉框选项
ALL_METHODS = [
    "无铅漂钓",
    "Running Sinker (活铅沉底)",
    "路亚大物",
    "软饵路亚 (Soft Bait)",
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
    # 淡水鱼种
    "Australian Bass (澳洲鲈鱼)",
    "Golden Perch (黄金鲈)",
    "Carp (锦鲤)",
    "Catfish (鲶鱼)",
    # 扩展常见海鱼
    "Snapper (真鲷)",
    "Trevally (鲹鱼)",
    "Bonito (鲣鱼)",
    "Mackerel (鲭鱼)",
    "Tuna (金枪鱼)",
    "Garfish (针鱼)",
]
