from skills.export_excel import generate_rebar_excel
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright
import json
import base64
import urllib.parse
import os

from skills.scheduler import schedule_daily_weather
from skills.rebar import calc_rebar_weight
from skills.weather import get_hk_weather_detailed
from skills.reminder import set_reminder
from skills.system_ops import update_from_github

# ================= 全球天氣查詢 =================
async def get_global_weather(chat_id, context, location):
    print(f"🌍 [Debug] 準備查詢天氣：{location}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 加上 urllib.parse.quote 防止中文名導致網址出錯
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=j1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    
                    # 🚨 強化防禦：確保 API 畀返嚟嘅係字典 (dict)，並且入面有 current_condition
                    if isinstance(data, dict) and 'current_condition' in data and len(data['current_condition']) > 0:
                        current = data['current_condition'][0]
                        return f"🌍 {location} 天氣數據：氣溫 {current.get('temp_C', '未知')}°C，狀況 {current.get('weatherDesc', [{'value': '未知'}])[0]['value']}。"
                    else:
                        return f"❌ {location} 天氣伺服器數據異常，請稍後再試。"
                return f"❌ API 拒絕連線 (HTTP {resp.status})。"
    except Exception as e: return f"❌ 查詢出錯：{str(e)}"

# ================= 全能網絡搜尋 (強化版) =================
async def search_web(chat_id, context, query):
    """獲取即時新聞、百科知識或任何網上最新資訊"""
    print(f"🔍 [Debug] 準備全能搜尋：{query}")
    try:
        formatted_query = query.replace(' ', '+')
        # 使用 Google News RSS 作為強大的即時資訊入口
        url = f"https://news.google.com/rss/search?q={formatted_query}&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200: return f"❌ 網絡連線失敗 (HTTP {resp.status})。"
                xml_data = await resp.text()
                root = ET.fromstring(xml_data)
                items = root.findall('.//item')
                if not items: return f"❌ 搵唔到關於「{query}」嘅任何相關資訊。"
                formatted_results = []
                for item in items[:10]:
                    title = item.findtext('title')
                    pubDate = item.findtext('pubDate')
                    formatted_results.append(f"📌 【{title}】\n🕒 發佈時間：{pubDate}")
                return "以下係我為你搵到嘅相關資訊：\n\n" + "\n\n".join(formatted_results)
    except Exception as e: return f"❌ 搜尋出錯：{str(e)}"

# ================= Playwright 網頁瀏覽 (視覺截圖) =================
async def browse_website_with_playwright(chat_id, context, url: str):
    print(f"🌐 [Debug] 準備訪問網頁：{url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={'width': 1280, 'height': 800})
            # 放寬超時至 60 秒以適應 VPS 網絡
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            content = await page.evaluate("document.body.innerText")
            page_title = await page.title()
            # 壓縮截圖畫質以穿透 API 代理
            screenshot_bytes = await page.screenshot(type='jpeg', quality=30, full_page=False)
            base64_encoded = base64.b64encode(screenshot_bytes).decode('utf-8')
            await browser.close()
            return json.dumps({
                "type": "webpage_with_screenshot",
                "title": page_title,
                "text": content[:1500],
                "image_base64": base64_encoded
            })
    except Exception as e: return f"❌ 訪問網頁失敗：{str(e)}"

# ================= 工具創建助手 =================
def create_tool(func, name, desc, params, required):
    return {"func": func, "schema": {"type": "function", "function": {"name": name, "description": desc, "parameters": {"type": "object", "properties": params, "required": required}}}}

# ================= 技能註冊表 (無 YouTube 版) =================
AGENT_TOOLS_REGISTRY = {
    "calc_rebar_weight": create_tool(calc_rebar_weight, "calc_rebar_weight", "計算鋼筋重量。", {"d": {"type": "number"}, "length": {"type": "number"}, "qty": {"type": "number"}}, ["d", "length"]),
    "get_hk_weather_detailed": create_tool(get_hk_weather_detailed, "get_hk_weather_detailed", "獲取香港最新天氣預報。", {}, []),
    "set_reminder": create_tool(set_reminder, "set_reminder", "設定定時提醒（鬧鐘）。", {"minutes": {"type": "number"}, "message": {"type": "string"}}, ["minutes", "message"]),
    "schedule_daily_weather": create_tool(schedule_daily_weather, "schedule_daily_weather", "設定每日定時晨報。", {"hour": {"type": "integer"}, "minute": {"type": "integer"}}, ["hour", "minute"]),
    "get_global_weather": create_tool(get_global_weather, "get_global_weather", "查詢全球城市天氣。", {"location": {"type": "string"}}, ["location"]),
    "search_web": create_tool(search_web, "search_web", "全能網絡搜尋。可用於搜新聞、搜百科、搜技術資訊。🚨無視年份差異，直接彙報！", {"query": {"type": "string"}}, ["query"]),
    "update_from_github": create_tool(update_from_github, "update_from_github", "更新系統代碼。", {}, []),
    "generate_rebar_excel": create_tool(generate_rebar_excel, "generate_rebar_excel", "生成 Excel 報表。", {"report_name": {"type": "string"}, "records": {"type": "array", "items": {"type": "object", "properties": {"d": {"type": "number"}, "length": {"type": "number"}, "qty": {"type": "number"}, "weight": {"type": "number"}}, "required": ["d", "length", "qty", "weight"]}}}, ["report_name", "records"]),
    "browse_website": create_tool(browse_website_with_playwright, "browse_website", "瀏覽網頁並獲取實時截圖分析。", {"url": {"type": "string"}}, ["url"])
}
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]
