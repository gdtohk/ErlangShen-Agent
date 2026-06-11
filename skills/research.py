import aiohttp
import re
import asyncio
import os

async def perform_deep_research(chat_id, context, query: str, **kwargs):
    """
    深度研究工具：自動搜尋並爬取多個網頁內容，直接生成完整數據供總結。
    """
    print(f"🕵️‍♂️ [深度研究] 啟動：{query}")
    
    # 1. 呼叫現有的 Jina 借刀殺人 API 進行搜尋與讀取
    search_url = f"https://s.jina.ai/{query}"
    
    # 讀取 .env 中的 API Key (如果無設定，就會係空字串)
    jina_key = os.getenv("JINA_API_KEY", "")
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    }
    
    # 如果有 API Key，就掛上通行證
    if jina_key:
        headers['Authorization'] = f"Bearer {jina_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers) as resp:
                if resp.status == 200:
                    raw_content = await resp.text()
                    # 截取前 8000 字（Gemini 2.5 Flash 吞得落），確保資料量足夠寫報告
                    final_data = raw_content[:8000]
                    return f"🕵️‍♂️ 深度研究報告原始數據已獲取：\n\n{final_data}\n\n🚨 請根據以上詳盡資料，立刻為老闆寫出深度分析報告，唔准再叫老闆等！"
                elif resp.status == 401:
                    return "❌ 深度研究失敗 (HTTP 401)。未授權，請檢查 .env 檔案內的 JINA_API_KEY 是否正確填寫。"
                elif resp.status == 402:
                    return "❌ 深度研究失敗 (HTTP 402)。Jina API 免費額度或每日限制已達到，請聽日再試，或者改用 search_web 工具。"
                else:
                    return f"❌ 深度研究失敗，無法連接搜尋引擎 (HTTP {resp.status})。"
    except Exception as e:
        return f"❌ 深度研究出錯：{str(e)}"
