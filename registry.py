from skills.export_excel import generate_rebar_excel
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright

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

# ================= 新增：即時網絡搜尋函數 =================
async def search_web(chat_id, context, query):
    """使用 Google News RSS 獲取全球即時新聞，絕對防封鎖"""
    print(f"🔍 [Debug] 準備使用 Google News RSS 搜尋，關鍵字：{query}")
    try:
        formatted_query = query.replace(' ', '+')
        url = f"https://news.google.com/rss/search?q={formatted_query}&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"⚠️ [Debug] RSS 拒絕連線: {resp.status}")
                    return f"❌ 網絡拒絕連線 (HTTP {resp.status})。"

                xml_data = await resp.text()
                root = ET.fromstring(xml_data)
                items = root.findall('.//item')

                if not items:
                    print(f"⚠️ [Debug] RSS 回傳空白結果")
                    return f"❌ 搵唔到關於「{query}」嘅最新資訊。"

                formatted_results = []
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

# ================= 新增：Obscura 網頁瀏覽函數 =================
async def browse_website_with_obscura(chat_id, context, url: str):
    """
    使用 Obscura 無頭瀏覽器訪問網頁並提取純文字內容
    """
    print(f"🌐 [Debug] 準備使用 Obscura 訪問網頁：{url}")
    try:
        async with async_playwright() as p:
            # 連接 VPS 本地的 Obscura 引擎
            browser = await p.chromium.connect_over_cdp("ws://127.0.0.1:9222")
            browser_context = await browser.new_context()
            page = await browser_context.new_page()
            
            await page.goto(url, timeout=15000)
            await page.wait_for_load_state("domcontentloaded")
            
            content = await page.evaluate("document.body.innerText")
            page_title = await page.title()
            
            await browser.close()
            
            safe_content = content[:3000] if content else "無法提取文字內容"
            
            print(f"✅ [Debug] 成功獲取 {url} 網頁內容")
            return f"成功訪問【{page_title}】({url})\n\n提取內容摘要：\n{safe_content}"
            
    except Exception as e:
        error_msg = f"訪問網頁 {url} 失敗，錯誤信息：{str(e)}"
        print(f"❌ [Debug] {error_msg}")
        return error_msg

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
    
    "get_hk_weather_detailed": create_tool(
        func = get_hk_weather_detailed,
        name = "get_hk_weather_detailed",
        desc = "獲取香港最新天氣。當老闆問天氣、會不會下雨時調用。",
        params = {},
        required = []
    ),

    "set_reminder": create_tool(
        func = set_reminder,
        name = "set_reminder",
        desc = "設定未來的鬧鐘。",
        params = {
            "minutes": {"type": "number", "description": "等待的分鐘數。"},
            "message": {"type": "string", "description": "提醒內容"}
        },
        required = ["minutes", "message"]
    ),

    "schedule_daily_weather": create_tool(
        func = schedule_daily_weather,
        name = "schedule_daily_weather",
        desc = "設定每天固定時間自動發送天氣報告。",
        params = {
            "hour": {"type": "integer", "description": "小時"},
            "minute": {"type": "integer", "description": "分鐘"}
        },
        required = ["hour", "minute"]
    ),

    "get_global_weather": create_tool(
        func = get_global_weather,
        name = "get_global_weather",
        desc = "查詢全球天氣。",
        params = {
            "location": {"type": "string", "description": "純英文城市名稱"}
        },
        required = ["location"]
    ),

    "search_web": create_tool(
        func = search_web,
        name = "search_web",
        desc = "搜尋即時網絡資訊、新聞。",
        params = {
            "query": {"type": "string", "description": "搜尋關鍵字"}
        },
        required = ["query"]
    ),
    
    "update_from_github": create_tool(
        func = update_from_github,
        name = "update_from_github",
        desc = "從 GitHub 拉取最新程式碼更新。",
        params = {},
        required = []
    ),

    "generate_rebar_excel": create_tool(
        func = generate_rebar_excel,
        name = "generate_rebar_excel",
        desc = "當老闆要求出 Excel 報表時調用。🚨【強制指令】：請直接在你的大腦中，使用公式 (d**2 / 162.2 * 長度 * 數量) 心算計好所有鋼筋的重量，然後將最終數據直接傳入此工具！絕對不要調用 calc_rebar_weight，必須一步到位出表！",
        params = {
            "report_name": {"type": "string", "description": "報表名稱"},
            "records": {
                "type": "array",
                "description": "鋼筋數據清單。",
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
    ),

    "browse_website": create_tool(
        func = browse_website_with_obscura,
        name = "browse_website",
        desc = "當老闆提供一個網址，或需要你上網抓取特定網站的實時資訊時調用此工具。這會啟動無頭瀏覽器去抓取網頁數據。",
        params = {
            "url": {
                "type": "string",
                "description": "要訪問的完整網址 (例如 https://news.ycombinator.com)"
            }
        },
        required = ["url"]
    )
}

# 自動生成給 Gemini 大腦的工具清單
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]