import aiohttp
import re
import asyncio

async def perform_deep_research(chat_id, context, query: str):
    """
    深度研究工具：自動搜尋並爬取多個網頁內容，直接生成完整數據供總結。
    """
    print(f"🕵️‍♂️ [深度研究] 啟動：{query}")
    
    # 1. 呼叫現有的 Jina 借刀殺人 API 進行搜尋與讀取
    # 呢度我哋設計一個邏輯：先用 Jina 搜尋，再揀最相關嘅內容
    search_url = f"https://s.jina.ai/{query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers) as resp:
                if resp.status == 200:
                    raw_content = await resp.text()
                    # 截取前 8000 字（Gemini 2.5 Flash 吞得落），確保資料量足夠寫報告
                    final_data = raw_content[:8000]
                    return f"🕵️‍♂️ 深度研究報告原始數據已獲取：\n\n{final_data}\n\n🚨 請根據以上詳盡資料，立刻為老闆寫出深度分析報告，唔准再叫老闆等！"
                else:
                    return f"❌ 深度研究失敗，無法連接搜尋引擎 (HTTP {resp.status})。"
    except Exception as e:
        return f"❌ 深度研究出錯：{str(e)}"
