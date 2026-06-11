import asyncio
import os
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler

# 獨立嘅同步搜尋函數，轉用 Tavily 官方 API，永不被 Block！
def search_target_urls(query: str):
    urls = []
    try:
        tavily_key = os.getenv("TAVILY_API_KEY", "")
        if not tavily_key:
            print("❌ 系統缺少 TAVILY_API_KEY")
            return urls
            
        client = TavilyClient(api_key=tavily_key)
        # 使用 advanced 深度搜尋模式，攞最精準嘅頭 2 個網址
        response = client.search(query, search_depth="advanced", max_results=2)
        
        for result in response.get('results', []):
            urls.append(result['url'])
            
    except Exception as e:
        print(f"Tavily API 搜尋發生錯誤: {e}")
    return urls

async def perform_deep_research(chat_id, context, query: str, **kwargs):
    """
    深度研究工具 (Tavily 官方 API + Crawl4AI 終極極速版)
    【⚠️ 系統嚴厲警告】：參數 query 必須填寫具體關鍵字，絕對禁止填寫 "query" 這個單字！
    """
    print(f"🕵️‍♂️ [深度研究] 啟動：{query}")
    
    # 🎯 防呆機制：防止 AI 大腦短路
    if query.strip().lower() == "query":
        return "❌ 系統攔截：你個 AI 大腦短路啦！參數 query 填錯咗做 'query'，請重新調用並填入真正要搵嘅關鍵字！"
        
    try:
        # 1. 透過 Tavily API 獲取網址 (100% 繞過 Google 防爬蟲)
        urls = await asyncio.to_thread(search_target_urls, query)
        
        if not urls:
            return "❌ 深度研究失敗：Tavily API 搵唔到相關網址，或者未設定 TAVILY_API_KEY。"
            
        report_data = f"🔍 成功透過 Tavily API 搵到以下來源，開始極速讀取：\n{urls}\n\n"
        
        # 2. 啟動 Crawl4AI 隱形瀏覽器爬取內文 (直連，無 Proxy 阻礙)
        async with AsyncWebCrawler() as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url=url)
                    if result.success:
                        report_data += f"【來源】：{url}\n【內容】：{result.markdown[:4000]}\n\n"
                    else:
                        report_data += f"【來源】：{url}\n【狀態】：讀取失敗 ({result.error_message})\n\n"
                except Exception as inner_e:
                    print(f"爬取 {url} 失敗: {inner_e}")
                    
        return f"🕵️‍♂️ 深度研究報告原始數據已獲取：\n\n{report_data}\n\n🚨 請根據以上詳盡資料，立刻為老闆寫出深度分析報告！"

    except Exception as e:
        return f"❌ 深度研究出錯：{str(e)}"
