from skills.export_excel import generate_rebar_excel
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright
import json
import base64
import urllib.parse
import os
from youtube_transcript_api import YouTubeTranscriptApi

from skills.scheduler import schedule_daily_weather
from skills.rebar import calc_rebar_weight
from skills.weather import get_hk_weather_detailed
from skills.reminder import set_reminder
from skills.system_ops import update_from_github

# ================= YouTube 影片字幕提取 (面具突破版) =================
async def analyze_youtube_video(chat_id, context, url: str):
    """獲取 YouTube 影片的字幕/文字稿"""
    print(f"📺 [Debug] 準備獲取 YouTube 字幕：{url}")
    try:
        parsed_url = urllib.parse.urlparse(url)
        if 'youtube.com' in parsed_url.netloc:
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v', [None])[0]
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.lstrip('/')
        else:
            return "❌ 無效的 YouTube 網址。"

        if not video_id:
            return "❌ 無法從網址中提取 Video ID。"

        ytt_api = YouTubeTranscriptApi()
        transcript_list = None
        
        # 🚨 突破封鎖：嘗試讀取本地 Cookies 檔案
        cookie_file = "youtube_cookies.txt"
        if os.path.exists(cookie_file):
            print("🍪 [Debug] 發現 YouTube Cookies 檔案，嘗試戴面具請求...")
            try:
                transcript_list = ytt_api.list(video_id, cookies=cookie_file)
            except Exception as e:
                print(f"⚠️ [Debug] 使用 Cookies 失敗，回退到普通請求：{str(e)}")
                
        # 如果冇 Cookie 或者 Cookie 失敗，就用普通請求試多次
        if not transcript_list:
            transcript_list = ytt_api.list(video_id)
        
        try:
            transcript = transcript_list.find_transcript(['zh-Hant', 'zh-HK', 'zh-Hans', 'zh-CN', 'zh', 'en'])
        except Exception:
            transcript = None
            for t in transcript_list:
                transcript = t
                break
        
        if not transcript:
            return "❌ 呢條影片完全冇提供任何字幕。"

        fetched_transcript = transcript.fetch()
        full_text_list = []
        for entry in fetched_transcript:
            if hasattr(entry, 'text'):
                full_text_list.append(entry.text)
            else:
                full_text_list.append(entry.get('text', ''))
                
        safe_text = " ".join(full_text_list)[:8000] 
        print(f"✅ [Debug] 成功獲取 YouTube 字幕，長度：{len(safe_text)}")
        return f"影片字幕提取成功！內容：\n\n{safe_text}"
    except Exception as e:
        return f"❌ 獲取字幕失敗 (可能 VPS IP 被 YouTube 封鎖)：{str(e)}"

# ================= 全球天氣查詢 =================
async def get_global_weather(chat_id, context, location):
    print(f"🌍 [Debug] 準備查詢天氣：{location}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://wttr.in/{location}?format=j1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    current = data['current_condition'][0]
                    return f"🌍 {location} 天氣數據：氣溫 {current['temp_C']}°C，狀況 {current['weatherDesc'][0]['value']}。"
                return f"❌ API 拒絕連線 (HTTP {resp.status})。"
    except Exception as e: 
        return f"❌ 查詢出錯：{str(e)}"

# ================= 即時網絡搜尋 =================
async def search_web(chat_id, context, query):
    print(f"🔍 [Debug] 準備搜尋新聞：{query}")
    try:
        formatted_query = query.replace(' ', '+')
        url = f"https://news.google.com/rss/search?q={formatted_query}&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        headers = {'User-Agent': 'Mozilla/5.0'}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return f"❌ 網絡拒絕連線 (HTTP {resp.status})。"
                xml_data = await resp.text()
                root = ET.fromstring(xml_data)
                items = root.findall('.//item')
                if not items:
                    return f"❌ 搵唔到關於「{query}」嘅資訊。"

                formatted_results = []
                for item in items[:10]:
                    title = item.findtext('title')
                    pubDate = item.findtext('pubDate')
                    formatted_results.append(f"📰 【{title}】\n🕒 時間：{pubDate}")
                return "以下係最新搜尋結果：\n\n" + "\n\n".join(formatted_results)
    except Exception as e: 
        return f"❌ 搜尋出錯：{str(e)}"

# ================= Playwright 網頁瀏覽 =================
async def browse_website_with_playwright(chat_id, context, url: str):
    print(f"🌐 [Debug] 準備訪問並截圖網頁：{url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={'width': 1280, 'height': 800})
            
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            content = await page.evaluate("document.body.innerText")
            page_title = await page.title()
            
            screenshot_bytes = await page.screenshot(type='jpeg', quality=30, full_page=False)
            base64_encoded = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            await browser.close()
            return json.dumps({
                "type": "webpage_with_screenshot",
                "title": page_title,
                "text": content[:1500],
                "image_base64": base64_encoded
            })
    except Exception as e: 
        return f"❌ 訪問網頁失敗：{str(e)}"

# ================= 工具創建助手 =================
def create_tool(func, name, desc, params, required):
    return {
        "func": func, 
        "schema": {
            "type": "function", 
            "function": {
                "name": name, 
                "description": desc, 
                "parameters": {
                    "type": "object", 
                    "properties": params, 
                    "required": required
                }
            }
        }
    }

# ================= 技能註冊表 =================
AGENT_TOOLS_REGISTRY = {
    "calc_rebar_weight": create_tool(
        func = calc_rebar_weight, 
        name = "calc_rebar_weight", 
        desc = "計算鋼筋的重量。", 
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
        desc = "獲取香港最新天氣。", 
        params = {}, 
        required = []
    ),
    
    "set_reminder": create_tool(
        func = set_reminder, 
        name = "set_reminder", 
        desc = "設定鬧鐘。", 
        params = {
            "minutes": {"type": "number", "description": "等待分鐘數"}, 
            "message": {"type": "string", "description": "提醒內容"}
        }, 
        required = ["minutes", "message"]
    ),
    
    "schedule_daily_weather": create_tool(
        func = schedule_daily_weather, 
        name = "schedule_daily_weather", 
        desc = "設定每日定時天氣報告。", 
        params = {
            "hour": {"type": "integer"}, 
            "minute": {"type": "integer"}
        }, 
        required = ["hour", "minute"]
    ),
    
    "get_global_weather": create_tool(
        func = get_global_weather, 
        name = "get_global_weather", 
        desc = "查詢全球天氣。", 
        params = {
            "location": {"type": "string"}
        }, 
        required = ["location"]
    ),
    
    "search_web": create_tool(
        func = search_web, 
        name = "search_web", 
        desc = "搜尋即時新聞。🚨【極度重要指令】：1. 不要加入年份。2. 無視年份差異，直接作為『今日最新資訊』匯報！", 
        params = {
            "query": {"type": "string"}
        }, 
        required = ["query"]
    ),
    
    "update_from_github": create_tool(
        func = update_from_github, 
        name = "update_from_github", 
        desc = "更新系統代碼。", 
        params = {}, 
        required = []
    ),
    
    "generate_rebar_excel": create_tool(
        func = generate_rebar_excel, 
        name = "generate_rebar_excel", 
        desc = "生成 Excel 報表。", 
        params = {
            "report_name": {"type": "string"}, 
            "records": {
                "type": "array", 
                "items": {
                    "type": "object", 
                    "properties": {
                        "d": {"type": "number"}, 
                        "length": {"type": "number"}, 
                        "qty": {"type": "number"}, 
                        "weight": {"type": "number"}
                    }, 
                    "required": ["d", "length", "qty", "weight"]
                }
            }
        }, 
        required = ["report_name", "records"]
    ),
    
    "browse_website": create_tool(
        func = browse_website_with_playwright, 
        name = "browse_website", 
        desc = "瀏覽網頁並提供截圖。", 
        params = {
            "url": {"type": "string"}
        }, 
        required = ["url"]
    ),
    
    "analyze_youtube_video": create_tool(
        func = analyze_youtube_video, 
        name = "analyze_youtube_video", 
        desc = "獲取 YouTube 字幕。", 
        params = {
            "url": {"type": "string"}
        }, 
        required = ["url"]
    )
}

# 自動生成給 Gemini 大腦的工具清單
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]