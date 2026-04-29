from skills.export_excel import generate_rebar_excel
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from skills.scheduler import schedule_daily_weather
from skills.rebar import calc_rebar_weight
from skills.weather import get_hk_weather_detailed
from skills.reminder import set_reminder
from skills.system_ops import update_from_github

# ================= 新增：全球天氣查詢函數 =================
async def get_global_weather(chat_id, context, location):
    """查詢全球天氣的工具函數"""
    print(f"🌍 [Debug] 準備查詢天氣，Gemini 傳入的城市為：{location}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        url = f"https://wttr.in/{location}?format=j1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    current = data['current_condition'][0]
                    temp = current['temp_C']
                    desc = current['weatherDesc'][0]['value']
                    print(f"✅ [Debug] 成功獲取 {location} 天氣：{temp}°C, {desc}")
                    return f"🌍 {location} 天氣數據：氣溫 {temp}°C，狀況 {desc}。"
                else:
                    error_msg = f"❌ API 拒絕連線 (HTTP {resp.status})，查唔到 {location} 嘅天氣。"
                    print(f"⚠️ [Debug] {error_msg}")
                    return error_msg
    except Exception as e:
        print(f"❌ [Debug] 查詢 {location} 出錯：{str(e)}")
        return f"❌ 查詢出錯：{str(e)}"

# ================= 新增：即時網絡搜尋函數 (Google News RSS 防封鎖版) =================
async def search_web(chat_id, context, query):
    """使用 Google News RSS 獲取全球即時新聞，絕對防封鎖"""
    print(f"🔍 [Debug] 準備使用 Google News RSS 搜尋，關鍵字：{query}")
    try:
        # 將關鍵字中的空格轉換為 URL 格式
        formatted_query = query.replace(' ', '+')
        # Google News RSS 官方連結 (hl=zh-HK 代表繁體中文)
        url = f"https://news.google.com/rss/search?q={formatted_query}&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"⚠️ [Debug] RSS 拒絕連線: {resp.status}")
                    return f"❌ 網絡拒絕連線 (HTTP {resp.status})。"

                # 讀取 XML 數據
                xml_data = await resp.text()
                
                # 解析 XML 結構
                root = ET.fromstring(xml_data)
                items = root.findall('.//item')

                if not items:
                    print(f"⚠️ [Debug] RSS 回傳空白結果")
                    return f"❌ 搵唔到關於「{query}」嘅最新資訊。"

                formatted_results = []
                # 提取最頂部的 10 條新聞
                for item in items[:10]:
                    title = item.findtext('title')
                    pubDate = item.findtext('pubDate')
                    formatted_results.append(f"📰 【{title}】\n🕒 時間：{pubDate}")

                reply_text = "以下係最新嘅 Google News 搜尋結果，請根據這些資訊總結並回答老闆：\n\n" + "\n\n".join(formatted_results)
                print("✅ [Debug] 成功獲取 Google News RSS 結果")
                return reply_text

    except Exception as e:
        print(f"❌ [Debug] RSS 搜尋出錯：{str(e)}")
        return f"❌ 網絡搜尋出錯：{str(e)}"

# ================= 工具創建助手 =================
def create_tool(func, name, desc, params, required):
    return {
        "func": func,
        "schema": {
            "type": "function",
            "function": {
                "name": name,
                "description": desc,
                "parameters": {"type": "object", "properties": params, "required": required}
            }
        }
    }

# ================= 技能註冊表 =================
AGENT_TOOLS_REGISTRY = {
    # 工具 1：鋼筋計算
    "calc_rebar_weight": create_tool(
        func = calc_rebar_weight,
        name = "calc_rebar_weight",
        desc = "計算鋼筋的重量。當詢問鋼筋重量時調用。",
        params = {
            "d": {"type": "number", "description": "直徑 (mm)"},
            "length": {"type": "number", "description": "長度 (m)"},
            "qty": {"type": "number", "description": "數量"}
        },
        required = ["d", "length"]
    ),
    
    # 工具 2：天氣預報 (香港本地)
    "get_hk_weather_detailed": create_tool(
        func = get_hk_weather_detailed,
        name = "get_hk_weather_detailed",
        desc = "獲取香港最新天氣。當老闆問天氣、會不會下雨時調用。",
        params = {},
        required = []
    ),

    # 工具 3：定時提醒鬧鐘
    "set_reminder": create_tool(
        func = set_reminder,
        name = "set_reminder",
        desc = "設定未來的鬧鐘。當老闆要求「发信息给我」、「通知我」、「提醒我」、「叫我」時調用。",
        params = {
            "minutes": {
                "type": "number", 
                "description": "距離現在需要等待的分鐘數。請讀取系統注入的【當前香港時間】，心算出老闆指定的目標時間距離現在還有幾分鐘，並填入此數值。"
            },
            "message": {
                "type": "string", 
                "description": "要提醒的事情內容，例如『喝水』、『開會』"
            }
        },
        required = ["minutes", "message"]
    ),

    # 工具 4：每天定時天氣匯報
    "schedule_daily_weather": create_tool(
        func = schedule_daily_weather,
        name = "schedule_daily_weather",
        desc = "設定每天固定時間自動發送天氣報告。當老闆要求「每天早上X點報告天氣」時調用。",
        params = {
            "hour": {"type": "integer", "description": "小時 (0-23)，例如早上5點填5"},
            "minute": {"type": "integer", "description": "分鐘 (0-59)，例如半填30"}
        },
        required = ["hour", "minute"]
    ),

    # 工具 5：全球天氣預報
    "get_global_weather": create_tool(
        func = get_global_weather,
        name = "get_global_weather",
        desc = "查詢全球天氣。當老闆詢問「香港以外」的世界各地城市天氣時調用此工具。",
        params = {
            "location": {
                "type": "string",
                "description": "【極度重要指令】必須將城市名稱翻譯成純英文（例如：Zhaoqing, Tokyo, London），絕不能傳入中文！"
            }
        },
        required = ["location"]
    ),

    # 工具 6：即時網絡搜尋 (Google News RSS 防封鎖版 + 打破時空緊箍咒)
    "search_web": create_tool(
        func = search_web,
        name = "search_web",
        desc = "搜尋即時網絡資訊、新聞、事實查核。當老闆詢問「最新新聞」、「今日發生咩事」時調用此工具。",
        params = {
            "query": {
                "type": "string",
                "description": "【極度重要指令】1. 不要加入年份或日期。2. 由於系統時差原因，搜尋傳回的新聞可能是舊的，請務必無視年份差異，直接將結果當作『今日最新新聞』向老闆匯報，絕對不要回答『因為是未來日子所以找不到新聞』！"
            }
        },
        required = ["query"]
    ),
    
    # 工具 7：系統更新 (Git Pull)
    "update_from_github": create_tool(
        func = update_from_github,
        name = "update_from_github",
        desc = "從 GitHub 拉取最新程式碼更新。當老闆要求「更新系統」、「拉取最新代碼」、「git pull」或「檢查更新」時調用。",
        params = {},
        required = []
    ),

    # 工具 8：生成 Excel 報表
    "generate_rebar_excel": create_tool(
        func = generate_rebar_excel,
        name = "generate_rebar_excel",
        desc = "當老闆要求出 Excel 報表時調用。🚨【強制指令】：請直接在你的大腦中，使用公式 (d**2 / 162.2 * 長度 * 數量) 心算計好所有鋼筋的重量，然後將最終數據直接傳入此工具！絕對不要調用 calc_rebar_weight，必須一步到位出表！",
        params = {
            "report_name": {
                "type": "string", 
                "description": "報表名稱，例如：B區大陣鋼筋表"
            },
            "records": {
                "type": "array",
                "description": "鋼筋數據清單。每個項目必須包含 d, length, qty, weight 四個數值。",
                "items": {
                    "type": "object",
                    "properties": {
                        "d": {"type": "number", "description": "直徑 (mm)"},
                        "length": {"type": "number", "description": "長度 (m)"},
                        "qty": {"type": "number", "description": "數量"},
                        "weight": {"type": "number", "description": "重量 (kg)"}
                    },
                    "required": ["d", "length", "qty", "weight"]
                }
            }
        },
        required = ["report_name", "records"]
    )
}

# 自動生成給 Gemini 大腦的工具清單
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]
