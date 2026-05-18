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
# 4. 20个史诗级精选岸钓钓点数据库 (全标签修复版)
# ==========================================
DEFAULT_SPOTS = [
    {
        "name": "Whale Beach (鲸鱼海滩及两侧礁石)",
        "region": "Northern Beaches (北部外海)",
        "type": "⚠️ 外海巨浪沙滩 / 岩石陡坡",
        "sheltered": False, "tide_delay": -5,
        "active_fish": "Australian Salmon（澳洲三文鱼）、Tailor（蓝鱼）、Black Drummer（黑毛）",
        "fish_tags": ["三文鱼", "蓝鱼", "黑毛"],
        "best_window": "🌅 清晨或黄昏 + 涨潮前后2小时。高水位能将大鱼推入沙滩浪区。",
        "family_friendly": "⭐⭐ (不适合低龄娃) 有公共洗手间和金黄沙滩，但风浪大，两侧礁石带有高危性质，绝不能带孩子过去。",
        "supported_methods": ["Running Sinker (活铅沉底)", "路亚大物"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！站在沙滩上远投挂大沙蚕，三文鱼和牛鳅咬钩极猛！",
            "路亚大物": "🎯 顶级推荐！风浪允许时站在南侧礁石台上向外海抛投重型铁板单挑 Kingfish。"
        },
        "route": "从 City 向北沿 Barrenjoey Rd 一路北上，右转切入 Whale Beach Road 顺山路下到海滩。",
        "parking": "海滩正下方有 Council 收费停车场。清晨卡着日出出竿可避开收费且车位多。"
    },
    {
        "name": "Bare Island (La Perouse 秃头岛桥底)",
        "region": "La Perouse (东南区湾口)",
        "type": "历史古迹桥底 / 外海礁石边缘",
        "sheltered": False, "tide_delay": -2,
        "active_fish": "Bream（鳊鱼）、Luderick（黑毛类）、Flathead（牛鳅）、Salmon",
        "fish_tags": ["鳊鱼", "黑毛", "牛鳅", "三文鱼"],
        "best_window": "🌊 潮水刚开始上涨至满潮期间。鱼群会顺着桥墩疯狂觅食。",
        "family_friendly": "⭐⭐⭐⭐ (极佳打卡地) 拥有绝美晚霞和木桥。草坪开阔适合野餐，路边有洗手间，极其适合推车遛娃，但严防礁石边缘滑倒。",
        "supported_methods": ["无铅漂钓", "Running Sinker (活铅沉底)", "路亚大物"],
        "method_tips": {
            "无铅漂钓": "🎯 顶级推荐！站在木桥上无铅挂整条虾肉顺流漂进桥墩阴影，狙击深水大 Bream 的圣地！",
            "Running Sinker (活铅沉底)": "👍 推荐！向桥墩周围沙地远投，平头牛鳅极多。但要提防挂底。",
            "路亚大物": "👍 推荐！岛屿外侧面对深海航道，清晨甩铁板常能遭遇 Salmon 炸水群。"
        },
        "route": "沿 Anzac Parade 一路向南开到最尽头即可看到 La Perouse 木桥。",
        "parking": "周边有超大免费公共停车场。周末白天观光客极堵，夜钓或清晨出竿最舒心。"
    },
    {
        "name": "Bradleys Head (石坝与旧码头)",
        "region": "Mosman (北区岬角)",
        "type": "港内伸入式石坝 / 乱石区",
        "sheltered": True, "tide_delay": 3,
        "active_fish": "Bream（鳊鱼）、Kingfish（黄尾师）、Tailor（蓝鱼）、Squid（大鱿鱼）",
        "fish_tags": ["鳊鱼", "黄尾师", "蓝鱼", "鱿鱼"],
        "best_window": "🕒 退潮三分。此时主航道冲出的湍急潮流产生回流，回游大鱼极度活跃。",
        "family_friendly": "⭐⭐⭐⭐ (风景绝美) 标志性的圆形剧场式草坪，正对歌剧院。有干净的公共厕所和林荫步道，极其适合铺张野餐垫遛娃。",
        "supported_methods": ["无铅漂钓", "路亚大物", "木虾抽鱿鱼"],
        "method_tips": {
            "无铅漂钓": "🎯 顶级推荐！在灯塔石坝两侧用无铅下沉法，专门搞定警戒心极高的内湾巨型老 Bream。",
            "路亚大物": "🎯 顶级推荐！直面主航道狭窄地带，非常适合用 20-30g 铁板拦截巡游的 Kingfish。",
            "木虾抽鱿鱼": "👍 推荐！两边大叶藻丰富，黄昏是用木虾摸鱿鱼的高产区"
        },
        "route": "驱车进入 Bradley's Head Road 一直向南开到尽头，沿步道走向灯塔石坝。",
        "parking": "属于国家公园管理，自助购买门票（约 $12/天）。晚上 8 点后通常车位非常空旷。"
    },
    {
        "name": "Balmoral Jetty & Public Wharf",
        "region": "Mosman (北区顶级内湾)",
        "type": "防波堤休闲木栈桥",
        "sheltered": True, "tide_delay": 8,
        "active_fish": "Calamari（大鱿鱼）、Whiting（沙尖）、Bream（鳊鱼）、Leatherjacket（剥皮鱼）",
        "fish_tags": ["鱿鱼", "沙尖", "鳊鱼", "剥皮鱼"],
        "best_window": "🌃 晚上 9 点至午夜的满潮期。夜间木栈桥的探照灯极度吸引鱿鱼。",
        "family_friendly": "⭐⭐⭐⭐⭐ (满分遛娃圣地) 自带儿童游乐场、遮阴草坪、免费高品质 BBQ 电炉。木栈桥极其平整安全，推车遛娃无压力！",
        "supported_methods": ["Running Sinker (活铅沉底)", "木虾抽鱿鱼", "无铅漂钓"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！贴着栈桥木桩不加铅放线往下漂，挂小方块面包或虾肉主攻鳊鱼。",
            "Running Sinker (活铅沉底)": "👍 推荐！栈桥前方是大片细沙滩，用活砂蚕远投经常能拉到大号 Whiting。",
            "木虾抽鱿鱼": "🎯 顶级推荐！悉尼最舒适的抽鱿鱼新手村。木桥下方长满海草，晚上灯光极好。"
        },
        "route": "走 Military Rd 转入 Spit Rd，右转下山进入 Awaba St 开到水边。",
        "parking": "海滩沿线白天停车极为昂贵。**夜钓绝对是首选**，晚上 8 点后车位空荡且免费。"
    },
    {
        "name": "Blues Point Reserve (McMahons Point)",
        "region": "North Sydney (北悉尼港内)",
        "type": "港内深水石墙 (Harbor Rock Wall)",
        "sheltered": True, "tide_delay": 0,
        "active_fish": "Bream（鳊鱼）、Flathead（牛鳅）、Jewfish（皇冠鲊）、Squid（大鱿鱼）",
        "fish_tags": ["鳊鱼", "牛鳅", "皇冠鲊", "鱿鱼"],
        "best_window": "🌙 深夜到凌晨 3 点。轮渡停航航道死寂，深水槽中的大物敢大胆靠岸。",
        "family_friendly": "⭐⭐⭐⭐ (硬核跨年机位) 正对海港大桥。有很棒的儿童秋千滑梯游乐场、大草坪和公共厕所。推车非常方便，白天遛娃看船、晚上爸爸甩竿。",
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
        "region": "St George (南区河口)",
        "type": "沙滩平滩 / 桥墩阴影",
        "sheltered": True, "tide_delay": 15,
        "active_fish": "Flathead（大平头牛鳅）、Whiting（沙尖）、Bream（鳊鱼）",
        "fish_tags": ["牛鳅", "沙尖", "鳊鱼"],
        "best_window": "🕒 满潮后开始退潮的前 3 小时。上游小虾被冲向深水槽，Flathead 在沙滩边缘埋伏。",
        "family_friendly": "⭐⭐⭐⭐⭐ (家庭野餐高分推荐) 拥有超多免费公共 BBQ 炉子、大型遮阳亭、干净洗手间、完备遛娃自行车道。孩子可以在浅沙滩安全玩沙。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！使用 3-4号通心铅，搭配活河虾或沙蚕顺流往主桥墩阴影抛出，主攻超大 Flathead。"
        },
        "route": "沿 Princes Highway 向南开，大桥前靠最左侧匝道切入桥底的 Riverside Drive。",
        "parking": "桥底公园沿线建有超大型全免费停车场。环境安全开阔，下车走 20 米即可开钓，推车无压力。"
    },
    {
        "name": "George Head (Mosman)",
        "region": "Mosman (北区岬角)",
        "type": "内湾深水岩石平台",
        "sheltered": True, "tide_delay": 5,
        "active_fish": "Yellowtail Kingfish（黄尾师）、Australian Salmon（三文鱼）、Calamari（大鱿鱼）",
        "fish_tags": ["黄尾师", "三文鱼", "鱿鱼"],
        "best_window": "🌄 太阳刚破晓的前后 1 小时 + 潮流最急的涨潮期。",
        "family_friendly": "⭐ (硬核钓手天堂，拒绝娃) 下山需要走长段没有护栏的丛林泥泞陡峭步道，完全无法推车，没有任何游乐或 BBQ 设施。",
        "supported_methods": ["路亚大物", "木虾抽鱿鱼", "无铅漂钓"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！站在礁石边缘将整只大虾肉不加铅投入拍击礁石形成的白沫带中，是打内湾大黑毛的极佳手段。",
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
        "sheltered": True, "tide_delay": 0,
        "active_fish": "Bream（鳊鱼）、Leatherjacket（剥皮鱼）、Squid（大鱿鱼）",
        "fish_tags": ["鳊鱼", "剥皮鱼", "鱿鱼"],
        "best_window": "🕗 晚上 8 点至夜间 11 点。最后一班渡轮停航，高位射灯打出的光晕会瞬间变为最佳捕食场。",
        "family_friendly": "⭐⭐⭐ (精致小巧) 紧挨着漂亮的 McKell Park。公园绿草如茵，有洗手间，但没有 BBQ 炉子。台阶较多推车略显不便。",
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
        "sheltered": False, "tide_delay": -5,
        "active_fish": "Black Drummer（黑毛）、Blue Groper（蓝唇鱼）、Yellowtail Kingfish（黄尾师）",
        "fish_tags": ["黑毛", "蓝唇鱼", "黄尾师"],
        "best_window": "🌊 涨潮正当时 + 必须在风浪极小的天气窗口。切勿为了赶鱼情盲目冒险！",
        "family_friendly": "⭐ (危险礁石，禁带家属) 纯硬核矶钓平台。乱石嶙峋，没有任何人工设施。风浪大时巨浪随时拍过头顶，为了安全别带家属。",
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
        "sheltered": True, "tide_delay": 50,
        "active_fish": "Flathead（牛鳅）、Whiting（沙尖鱼）、Bream（鳊鱼）",
        "fish_tags": ["牛鳅", "沙尖", "鳊鱼"],
        "best_window": "☀️ 白天阳光充足期结合满潮。浅水滩阳光照射提高水温，Flathead 捕食最积极。",
        "family_friendly": "⭐⭐⭐⭐⭐ (满分自然大氧吧) 拥有极为奢华的遮阳 BBQ 亭子群、超级大型草坪、儿童海盗船游乐场、平整无障碍推车绿道。家庭出游完美首选！",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！完全避风的泥沙底远投绝不挂底。挂沙蚕或鲜虾肉主攻大平头牛鳅。"
        },
        "route": "从 Turramurra 沿着 Bobbin Head Rd 一直向下开到山谷最底部的入海口。",
        "parking": "景区内部建有数个超大停车场。进入属于国家公园，需购买 $12 车辆单日票。"
    },
    {
        "name": "Clifton Gardens Wharf (Mosman)",
        "region": "Mosman (北区内湾)",
        "type": "内湾大栈桥 (Inner Harbor Wharf)",
        "sheltered": True, "tide_delay": 5,
        "active_fish": "Yellowtail Kingfish（黄尾师）、Calamari（大鱿鱼）、Bream（鳊鱼）",
        "fish_tags": ["黄尾师", "鱿鱼", "鳊鱼"],
        "best_window": "🌅 清晨第一缕光或者夜钓满潮期。回游的 Kingfish 会冲进防鲨网周边疯狂咬饵。",
        "family_friendly": "⭐⭐⭐⭐⭐ (悉尼老牌双冠王) 栈桥自带安全高护栏，海滩旁就是树荫儿童乐园、草坪、一整排全免费的公共 BBQ 电炉。推车极丝滑！",
        "supported_methods": ["无铅漂钓", "路亚大物", "木虾抽鱿鱼"],
        "method_tips": {
            "无铅漂钓": "👍 推荐！贴着木桥底或桩基放线，挂香蕉虾肉，容易拉到大 Bream 和 Trevally。",
            "路亚大物": "🎯 顶级推荐！清晨用 20-30g 活饵或铁板在桥头远投，主攻冲进内湾洗劫的黄尾师 Kingfish。",
            "木虾抽鱿鱼": "🎯 顶级推荐！桥下两侧密布海草床。夜间桥头灯光亮起，是用 2.5号木虾摸大鱿鱼的黄金胜地。"
        },
        "route": "走 Military Rd，右转切入 Bradley's Head Rd，顺着 Chowder Bay Rd 开到底。",
        "parking": "码头旁有大型 Council 收费停车场。周末白天爆满，省钱可以停在坡上居民区步行下来。"
    },
    {
        "name": "Tom Uglys Bridge (北侧平台)",
        "region": "Blakehurst (南区河口)",
        "type": "水道交汇桥底平台",
        "sheltered": True, "tide_delay": 20,
        "active_fish": "Bream（鳊鱼）、Flathead（牛鳅）、Mulloway（皇冠鲊）",
        "fish_tags": ["鳊鱼", "牛鳅", "皇冠鲊"],
        "best_window": "🕒 每天夜潮开始涨潮至满潮。桥墩在水下形成的巨大阴影区是顶级夜行猎食大物的藏身处。",
        "family_friendly": "⭐⭐⭐ (下车即钓，无游乐设施) 桥底建有铁护栏专属钓鱼平台。推婴儿车极其平整，但周边缺乏滑梯秋千，桥头有海鲜餐馆和公厕。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！使用 3号通心铅，挂一整条活虾或鲜乌贼条，抛向新旧大桥中间，深夜易单挑大 Mulloway！"
        },
        "route": "沿 Princes Highway 一路向南开，在即将驶上 Georges River 大桥前的最左侧匝道直接切入桥底。",
        "parking": "桥底北方尽头设有专属钓鱼免费停车场，车位较多，停好车走几步就到水边。"
    },
    {
        "name": "Gunnamatta Bay Baths",
        "region": "Cronulla (南区湾内)",
        "type": "平缓内湾木网水闸 / 栈桥",
        "sheltered": True, "tide_delay": 10,
        "active_fish": "Whiting（沙尖鱼）、Bream（鳊鱼）、Flathead（牛鳅）",
        "fish_tags": ["沙尖", "鳊鱼", "牛鳅"],
        "best_window": "☀️ 白天阳光明媚 + 满潮退三分。清澈见底的浅滩会引来大批 Whiting 过来进食。",
        "family_friendly": "⭐⭐⭐⭐⭐ (宝藏玩水点) 公园大草坪开阔漂亮，配有完善的遮阳野餐桌、遮阳大树、干净洗手间。水闸围成天然静水泳池，非常适合带小娃玩沙踩水安全系数极高。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！底部是极其纯净的白沙绝不挂底！使用 1-2号小通心铅挂活沙蚕，主攻大白沙尖 Whiting。"
        },
        "route": "走 Princes Hwy 接 Kingsway 一直向东开往 Cronulla，右转进入 Nicholson Parade 即可看到宽阔的公园。",
        "parking": "Gunnamatta 公园自带超大型全免费停车场。车位充足，停好车后穿过平坦草坪步行 2 分钟到水闸。"
    },
    {
        "name": "Clarkes Point Reserve & Woolwich Dock",
        "region": "Woolwich (中北区河口)",
        "type": "双河交汇岬角石墙 / 废弃旧船坞",
        "sheltered": True, "tide_delay": 2,
        "active_fish": "Bream（鳊鱼）、Flathead（牛鳅）、Leatherjacket（剥皮鱼）、Squid（大鱿鱼）",
        "fish_tags": ["鳊鱼", "牛鳅", "剥皮鱼", "鱿鱼"],
        "best_window": "🌅 傍晚黄昏到入夜。处于双河交汇大拐弯处，流水交汇，饵鱼极其丰富。",
        "family_friendly": "⭐⭐⭐⭐⭐ (野餐天花板) 悉尼最顶级的全景草坪公园之一。拥有大量全免费高级 BBQ 电炉、全无障碍推车绿道、超大树荫。妈妈野餐，爸爸钓鱼，绝美体验！",
        "supported_methods": ["Running Sinker (活铅沉底)", "无铅漂钓", "木虾抽鱿鱼"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "👍 推荐！向两河交汇处的深水主槽抛投 Running Sinker 钓组，主攻沿河上游漫游的肥美 Flathead 牛鳅。",
            "无铅漂钓": "👍 推荐！在旧石墙根打碎面包屑，无铅挂鸡肉慢沉，专门狙击藏在石墙结构洞穴里的大 Bream。",
            "木虾抽鱿鱼": "👍 推荐！在右侧干船坞下方的碎石乱草丛附近，常有小群 Squid 聚集。"
        },
        "route": "走 Victoria Rd，在 Hunters Hill 拐入 Church St，顺着开到底进入 Woolwich Road 一直走到尽头岬角。",
        "parking": "公园内部建有非常宽阔的多功能公共停车场，部分车位免费 2 小时，夜间停车大把车位且全免费。"
    },
    {
        "name": "Cabarita Park Wharf",
        "region": "Cabarita (内西区河道)",
        "type": "内河主干道轮渡码头旁石墙",
        "sheltered": True, "tide_delay": 12,
        "active_fish": "Bream（鳊鱼）、Flathead（牛鳅）、Jewfish（皇冠鲊）",
        "fish_tags": ["鳊鱼", "牛鳅", "皇冠鲊"],
        "best_window": "🕒 夜间涨潮满潮前 2 小时。白天轮渡频繁，深夜河面静谧是大物靠岸猎食黄金期。",
        "family_friendly": "⭐⭐⭐⭐⭐ (内西区遛娃首选) 公园自带儿童水上嬉水喷泉、大型儿童游乐场、大量遮阳大树、全平整无障碍推车步道、免费 BBQ 电炉及意式咖啡馆。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！在轮渡码头右侧的天然乱石挡土墙边缘用活铅沉底挂整条河虾，主攻大牛鳅和红眼大 Bream。"
        },
        "route": "走 Parramatta Road 或 Great North Road，拐入 Cabarita Road 一直开到半岛最底部的 Cabarita Park 仓库里。",
        "parking": "公园内部配有超大型有划线停车场。白天收费，傍晚和夜钓时停止收费且车位极度充裕。"
    },
    {
        "name": "Kissing Point Park & Wharf",
        "region": "Ryde (西区内河)",
        "type": "内河亲水石墙 / 浅滩乱石结合部",
        "sheltered": True, "tide_delay": 20,
        "active_fish": "Bream（鳊鱼）、Flathead（牛鳅）",
        "fish_tags": ["鳊鱼", "牛鳅"],
        "best_window": "🌅 傍晚黄昏到晚上 10 点。随着潮水漫上内西区浅滩，蠕虫活跃，鱼群会进滩抢食。",
        "family_friendly": "⭐⭐⭐⭐⭐ (华人老钓友最爱) 建有高标准封闭式软地基儿童大型游乐场、多台免费现代化 BBQ 电炉、平整河畔漫步道。岸边全建有安全护栏，极度适合全家出动。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！完全面向内河沙泥结合部，使用 Running Sinker 钓组挂大虾肉或者鱼肉，主攻西区红眼大 Bream。"
        },
        "route": "走 Victoria Road，在 Ryde 区域拐入 Morrison Road，再转进 Waterview Street 开到底即可。",
        "parking": "公园自带大型全免费公共停车场。周中傍晚和周末夜钓时车位极其空旷，下车走 10 米即开钓。"
    },
    {
        "name": "Lyne Park & Rose Bay Public Jetty",
        "region": "Rose Bay (东区高端湾区)",
        "type": "高档内湾浅滩沙地 / 公众小栈桥",
        "sheltered": True, "tide_delay": 0,
        "active_fish": "Whiting（大沙尖）、Bream（鳊鱼）、Flathead（牛鳅）、Squid（大鱿鱼）",
        "fish_tags": ["沙尖", "鳊鱼", "牛鳅", "鱿鱼"],
        "best_window": "🕒 涨潮顶峰（High Tide Apex）。东区清澈的洋流会把大批大沙尖顶入 Lyne Park 岸边的优质浅沙滩区。",
        "family_friendly": "⭐⭐⭐⭐⭐ (看水上飞机起降) 拥有全围栏封闭式高级儿童乐园（极度安全）、多台高规格 BBQ 电炉、无敌海景餐厅。大片平整草地推车遛娃完美无缺。",
        "supported_methods": ["Running Sinker (活铅沉底)", "木虾抽鱿鱼"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！站在小栈桥上用 2号轻通心铅抛向草床与沙地交界，挂新鲜沙蚕，主攻东区拉力惊人的大 Whiting。",
            "木虾抽鱿鱼": "👍 推荐！栈桥下方长满海草，夜间灯光柔和，用 2.0号慢沉小木虾常有本地小鱿鱼咬钩。"
        },
        "route": "从 City 沿 New South Head Road 一路向东开，看到大片草坪和水上飞机码头即是 Lyne Park。",
        "parking": "内部配有两个超大型公共停车场，提供大把免费 2 小时或 4 小时车位，推婴儿车非常省力。"
    },
    {
        "name": "The Spit Bridge (Seaforth侧桥底石坝)",
        "region": "Seaforth (北区瓶颈主航道)",
        "type": "极深水道天然瓶颈石墙 (Deep Channel Wall)",
        "sheltered": True, "tide_delay": 10,
        "active_fish": "Yellowtail Kingfish（黄尾师）、Australian Salmon（三文鱼）、Tailor（蓝鱼）、Squid（大鱿鱼）",
        "fish_tags": ["黄尾师", "三文鱼", "蓝鱼", "鱿鱼"],
        "best_window": "🕒 潮水刚刚开始转舵停流的半小时（Slack Water）。激流稍微放缓，是路亚大物和抽大鱿鱼最好控线的黄金瞬间。",
        "family_friendly": "⭐⭐⭐ (风景优美但无游乐场) 桥底连接 Ellery Wentworth Park，拥有大片看海绿草地。环境极其干净，100%全平整，推婴儿车走去亲水石坝很方便。无固定 BBQ 及儿童滑梯。",
        "supported_methods": ["路亚大物", "木虾抽鱿鱼"],
        "method_tips": {
            "路亚大物": "🎯 顶级推荐！北区老司机的重路亚圣地。站在石坝上用 30-40g 铁板抛向主激流区拦截大 Kingfish！",
            "木虾抽鱿鱼": "🎯 顶级推荐！桥底两侧水深且藏有深水海草床，停流时用 3.0号重木虾切入深水慢抽，主攻怪兽大鱿鱼。"
        },
        "route": "走 Spit Road 北上过 Spit Bridge 大桥，过桥后红绿灯立刻左转下山切入 Seaforth 侧桥底。",
        "parking": "桥底公园配有专属划线 Council 收费停车场（可用手机缴费）。停好车后，推车走 2 分钟即可到达作钓区。"
    },
    {
        "name": "Little Manly Point",
        "region": "Manly (北区岬角内侧)",
        "type": "港内深水水泥码头 / 亲水石护栏",
        "sheltered": True, "tide_delay": 2,
        "active_fish": "Squid（大鱿鱼）、Bream（鳊鱼）、Leatherjacket（剥皮鱼）、Yellowtail Kingfish（黄尾师）",
        "fish_tags": ["鱿鱼", "鳊鱼", "剥皮鱼", "黄尾师"],
        "best_window": "🌅 黎明破晓前 1 小时至上午 9 点。外海洋流会将高含氧量海水推入这个拐角，是钓鱿鱼和路亚的绝妙窗口。",
        "family_friendly": "⭐⭐⭐⭐⭐ (隐秘遛娃宝地) 拥有现代化高滑梯儿童乐园、免费公共高级 BBQ 电炉、全平整无障碍环绕绿道。水泥作钓区建有完备极其安全的高防护栏，推婴儿车极度省心！",
        "supported_methods": ["木虾抽鱿鱼", "Running Sinker (活铅沉底)", "无铅漂钓"],
        "method_tips": {
            "木虾抽鱿鱼": "🎯 顶级推荐！水泥码头前方是深水藻礁交错带。使用 2.5号木虾，是北区摸大鱿鱼的终极高产基地！",
            "Running Sinker (活铅沉底)": "👍 推荐！用轻铅 Running Sinker 钓组向乱石边缘抛投，能钓到个头极大的深湾青衣和肥 bream。"
        },
        "route": "走 Military Rd 接 Condamine St 向 Manly 方向开，转入 Stuart Street 一直开到底。",
        "parking": "Little Manly Point Reserve 内部自带一个超大型全免费公共停车场（不限时或限时 4 小时）。车位极多好停。"
    },
    {
        "name": "Narrabeen Lagoon (湖口内侧平滩)",
        "region": "Narrabeen (北部大泻湖)",
        "type": "半封闭型泻湖内口 / 平缓纯沙平滩",
        "sheltered": True, "tide_delay": 30,
        "active_fish": "Flathead（牛鳅）、Whiting（大沙尖）、Bream（鳊鱼）",
        "fish_tags": ["牛鳅", "沙尖", "鳊鱼"],
        "best_window": "🕒 满潮退三分至干潮底的前 2 小时。内湖庞大积水带着虾苗涌入大洋，Flathead 会在沙窝里疯狂埋伏接食。",
        "family_friendly": "⭐⭐⭐⭐⭐ (家庭度假天花板) 环绕大泻湖建有数公里长、完美平整无阶梯的胶质遛娃道。遍布免费高级 BBQ 电炉群、遮阳亭。水流极为清澈平缓且没有大浪，孩子可以完全放飞挖沙。",
        "supported_methods": ["Running Sinker (活铅沉底)"],
        "method_tips": {
            "Running Sinker (活铅沉底)": "🎯 顶级推荐！底部是清一色镜面细沙，100%绝不挂底！带上你的 2-4号通心铅钓组，一边散步一边缓缓拖底收线，趴在泥沙里的大 Flathead 牛鳅极其疯狂！"
        },
        "route": "沿着 Pittwater Road 向北开，过 Narrabeen 桥立刻左转切入 Lake Park Road 绕到湖口内侧。",
        "parking": "湖口沿线配套建有数个极其宽阔的大型停车场。可用手机 App 购买临时车位，位置充足。"
    }
]

# ==========================================
# 5. 前端界面布局与日期联动选项卡
# ==========================================
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🎣 悉尼钓鱼助手 Pro</h1>", unsafe_allow_html=True)
st.markdown("---")

forecast_result = get_sydney_marine_data_3days()
days_data = forecast_result['days']

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
        
        # 布局
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
        
        # 顶部筛选区域
        st.subheader("🔍 智能筛选钓点")
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            selected_method = st.selectbox(
                "选择钓法：",
                ["全部钓法显示", "无铅漂钓", "Running Sinker (活铅沉底)", "路亚大物", "木虾抽鱿鱼"],
                key=f"method_filter_{idx}"
            )
            
        with filter_col2:
            selected_fish = st.selectbox(
                "选择目标鱼种：",
                ["全部鱼种显示", "鳊鱼", "牛鳅", "沙尖", "鱿鱼", "黄尾师", "蓝鱼", "三文鱼", "黑毛", "皇冠鲊", "剥皮鱼", "蓝唇鱼"],
                key=f"fish_filter_{idx}"
            )
            
        st.markdown("---")
        st.subheader(f"📍 匹配钓点及出行打分 (当前已扩容至 20 个大钓点)")
        
        # ==========================================
        # 6. 核心联合智能过滤与打分算法
        # ==========================================
        visible_count = 0
        
        for spot in DEFAULT_SPOTS:
            if selected_method != "全部钓法显示" and selected_method not in spot['supported_methods']:
                continue
                
            if selected_fish != "全部鱼种显示" and selected_fish not in spot['fish_tags']:
                continue
                
            visible_count += 1
            
            # 【安全网防崩溃改进】防范 method_tips 的 KeyError
            method_key = selected_method if selected_method != "全部钓法显示" else spot['supported_methods'][0]
            method_guide = spot['method_tips'].get(method_key, "该钓点不太适合此钓法，建议在下方查看其他专属推荐。")
            
            status = "✅ 极力推荐"
            score = "⭐⭐⭐⭐⭐"
            advice = "此日海况温和，该钓点非常符合您的作钓需求，祝爆护！"
            
            # 计算专属潮汐时间
            spot_tides = []
            for i, bt in enumerate(base_tides):
                real_time = bt + timedelta(minutes=spot['tide_delay'])
                t_type = "满潮 🟢" if i % 2 == 0 else "干潮 🔵"
                spot_tides.append(f"{t_type}`{real_time.strftime('%H:%M')}`")
            
            # 外海风浪硬核打分拦截
            if not spot['sheltered'] and (day_data['swell_height'] > 1.3 or day_data['wind'] > 20):
                status = "❌ 极度危险 (不建议前往)"
                score = "⭐"
                advice = f"🚨 警告：外海浪涌预计达 {day_data['swell_height']}米！该钓点直面太平洋，大浪极易卷人，全家出行请立刻取消，改去高星级内湾避风港！"
            elif spot['sheltered'] and (day_data['swell_height'] > 1.4 or day_data['wind'] > 22):
                status = "⚠️ 谨慎前往"
                score = "⭐⭐⭐"
                advice = "此日悉尼阵风较大。虽是内湾避风港，但顶风抛投体感一般，请选择背风建筑物或大桥下方作钓。"
        
            # 渲染前端
            with st.expander(f"{score} {spot['name']} —— {status}"):
                st.write(f"**🌍 所属区域**：`{spot['region']}` | **📍 地形**：`{spot['type']}`")
                # 【安全网防崩溃改进】使用 .get() 确保绝对不会引发 KeyError
                st.markdown(f"**👨‍👩‍👧‍👦 家人友好度 (遛娃/BBQ)**：{spot.get('family_friendly', '⭐⭐⭐ 暂无该钓点家庭设施的具体情报。')}")
                st.write(f"**🐟 今日活跃鱼种**：`{spot['active_fish']}`")
                st.write(f"**⏱️ 最佳作钓窗口**：{spot['best_window']}")
                st.write(f"**⏰ 钓点专属潮汐推算**：{' | '.join(spot_tides)}")
                st.markdown(f"**💡 当前钓法实战建议 ({method_key})**：\n> {method_guide}")
                st.write(f"**🚗 自驾路线**：{spot['route']}")
                st.info(f"**🅿️ 停车方案**：{spot['parking']}")
                st.warning(f"**⚠️ 针对当前海况的安全劝告**：{advice}")
                
        if visible_count == 0:
            st.info("ℹ️ 暂无完全满足当前双重筛选条件的钓点，建议您放宽筛选条件再试。")

st.markdown("---")
st.caption("🚨 提示：海边钓鱼具有一定风险，出行前请务必穿戴好救生衣与防滑鞋。")
