import asyncio
from duckduckgo_search import DDGS
import aiohttp
from skills.scheduler import schedule_daily_weather
from skills.rebar import calc_rebar_weight
from skills.weather import get_hk_weather_detailed
from skills.reminder import set_reminder

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

# ================= 新增：即時網絡搜尋函數 (DDG 穩定版) =================
async def search_web(chat_id, context, query):
    """使用 DuckDuckGo 搜尋全球即時資訊與新聞"""
    print(f"🔍 [Debug] 準備使用 DuckDuckGo 搜尋網絡，關鍵字：{query}")
    try:
        def do_search():
            with DDGS() as ddgs:
                # 移除 region 限制，確保全球各國新聞都能獲取
                return list(ddgs.text(query, max_results=5))

        results = await asyncio.to_thread(do_search)

        if not results:
            print(f"⚠️ [Debug] DDG 回傳空白結果")
            return f"❌ 搵唔到關於「{query}」嘅最新資訊。"

        formatted_results = []
        for r in results:
            formatted_results.append(f"📰 【{r.get('title', '無標題')}】\n📝 摘要：{r.get('body', '無內容')}")

        reply_text = "以下係最新嘅網絡搜尋結果，請根據這些資訊總結並回答老闆：\n\n" + "\n\n".join(formatted_results)
        print("✅ [Debug] 成功獲取 DuckDuckGo 搜尋結果")
        return reply_text

    except Exception as e:
        print(f"❌ [Debug] DDG 搜尋出錯：{str(e)}")
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

    # 工具 6：即時網絡搜尋 (打破時空版)
    "search_web": create_tool(
        func = search_web,
        name = "search_web",
        desc = "搜尋即時網絡資訊、新聞、事實查核。當老闆詢問「最新新聞」、「今日發生咩事」時調用此工具。",
        params = {
            "query": {
                "type": "string",
                "description": "【極度重要指令】1. 不要加入年份或日期。2. 由於系統時差原因，搜尋傳回的新聞可能是2024年的，請務必無視年份差異，直接將結果當作『今日最新新聞』向老闆匯報，絕對不要回答『因為是未來日子所以找不到新聞』！"
            }
        },
        required = ["query"]
    )
}

# 自動生成給 Gemini 大腦的工具清單
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]
