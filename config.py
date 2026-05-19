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

# 🍳 鱼种烹饪做法数据库
FISH_COOKING_RECIPES = {
    "Bream (鳊鱼)": {
        "icon": "🐟",
        "legal_size": "25 cm",  # NSW DPI 官方法定尺寸
        "photo_path": "static/fish/bream.jpg",
        "methods": [
            "🍳 香煎：裹少许面粉，中火煎至两面金黄",
            "🍲 清蒸：葱姜丝垫底，大火蒸8-10分钟",
            "🔥 盐烧：粗盐腌制30分钟后炭烤",
            "🥘 红烧：豆瓣酱红烧最入味",
        ],
        "tips": "Bream 肉质细嫩，适合清蒸或香煎，不适合久煮。去鳞后用料酒腌制15分钟去腥。",
        "videos": [
            "https://www.youtube.com/watch?v=Kz4Zp7OvQVQ",
            "https://www.youtube.com/watch?v=9bZkp7q19f0",
        ],
    },
    "Flathead (牛鳅)": {
        "icon": "🐟",
        "legal_size": "36-70 cm (槽限制)",  # NSW DPI 2024 官方: 36cm 最小, 70cm 最大
        "photo_path": "static/fish/flathead.jpg",
        "methods": [
            "🍤 鱼排：片肉裹粉香煎，配柠檬",
            "🍲 鱼汤：鱼骨熬汤底，鲜甜无比",
            "🧄 蒜蓉蒸：蒜蓉葱花蒸8分钟",
            "🥟 鱼丸：打浆做鱼丸，Q弹爽口",
        ],
        "tips": "Flathead 肉质白嫩，刺少肉多，是做鱼排的绝佳选择。鱼片不要切太薄，1.5cm 左右最佳。",
        "videos": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ],
    },
    "Whiting (沙尖)": {
        "icon": "🐟",
        "legal_size": "27 cm",  # NSW DPI 官方法定尺寸
        "photo_path": "static/fish/whiting.jpg",
        "methods": [
            "🍳 干煎：去头洗净，中火干煎",
            "🧂 盐酥：裹地瓜粉油炸至酥脆",
            "🍲 煮粥：做潮汕鱼粥，鲜甜",
            "🔥 炭烤：串起来炭火慢烤",
        ],
        "tips": "沙尖鱼虽小但肉质鲜美，做法越简单越好吃。煎之前用厨房纸吸干水分更容易煎得酥脆。",
        "videos": [],
    },
    "Squid (鱿鱼)": {
        "icon": "🦑",
        "legal_size": "无限制",
        "photo_path": "static/fish/squid.jpg",
        "methods": [
            "🔥 铁板烧：切花刀，铁板快速煎烤",
            "🧄 蒜蓉蒸：蒜蓉粉丝蒸8分钟",
            "🍤 酥炸：裹粉油炸配椒盐",
            "🥗 刺身：新鲜鱿鱼直接做刺身",
            "🍝 鱿鱼圈：切圈裹粉油炸配意面",
        ],
        "tips": "鱿鱼最忌煮太久，会变老变硬。大火快速烹饪30秒-2分钟最佳。切花刀更容易入味。",
        "videos": [
            "https://www.youtube.com/watch?v=1j2N3b4V5bM",
        ],
    },
    "Kingfish (黄尾师)": {
        "icon": "🐟",
        "legal_size": "65 cm",  # NSW DPI 官方法定尺寸
        "photo_path": "static/fish/kingfish.jpg",
        "methods": [
            "🥩 刺身：顶级刺身食材，油脂丰富",
            "🍣 寿司：做握寿司或军舰",
            "🔥 鱼排：厚切2cm，中火煎至半熟",
            "🥘 照烧：日式照烧酱慢煮",
            "🧊 鱼生：潮汕鱼生做法",
        ],
        "tips": "黄尾师是顶级刺身鱼，肉色粉红，油脂丰富。越新鲜越好吃，建议3天内食用。",
        "videos": [
            "https://www.youtube.com/watch?v=example-kingfish",
        ],
    },
    "Tailor (蓝鱼)": {
        "icon": "🐟",
        "legal_size": "30 cm",  # NSW DPI 官方法定尺寸
        "photo_path": "static/fish/tailor.jpg",
        "methods": [
            "🍳 香煎：厚切煎至外酥里嫩",
            "🧄 蒜烧：大蒜爆香后焖烧",
            "🍲 咖喱：做鱼咖喱超下饭",
            "🥫 茄汁：茄汁炆鱼，酸甜开胃",
        ],
        "tips": "蓝鱼肉质紧实，味道浓郁，适合重口味做法。建议放血后再处理，肉质更白。",
        "videos": [],
    },
    "Salmon (三文鱼)": {
        "icon": "🐟",
        "legal_size": "30 cm",  # NSW DPI 官方法定尺寸 (Australian Salmon)
        "photo_path": "static/fish/salmon.jpg",
        "methods": [
            "🍣 刺身：最经典吃法，配芥末酱油",
            "🔥 烟熏：冷熏或热熏都美味",
            "🍳 煎排：皮朝下煎，皮脆肉嫩",
            "🧈 黄油烤：黄油香草烤制",
            "🥗 沙拉：烤三文鱼配沙拉",
        ],
        "tips": "澳洲三文鱼和三文鱼是不同品种！澳洲 Salmon 脂肪较少，更适合煎烤，不建议刺身生吃。",
        "videos": [],
    },
    "Drummer (黑毛)": {
        "icon": "🐟",
        "legal_size": "30 cm",  # NSW DPI 官方法定尺寸
        "photo_path": "static/fish/drummer.jpg",
        "methods": [
            "🍲 清蒸：顶级矶钓鱼，清蒸最佳",
            "🧄 蒜蓉蒸：蒜蓉豆豉蒸",
            "🍳 香煎：厚切慢火香煎",
            "🥘 炖汤：和中药材一起炖汤",
        ],
        "tips": "黑毛是钓鱼人的梦幻鱼种，肉质极为细嫩鲜甜，最简单的清蒸最能体现其本味。",
        "videos": [],
    },
    "Jewfish (皇冠鲊)": {
        "icon": "🐟",
        "legal_size": "45 cm",  # NSW DPI 官方法定尺寸 (Mulloway/Jewfish)
        "photo_path": "static/fish/jewfish.jpg",
        "methods": [
            "🥩 鱼排：大鱼肉厚，做鱼排超赞",
            "🍲 鱼头汤：大鱼头熬奶白汤",
            "🧄 蒜子焖：大蒜焖鱼块",
            "🥫 红烧：大块红烧，过瘾",
        ],
        "tips": "皇冠鲊个体大，肉质细嫩但刺少。鱼膘是顶级食材，千万不要丢！",
        "videos": [],
    },
    "Leatherjacket (剥皮鱼)": {
        "icon": "🐟",
        "legal_size": "25 cm",  # NSW DPI 官方法定尺寸
        "photo_path": "static/fish/leatherjacket.jpg",
        "methods": [
            "🍤 酥炸：去头去皮，裹粉油炸",
            "🧄 豆酱煮：普宁豆酱煮最经典",
            "🍲 煮粥：剥皮鱼粥是潮汕名菜",
            "🔥 干煎：中火干煎配桔油",
        ],
        "tips": "一定要剥皮！皮厚且韧无法食用。鱼肉鲜甜有韧性，是非常实惠的食用鱼。",
        "videos": [],
    },
    "Blue Groper (蓝唇鱼)": {
        "icon": "🐟",
        "legal_size": "禁捕",  # NSW DPI 2025 新规: 禁捕至 2028 年 (Eastern Blue Groper)
        "photo_path": "static/fish/bluegroper.jpg",
        "methods": [
            "🍳 香煎：厚切慢煎，外香里嫩",
            "🧄 蒜蓉蒸：蒜蓉蒸10分钟",
            "🥘 咖喱：鱼肉紧实适合咖喱",
            "🔥 烤鱼：整条炭烤，皮脆肉嫩",
        ],
        "tips": "蓝唇鱼是澳洲特有鱼种，肉质紧实有弹性，味道清甜。注意：有些地区有尺寸和数量限制。",
        "videos": [],
    },
}
