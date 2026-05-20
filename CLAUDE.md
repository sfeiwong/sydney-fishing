# CLAUDE.md — 悉尼钓鱼助手 项目上下文

本文件为 AI 辅助开发提供项目背景，迭代时请先阅读此文件。

---

## 项目简介

**Sydney Fishing Assistant（悉尼钓鱼助手 Pro+）**
一个面向悉尼本地钓鱼爱好者的 Streamlit Web 应用，整合实时天气/海况、潮汐推算、钓点数据库，帮助用户选择当天最合适的钓点和钓法。

- **目标用户**：悉尼华人钓鱼爱好者（含家庭出行需求）
- **语言**：界面全中文，鱼名/钓法双语标注（中英对照）
- **运行方式**：`streamlit run app.py`

---

## 目录结构

```
sydney-fishing/
├── app.py                  # 主程序，只负责 UI 渲染和页面逻辑
├── config.py               # 全局常量：安全阈值、筛选选项、潮汐参数
├── requirements.txt
├── CLAUDE.md               # 本文件
├── data/
│   ├── __init__.py
│   ├── loader.py           # load_spots() 从 spots.json 加载钓点
│   └── spots.json          # 48 个钓点的完整数据库（含坐标）
└── services/
    ├── __init__.py
    ├── weather.py          # 调用 Open-Meteo API，按坐标区域缓存
    └── tides.py            # 潮汐天文近似推算（Fort Denison 基准）
```

---

## 核心数据结构

### 钓点对象（`data/spots.json` 中每一项）

```jsonc
{
  "name": "钓点名称（中英双语）",
  "region": "所属区域",
  "type": "地形类型描述",
  "lat": -33.85,           // 钓点纬度（必填，用于获取当地天气）
  "lon": 151.21,           // 钓点经度（必填）
  "water_type": "harbour", // 水域类型：ocean | harbour | brackish | freshwater
  "sheltered": true,       // 由 water_type 派生（ocean=false，其余=true），影响安全评估
  "tide_delay": 10,        // 相对 Fort Denison 的潮汐时间偏差（分钟，可负）；淡水点填 0
  "active_fish": "...",    // 可钓鱼种自由描述文字
  "fish_tags": ["Bream (鳊鱼)", "..."],  // 用于多选筛选的标准化标签
  "best_window": "...",    // 最佳出钓时间窗口描述
  "family_friendly": "⭐⭐⭐⭐⭐ ...", // 家庭友好度（⭐数量 + 文字说明）
  "supported_methods": ["Running Sinker (活铅沉底)", "..."],  // 支持的钓法列表
  "method_tips": {         // 每种钓法的具体攻略（key 必须与 supported_methods 一致）
    "Running Sinker (活铅沉底)": "🎯 顶级推荐！..."
  },
  "route": "自驾路线描述",
  "parking": "停车方案描述"
}
```

**`water_type` 取值说明：**

| 值 | 含义 | 典型场景 |
|----|------|---------|
| `ocean` | 外海 | 矶钓礁盘、外海悬崖 |
| `harbour` | 内湾 | 悉尼港、博特尼湾内侧 |
| `brackish` | 咸淡水 | 河口、泻湖、潮汐影响的内河上游 |
| `freshwater` | 淡水 | 内陆湖泊、纯淡水河段 |

### 天气数据对象（`services/weather.py` 返回）

```python
{
    "success": True,          # False 时 UI 显示警告
    "days": [                 # 索引 0=今天, 1=明天, 2=后天
        {
            "date": "2026-05-19",
            "temp": 22.0,          # 最高气温 °C
            "wind": 15.0,          # 最大风速 km/h
            "wave": 1.2,           # 综合浪高 m
            "swell_height": 0.9,   # 纯涌浪高度 m
            "swell_direction": 140,# 涌向 °
            "swell_period": 8.5,   # 涌浪周期 s
        }
    ]
}
```

### 潮汐对象（`services/tides.py` 返回，每天 4 项）

```python
[
    {"time": datetime(...), "is_high": True,  "label": "🟢 满潮"},
    {"time": datetime(...), "is_high": False, "label": "🔵 干潮"},
    ...
]
```

---

## 关键业务逻辑

### 安全评估（`app.py → assess_safety()`）

以 `water_type` 为主要判断依据：

| `water_type` | 条件 | 结果 |
|---|---|---|
| `ocean` | swell > 1.3m 或 wind > 20km/h | ❌ 极度危险（红色） |
| `harbour` / `brackish` | swell > 1.4m 或 wind > 22km/h | ⚠️ 谨慎前往（橙色） |
| `freshwater` | wind > 22km/h | ⚠️ 谨慎前往（橙色）；不检查浪涌 |
| 其他 | — | ✅ 极力推荐（绿色） |

阈值在 `config.py` 中集中管理：`OCEAN_SWELL_DANGER`, `OCEAN_WIND_DANGER`, `SHELTERED_SWELL_WARN`, `SHELTERED_WIND_WARN`。

### 天气 API 缓存策略

`services/weather.py` 将坐标取整到 0.5°（约 55km 精度）再作为缓存键，避免 48 个钓点发起 48 次独立 API 请求。同一区域的钓点共用同一份预报数据。缓存 TTL = 1 小时（`config.py → WEATHER_CACHE_TTL`）。

### 潮汐推算精度说明

当前为天文近似算法，误差 ±30~60 分钟，适合辅助决策。如需精确数据，替换 `services/tides.py` 中的 `get_tides_for_date()` 即可，接口签名不变：

```python
def get_tides_for_date(target_date: datetime, delay_minutes: int = 0) -> list[dict]:
    ...
```

推荐替换方案：
- **免费**：每日抓取 [BOM 官方潮汐页](http://www.bom.gov.au/oceanography/tides/)
- **付费**：[WorldTides API](https://www.worldtides.info/api)（精度 ±5 分钟）

---

## 标准化枚举值

新增钓点时，`fish_tags` 和 `supported_methods` 的值必须来自以下列表（在 `config.py` 定义），否则多选筛选器无法匹配。

**`ALL_FISH`（鱼种标签）：**
`Bream (鳊鱼)` · `Flathead (牛鳅)` · `Whiting (沙尖)` · `Squid (鱿鱼)` · `Kingfish (黄尾师)` · `Tailor (蓝鱼)` · `Salmon (三文鱼)` · `Drummer (黑毛)` · `Jewfish (皇冠鲊)` · `Leatherjacket (剥皮鱼)` · `Blue Groper (蓝唇鱼)`
· `Australian Bass (澳洲鲈鱼)` · `Golden Perch (黄金鲈)` · `Carp (锦鲤)` · `Catfish (鲶鱼)`

**`ALL_METHODS`（钓法）：**
`无铅漂钓` · `Running Sinker (活铅沉底)` · `路亚大物` · `软饵路亚 (Soft Bait)` · `木虾抽鱿鱼` · `重铅沉底` · `全游动` · `半游动` · `活饵放流`

---

## 外部依赖

| 依赖 | 用途 | 备注 |
|------|------|------|
| `streamlit` | Web UI 框架 | 核心框架 |
| `requests` | HTTP 请求 | 调用天气 API |
| `folium` | 地图渲染 | 地图 Tab 使用 |
| `streamlit-folium` | Folium 与 Streamlit 桥接 | 配合 folium 使用 |

天气数据来源：
- 气象：`https://api.open-meteo.com/v1/forecast`
- 海况：`https://marine-api.open-meteo.com/v1/marine`
- 均为免费 API，无需 Key

---

## 常见迭代任务指引

**新增钓点**
→ 直接在 `data/spots.json` 末尾追加一个符合上述结构的 JSON 对象，必须填写 `water_type`（ocean/harbour/brackish/freshwater），并同步设置 `sheltered`（ocean=false，其余=true）。确保 `fish_tags` 和 `supported_methods` 使用标准化枚举值。淡水钓点 `tide_delay` 填 0。

**调整安全阈值**
→ 修改 `config.py` 中的 `OCEAN_SWELL_DANGER` 等四个常量。

**新增鱼种或钓法**
→ 在 `config.py` 的 `ALL_FISH` / `ALL_METHODS` 列表中追加，同时更新相关钓点的 `fish_tags` / `supported_methods`。

**替换潮汐数据源**
→ 只改 `services/tides.py`，保持 `get_tides_for_date(target_date, delay_minutes)` 的返回格式不变。

**修改 UI 布局**
→ 只改 `app.py`，业务逻辑和数据层不受影响。

**新增筛选维度（如按区域筛选）**
→ 在 `app.py` 侧边栏加 `st.multiselect`，在 `spot_matches()` 函数中加对应条件。

---

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```
