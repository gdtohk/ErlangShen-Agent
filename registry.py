from skills.export_excel import generate_rebar_excel
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright
import json
import base64
import urllib.parse
from youtube_transcript_api import YouTubeTranscriptApi

from skills.scheduler import schedule_daily_weather
from skills.rebar import calc_rebar_weight
from skills.weather import get_hk_weather_detailed
from skills.reminder import set_reminder
from skills.system_ops import update_from_github

# ================= 新增：YouTube 影片字幕提取 (無差別兜底版) =================
async def analyze_youtube_video(chat_id, context, url: str):
    """獲取 YouTube 影片的字幕/文字稿"""
    print(f"📺 [Debug] 準備獲取 YouTube 字幕：{url}")
    try:
        # 提取 Video ID
        parsed_url = urllib.parse.urlparse(url)
        if 'youtube.com' in parsed_url.netloc:
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v', [None])[0]
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.lstrip('/')
        else:
            return "❌ 無效的 YouTube 網址。"

        if not video_id:
            return "❌ 無法從網址中提取 Video ID。"

        # 獲取影片所有可用的字幕清單
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            # 優先嘗試精準配對中英文
            transcript = transcript_list.find_transcript(['zh-Hant', 'zh-HK', 'zh-Hans', 'zh-CN', 'zh', 'en'])
        except Exception:
            # 【無差別兜底機制】：如果無中英文，直接夾硬攞第一條可用嘅字幕（包含自動生成）
            # 唔使擔心語言問題，Gemini 大腦會自動翻譯並總結
            transcript = None
            for t in transcript_list:
                transcript = t
                break
            
            if not transcript:
                return "❌ 呢條影片真係完全冇提供任何字幕（連自動生成都冇）。"

        # 獲取實際字幕數據
        fetched_transcript = transcript.fetch()
        
        # 將字幕組合成完整文字
        full_text = " ".join([entry['text'] for entry in fetched_transcript])
        
        # 截斷保護 (避免超過大模型 token 限制)
        safe_text = full_text[:15000] 
        
        print(f"✅ [Debug] 成功獲取 YouTube 字幕 (語言: {transcript.language})，長度：{len(safe_text)}")
        return f"影片字幕提取成功！請根據以下內容進行總結或回答：\n\n{safe_text}"
        
    except Exception as e:
        error_msg = f"無法獲取字幕：{str(e)}"
        print(f"❌ [Debug] {error_msg}")
        return error_msg

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

# ================= 升級：具備截圖功能之 Playwright 網頁瀏覽函數 =================
async def browse_website_with_playwright(chat_id, context, url: str):
    """使用 Playwright 訪問網頁，同時獲取文字與截圖"""
    print(f"🌐 [Debug] 準備訪問並截圖網頁：{url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            browser_context = await browser.new_context(viewport={'width': 1280, 'height': 800})
            page = await browser_context.new_page()
            
            await page.goto(url, timeout=15000)
            await page.wait_for_load_state("domcontentloaded")
            
            content = await page.evaluate("document.body.innerText")
            page_title = await page.title()
            
            screenshot_bytes = await page.screenshot(type='jpeg', quality=60, full_page=False)
            base64_encoded = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            await browser.close()
            
            safe_content = content[:2000] if content else "無法提取文字內容"
            print(f"✅ [Debug] 成功獲取 {url} 文字及截圖")
            
            return json.dumps({
                "type": "webpage_with_screenshot",
                "title": page_title,
                "text": safe_content,
                "image_base64": base64_encoded
            })
            
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
        func = browse_website_with_playwright,
        name = "browse_website",
        desc = "當老闆提供一個網址，或需要你上網抓取特定網站的實時資訊時調用此工具。這會啟動無頭瀏覽器去抓取網頁數據，並同步提供網頁截圖供你進行視覺分析。",
        params = {
            "url": {
                "type": "string",
                "description": "要訪問的完整網址 (例如 https://news.ycombinator.com)"
            }
        },
        required = ["url"]
    ),

    "analyze_youtube_video": create_tool(
        func = analyze_youtube_video,
        name = "analyze_youtube_video",
        desc = "當老闆要求你總結或觀看 YouTube 影片時調用。此工具會自動提取影片的精確字幕文本供你分析。",
        params = {
            "url": {
                "type": "string",
                "description": "YouTube 影片完整網址"
            }
        },
        required = ["url"]
    )
}

# 自動生成給 Gemini 大腦的工具清單
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]