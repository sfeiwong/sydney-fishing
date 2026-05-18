import streamlit as st
import requests
from datetime import datetime, timedelta

# ==========================================
# 1. 页面基本配置
# ==========================================
st.set_page_config(page_title="悉尼钓鱼助手 Pro", page_icon="🎣", layout="centered")

# ==========================================
# 2. 从免费 API 获取悉尼未来三天的海况与浪涌预测
# ==========================================
@st.cache_data(ttl=3600)
def get_sydney_marine_data_3days():
    try:
        lat, lon = -33.8688, 151.2093
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,wind_speed_10m_max&timezone=Australia%2FSydney"
        weather_res = requests.get(weather_url).json()
        
        marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&daily=wave_height_max,swell_wave_height_max,swell_wave_direction_dominant,swell_wave_period_max&timezone=Australia%2FSydney"
        marine_res = requests.get(marine_url).json()
        
        forecast_data = []
        for i in range(3):
            forecast_data.append({
                "date": weather_res['daily']['time'][i],
                "temp": weather_res['daily']['temperature_2m_max'][i],
                "wind": weather_res['daily']['wind_speed_10m_max'][i],
                "wave": marine_res['daily']['wave_height_max'][i],
                "swell_height": marine_res['daily']['swell_wave_height_max'][i],
                "swell_direction": marine_res['daily']['swell_wave_direction_dominant'][i],
                "swell_period": marine_res['daily']['swell_wave_period_max'][i]
            })
        return {"success": True, "days": forecast_data}
    except Exception as e:
        today = datetime.now()
        fallback_data = []
        for i in range(3):
            future_date = today + timedelta(days=i)
            fallback_data.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "temp": 21.0, "wind": 12.0, "wave": 1.1,
                "swell_height": 0.9, "swell_direction": 140, "swell_period": 8.5
            })
        return {"success": False, "days": fallback_data}

# ==========================================
# 3. 智能潮汐核心推算函数
# ==========================================
def get_base_tides_for_date(target_date):
    base_date = datetime(2026, 1, 1, 6, 0)
    days_diff = (target_date - base_date).days
    total_minutes_shift = days_diff * 50
    first_high_target_day = base_date + timedelta(minutes=total_minutes_shift)
    
    t1 = datetime(target_date.year, target_date.month, target_date.day, first_high_target_day.hour % 24, first_high_target_day.minute % 60)
    t2 = t1 + timedelta(hours=6, minutes=12)
    t3 = t2 + timedelta(hours=6, minutes=12)
    t4 = t3 + timedelta(hours=6, minutes=12)
    return [t1, t2, t3, t4]

# ==========================================
# 4. 终极默认数据列表：内置悉尼 10 大岸钓钓点
# ==========================================
DEFAULT_SPOTS = [
    {
        "name": "Whale Beach (鲸鱼海滩及两侧礁石)",
        "region": "Northern Beaches (北部海滩外海)",
        "type": "⚠️ 外海巨浪沙滩 / 岩石陡坡",
        "sheltered": False,
        "tide_delay": -5,
        "active_fish": "Australian Salmon（澳洲三文鱼）、Tailor（蓝鱼）、Black Drummer（黑毛）、Whiting（大沙尖）",
        "fish_tags": ["三文鱼", "蓝鱼", "黑毛", "沙尖"],
        "best_window": "🌅 清晨或黄昏 + 涨潮（High Tide）前后的2小时。",
        "supported_methods": ["无铅漂钓", "Running Sinker (活铅沉底)", "路亚大物"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！仅限风平浪静，在南侧礁石打出的白沫区漂面包，主攻极大的外海黑毛。",
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！带上远投竿站在沙滩上，挂大沙蚕，大平头牛鳅和三文鱼咬钩极猛！",
            "路亚大物": "🎯 顶级推荐！站在南侧礁石台上向外海抛投重型铁板，单挑大 Kingfish 的风水宝地。"
        },
        "route": "从 City 向北沿 Barrenjoey Rd 一路北上，右转切入 Whale Beach Road 顺山路下到海滩。",
        "parking": "海滩正下方有大型收费停车场。建议清晨 5-6 点卡着日出出竿，车位充足且能避开收费。"
    },
    {
        "name": "Bare Island (La Perouse 秃头岛桥底)",
        "region": "Randwick / La Perouse (东南区湾口)",
        "type": "历史古迹桥底 / 外海礁石边缘",
        "sheltered": False,
        "tide_delay": -2,
        "active_fish": "Bream（鳊鱼）、Luderick（黑毛类）、Flathead（牛鳅）、Salmon（三文鱼）",
        "fish_tags": ["鳊鱼", "黑毛", "牛鳅", "三文鱼"],
        "best_window": "🌊 潮水刚开始上涨至满潮期间。鱼群会顺着桥墩疯狂觅食。",
        "supported_methods": ["无铅漂钓", "Running Sinker (活铅沉底)", "路亚大物"],
        "method_tips": {
            "无铅漂钓": "🎯 顶级推荐！站在木桥上无铅挂整条虾肉顺流漂进桥墩阴影，狙击深水大 Bream 的圣地！",
            "Running Sinker (活铅沉底)": "👍 推荐！向桥墩周围沙地远投，平头牛鳅极多。但要提防挂底。",
            "路亚大物": "👍 推荐！岛屿外侧面对深海航道，清晨甩铁板常能遭遇 Salmon 炸水群。"
        },
        "route": "沿 Anzac Parade 一路向南开到最尽头，即可看到 La Perouse 历史遗址和木桥。",
        "parking": "周边有超大免费公共停车场。周末白天极堵，夜钓或清晨看日出出竿是老手首选。"
    },
    {
        "name": "Bradleys Head (石坝与旧码头)",
        "region": "Mosman (北区岬角中部)",
        "type": "港内伸入式石坝 / 乱石区",
        "sheltered": True,
        "tide_delay": 3,
        "active_fish": "Bream（鳊鱼）、Kingfish（黄尾师）、Tailor（蓝鱼）、Squid（大鱿鱼）",
        "fish_tags": ["鳊鱼", "黄尾师", "蓝鱼", "鱿鱼"],
        "best_window": "🕒 退潮三分。此时主航道冲出的湍急潮流产生回流，回游大鱼极度活跃。",
        "supported_methods": ["无铅漂钓", "路亚大物", "木虾抽鱿鱼"],
        "method_tips": {
            "无铅漂钓": "🎯 顶级推荐！在灯塔石坝两侧用无铅下沉法，专门搞定警戒心极高的内湾巨型老 Bream。",
            "Running Sinker (活铅沉底)": "一般。石坝周围水底乱石密布，极易卡铅挂底。",
            "路亚大物": "🎯 顶级推荐！直面主航道狭窄地带，非常适合用 20-30g 铁板拦截巡游的 Kingfish。",
            "木虾抽鱿鱼": "👍 推荐！两边大叶藻丰富，黄昏是用木虾摸鱿鱼的高产区。"
        },
        "route": "驱车进入 Bradley's Head Road 一直向南开到尽头，沿步道走向灯塔石坝。",
        "parking": "属于国家公园管理，自助购买门票（约 $12/天）。晚上 8 点后通常车位非常空旷。"
    },
    {
        "name": "Balmoral Jetty & Public Wharf",
        "region": "Mosman (北区顶级内湾)",
        "type": "防波堤休闲木栈桥",
        "sheltered": True,
        "tide_delay": 8,
        "active_fish": "Calamari（大鱿鱼）、Whiting（沙尖）、Bream（鳊鱼）、Leatherjacket（剥皮鱼）",
        "fish_tags": ["鱿鱼", "沙尖", "鳊鱼", "剥皮鱼"],
        "best_window": "🌃 晚上 9 点至午夜的满潮期。夜间木栈桥的探探照灯极度吸引鱿鱼。",
        "supported_methods": ["Running Sinker (活铅沉底)", "木虾抽鱿鱼", "无铅漂钓"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！贴着栈桥木桩不加铅放线往下漂，挂小方块面包或虾肉主攻中小型鳊鱼。",
            "Running Sinker (活铅沉底)": "👍 推荐！栈桥前方是大片细沙滩，用活砂蚕远投经常能拉到大号 Whiting。",
            "路亚大物": "不推荐。属于极深内湾，极少有大洋 Pelagic 大物进湾。",
            "木虾抽鱿鱼": "🎯 顶级推荐！悉尼最舒适的抽鱿鱼新手村。木桥下方长满海草，晚上灯光极好。"
        },
        "route": "走 Military Rd 转入 Spit Rd，右转下山进入 Awaba St 开到水边。",
        "parking": "海滩沿线白天停车极为昂贵。**夜钓绝对是首选**，晚上 8 点后部分路段免费且车位空荡。"
    },
    {
        "name": "Blues Point Reserve (McMahons Point)",
        "region": "North Sydney (北悉尼港内)",
        "type": "港内深水石墙 (Harbor Rock Wall)",
        "sheltered": True,
        "tide_delay": 0,
        "active_fish": "Bream（鳊鱼）、Flathead（牛鳅）、Jewfish（皇冠鲊）、Squid（大鱿鱼）",
        "fish_tags": ["鳊鱼", "牛鳅", "皇冠鲊", "鱿鱼"],
        "best_window": "🌙 深夜到凌晨 3 点。轮渡停航航道死寂，深水槽中的大物敢大胆靠岸。",
        "supported_methods": ["Running Sinker (活铅沉底)", "无铅漂钓", "木虾抽鱿鱼"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！沿着防波石墙根无铅挂整条死虾贴着石缝随流往下放，主攻大鳊鱼。",
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！使用 2-3号通心铅向前方深水主航道盲抛，是深夜守大 Jewfish 的宝地。",
            "木虾抽鱿鱼": "👍 推荐！面向主航道且有探照灯，2.5号木虾贴底慢抽效果不错。"
        },
        "route": "经北悉尼切入 Blues Point Road 一路向南开到半岛的最尽头水边。",
        "parking": "道路尽头环形区有较多车位。**推荐晚上 8 点后前往**，完全免费且车位充足。"
    },
    {
        "name": "Captain Cook Bridge ( Sans Souci 北侧桥底 )",
        "region": "St George / Rockdale (南区河口)",
        "type": "沙滩平滩 / 桥墩阴影",
        "sheltered": True,
        "tide_delay": 15,
        "active_fish": "Flathead（大平头牛鳅）、Whiting（沙尖）、Bream（鳊鱼）",
        "fish_tags": ["牛鳅", "沙尖", "鳊鱼"],
        "best_window": "🕒 满潮后开始退潮的前 3 小时。上游小虾被冲向深水槽，Flathead 在沙滩边缘埋伏。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "无铅漂钓": "不推荐。属于纯平沙滩结构，无铅难以控线，容易被冲回岸边。",
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！使用 3-4号通心铅，搭配活河虾或沙蚕顺流往主桥墩阴影抛出，主攻超大 Flathead。",
            "木虾抽鱿鱼": "不推荐。无藻礁，几乎没有鱿鱼定居。"
        },
        "route": "沿 Princes Highway 向南开，大桥前靠最左侧匝道切入桥底的 Riverside Drive。",
        "parking": "桥底公园沿线建有超大型全免费停车场。环境安全开阔，下车走 20 米即可开钓。"
    },
    {
        "name": "George Head (Mosman)",
        "region": "Mosman (北区岬角)",
        "type": "内湾深水岩石平台",
        "sheltered": True,
        "tide_delay": 5,
        "active_fish": "Yellowtail Kingfish（黄尾师）、Australian Salmon（三文鱼）、Calamari（大鱿鱼）、Black Drummer（黑毛）",
        "fish_tags": ["黄尾师", "三文鱼", "鱿鱼", "黑毛"],
        "best_window": "🌄 太阳刚破晓的前后 1 小时（First Light）+ 潮流最急的涨潮期。",
        "supported_methods": ["路亚大物", "木虾抽鱿鱼", "无铅漂钓"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！站在礁石边缘将整只大虾肉不加铅投入拍击礁石形成的白沫带中，是打大内湾黑毛的极佳手段。",
            "Running Sinker (活铅沉底)": "不推荐。水流湍急且水底全是海草和挂底乱石，沉底必卡。",
            "路亚大物": "🎯 顶级推荐！直面主航道，建议使用 20-40g 铁板拦截 Kingfish。大流时鱼讯极其疯狂。",
            "木虾抽鱿鱼": "🎯 顶级推荐！水下大叶藻床极其茂盛，使用 2.5号或3.0号常规木虾盛产大号 Calamari。"
        },
        "route": "驱车前往 Mosman 的 Middle Head Road，随后切入 Suakin Drive 停靠在 Headland Park 区域。",
        "parking": "有收费停车场。停好车后，需要步行沿着丛林步道下山约 10 分钟到达礁石区。"
    },
    {
        "name": "Darling Point Wharf",
        "region": "Darling Point (东区内湾)",
        "type": "渡轮码头 / 亲水石墙",
        "sheltered": True,
        "tide_delay": 0,
        "active_fish": "Bream（鳊鱼）、Leatherjacket（剥皮鱼）、Squid（大鱿鱼）",
        "fish_tags": ["鳊鱼", "剥皮鱼", "鱿鱼"],
        "best_window": "🕗 晚上 8 点至夜间 11 点。最后一班渡轮停航，高位射灯打出的光晕会瞬间变为最佳捕食场。",
        "supported_methods": ["Running Sinker (活铅沉底)", "木虾抽鱿鱼", "无铅漂钓"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！夜间轮渡停航后，用无铅漂钓法挂小块鸡肉，顺着木桩边缘缓缓放线钓大 Bream。",
            "Running Sinker (活铅沉底)": "👍 推荐！用轻铅 Running Sinker 钓组挂鲜虾肉在石墙和栈桥阴影边缘作钓。",
            "木虾抽鱿鱼": "👍 推荐！夜间亮灯后木虾抽鱿鱼的经典小窝子，建议使用 2.0号慢沉木虾。"
        },
        "route": "从 City 沿着 New South Head Rd 向东开，左转切入 Darling Point Road 一直开到底。",
        "parking": "富人区白天车位极少。**极力推荐在晚上 8 点后自驾前往夜钓**，此时路边车位完全空出且免费。"
    },
    {
        "name": "Buchan Point (Malabar)",
        "region": "Randwick (东区外海)",
        "type": "⚠️ 高危外海岩石平台",
        "sheltered": False,
        "tide_delay": -5,
        "active_fish": "Black Drummer（黑毛）、Blue Groper（蓝唇鱼）、Yellowtail Kingfish（黄尾师）",
        "fish_tags": ["黑毛", "蓝唇鱼", "黄尾师"],
        "best_window": "🌊 涨潮正当时 + 必须在风浪极小的天气窗口。切勿为了赶鱼情盲目冒险！",
        "supported_methods": ["无铅漂钓", "Running Sinker (活铅沉底)", "路亚大物"],
        "method_tips": {
            "无铅漂钓": "🎯 顶级推荐！标准的【面包流漂钓】。不加铅，单钩挂面包芯随波逐流狙击巨型 Drummer。",
            "Running Sinker (活铅沉底)": "👍 推荐（重矶防挂底）！这里使用 Running Sinker 需要使用极重的铅弹狙击底层大物。",
            "路亚大物": "👍 推荐！迎风甩 40-80g 重型路亚铁板或波趴，有机会单挑巡游的超级大 Kingfish。"
        },
        "route": "沿 Anzac Parade 一路向南开到底，左转进入 Franklin St 到底。",
        "parking": "路边有免费停车位。停好车后需要背负装备翻越乱石坡，必须穿着钉鞋防滑。"
    },
    {
        "name": "Bobbin Head (Ku-ring-gai Chase)",
        "region": "Ku-ring-gai (北区国家公园)",
        "type": "国家公园深湾栈桥/河口",
        "sheltered": True,
        "tide_delay": 50,
        "active_fish": "Flathead（牛鳅）、Whiting（沙尖鱼）、Bream（鳊鱼）",
        "fish_tags": ["牛鳅", "沙尖", "鳊鱼"],
        "best_window": "☀️ 白天阳光充足期结合满潮。浅水滩阳光照射提高水温，Flathead 捕食最积极。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "无铅漂钓": "一般。这里水流太缓慢，诱鱼效果不如贴底的活铅沉底。",
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！完全避风的泥沙底远投绝不挂底。挂沙蚕或鲜虾肉主攻大平头牛鳅。",
            "路亚大物": "一般。无回游大物，仅适合轻量微物路亚钓青衣或鳊鱼。"
        },
        "route": "从 Turramurra 沿着 Bobbin Head Rd 一直向下开到山谷最底部的入海口。",
        "parking": "景区内部建有数个超大停车场。进入属于国家公园，需购买 $12 车辆单日票。"
    }
]

# ==========================================
# 5. 前端界面布局
# ==========================================
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🎣 悉尼钓鱼助手 Pro</h1>", unsafe_allow_html=True)
st.markdown("---")

# 一次性获取未来 3 天的数据
forecast_result = get_sydney_marine_data_3days()
days_data = forecast_result['days']

# 顶部的日期选项卡
tab_titles = [
    f"📅 今天 ({days_data[0]['date']})",
    f"📅 明天 ({days_data[1]['date']})",
    f"📅 后天 ({days_data[2]['date']})"
]
tabs = st.tabs(tab_titles)

for idx, tab in enumerate(tabs):
    with tab:
        day_data = days_data[idx]
        target_dt = datetime.strptime(day_data['date'], "%Y-%m-%d")
        
        # 布局：左海况看板，右当日基准潮汐
        col_left, col_right = st.columns([1.1, 0.9])
        
        with col_left:
            st.subheader("🌊 实时海况预测")
            st.metric(label="🌡️ 最高气温", value=f"{day_data['temp']} °C")
            st.metric(label="💨 最大风速", value=f"{day_data['wind']} km/h")
            st.metric(label="🌊 综合浪高", value=f"{day_data['wave']} 米")
            
            st.markdown(f"""
            > **📊 核心浪涌（Swell）参数：**
            > * **纯浪涌高度**：`{day_data['swell_height']} 米`
            > * **浪涌周期**：`{day_data['swell_period']} 秒`
            > * **涌向**：`{day_data['swell_direction']}°`
            """)
            
        with col_right:
            st.subheader("📅 当日基准潮汐 (Fort Denison)")
            base_tides = get_base_tides_for_date(target_dt)
            for i, t in enumerate(base_tides):
                t_type = "🟢 满潮 (High Tide)" if i % 2 == 0 else "🔵 干潮 (Low Tide)"
                st.markdown(f"**{t_type}** —— `{t.strftime('%H:%M')}`")
                
        st.markdown("---")
        
        # ==========================================
        # 核心修改：在钓点上方加入主页面筛选条件（默认显示全部）
        # ==========================================
        st.subheader("🔍 智能筛选钓点")
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            selected_method = st.selectbox(
                "选择钓法：",
                ["全部钓法显示", "无铅漂钓", "Running Sinker (活铅沉底)", "路亚大物", "木虾抽鱿鱼"],
                key=f"method_filter_{idx}" # 确保多天选项卡之间组件ID不冲突
            )
            
        with filter_col2:
            selected_fish = st.selectbox(
                "选择目标鱼种：",
                ["全部鱼种显示", "鳊鱼", "牛鳅", "沙尖", "鱿鱼", "黄尾师", "蓝鱼", "三文鱼", "黑毛", "皇冠鲊", "剥皮鱼"],
                key=f"fish_filter_{idx}"
            )
            
        st.markdown("---")
        st.subheader("📍 匹配钓点及出行打分")
        
        # ==========================================
        # 6. 核心联合智能过滤与打分算法
        # ==========================================
        visible_count = 0
        
        for spot in DEFAULT_SPOTS:
            # 1. 过滤逻辑 A：钓法匹配
            if selected_method != "全部钓法显示" and selected_method not in spot['supported_methods']:
                continue
                
            # 2. 过滤逻辑 B：鱼种匹配
            if selected_fish != "全部鱼种显示" and selected_fish not in spot['fish_tags']:
                continue
                
            visible_count += 1
            
            # 确定当前钓点要显示的建议指南
            method_key = selected_method if selected_method != "全部钓法显示" else spot['supported_methods'][0]
            
            status = "✅ 极力推荐"
            score = "⭐⭐⭐⭐⭐"
            advice = "此日海况温和，该钓点非常符合您的作钓需求，祝爆护！"
            
            # 计算专属潮汐时间
            spot_tides = []
            for i, bt in enumerate(base_tides):
                real_time = bt + timedelta(minutes=spot['tide_delay'])
                t_type = "满潮 🟢" if i % 2 == 0 else "干潮 🔵"
                spot_tides.append(f"{t_type}`{real_time.strftime('%H:%M')}`")
            
            # 风浪安全系数考量
            if not spot['sheltered'] and (day_data['swell_height'] > 1.3 or day_data['wind'] > 20):
                status = "❌ 极度危险 (不建议前往)"
                score = "⭐"
                advice = f"🚨 警告：外海浪涌预计达 {day_data['swell_height']}米！该钓点直面外海，极易拍起夺命大浪，请立刻更换为内湾安全钓点！"
            elif spot['sheltered'] and (day_data['swell_height'] > 1.4 or day_data['wind'] > 22):
                status = "⚠️ 谨慎前往"
                score = "⭐⭐⭐"
                advice = "此日悉尼风浪较大。虽是内湾避风港，但顶风抛投会受到影响，请选择背风位作钓。"
        
            # 渲染前端折叠面板
            with st.expander(f"{score} {spot['name']} —— {status}"):
                st.write(f"**🌍 所属区域**：`{spot['region']}` | **📍 地形**：`{spot['type']}`")
                st.write(f"**🐟 今日活跃鱼种**：`{spot['active_fish']}`")
                st.write(f"**⏱️ 最佳作钓窗口**：{spot['best_window']}")
                st.write(f"**⏰ 钓点专属潮汐推算**：{' | '.join(spot_tides)}")
                st.markdown(f"**💡 当前钓法实战建议 ({method_key})**：\n> {spot['method_tips'][method_key]}")
                st.write(f"**🚗 自驾路线**：{spot['route']}")
                st.info(f"**🅿️ 停车方案**：{spot['parking']}")
                st.warning(f"**⚠️ 针对当前海况的安全劝告**：{advice}")
                
        # 如果双重筛选下没有一个匹配的钓点，给用户一个温馨提示
        if visible_count == 0:
            st.info("ℹ️ 暂无完全满足当前双重筛选条件的钓点，建议您放宽筛选条件（如选择‘全部鱼种显示’）再试。")

st.markdown("---")
st.caption("🚨 提示：海边钓鱼具有一定风险，出行前请务必穿戴好救生衣与防滑鞋。预测数据基于公开气象模型推算。")
