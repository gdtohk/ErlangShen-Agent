import asyncio
import os
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler

# 獨立嘅同步搜尋函數，專攻外國科技圈同討論區
def search_trend_urls(query: str):
    urls = []
    try:
        tavily_key = os.getenv("TAVILY_API_KEY", "")
        if not tavily_key:
            print("❌ 系統缺少 TAVILY_API_KEY")
            return urls
            
        client = TavilyClient(api_key=tavily_key)
        
        # 核心靈魂：限定只搜尋 Reddit, Hacker News, X (Twitter), YouTube，兼且限定過去 30 日
        response = client.search(
            query=f"{query} discussions opinions",
            search_depth="advanced",
            include_domains=["reddit.com", "news.ycombinator.com", "twitter.com", "youtube.com"],
            max_results=3,
            days=30  # Tavily API 神級功能：直接限制搜尋過去 30 日內嘅內容
        )
        
        for result in response.get('results', []):
            urls.append(result['url'])
            
    except Exception as e:
        print(f"輿情雷達搜尋發生錯誤: {e}")
    return urls

async def perform_last30days_research(chat_id, context, topic: str, **kwargs):
    """
    全網輿情與趨勢雷達 (Last 30 Days 工具)：
    專門搜尋過去 30 日內，外國網民喺 Reddit, Hacker News, X (Twitter), YouTube 上面對某個主題的真實討論與民意。
    """
    print(f"📡 [輿情雷達] 啟動：{topic}")
    
    if topic.strip().lower() in ["topic", "query"]:
        return "❌ 系統攔截：請輸入真正要分析嘅關鍵字，唔好填變數名稱！"
        
    try:
        # 1. 透過 Tavily API 獲取過去 30 日嘅熱門討論網址
        urls = await asyncio.to_thread(search_trend_urls, topic)
        
        if not urls:
            return f"📡 輿情雷達暫時搵唔到過去 30 日內關於「{topic}」嘅外國熱門討論。"
            
        report_data = f"📡 成功鎖定以下外國熱門討論區來源，開始抽取網民意見：\n{urls}\n\n"
        
        # 2. 啟動 Crawl4AI 隱形瀏覽器爬取討論區留言
        async with AsyncWebCrawler() as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url=url)
                    if result.success:
                        # 討論區通常廢話多，我哋抽取前 3000 字精華
                        report_data += f"【來源】：{url}\n【網民討論內容】：{result.markdown[:3000]}\n\n"
                    else:
                        report_data += f"【來源】：{url}\n【狀態】：讀取失敗 ({result.error_message})\n\n"
                except Exception as inner_e:
                    print(f"爬取 {url} 失敗: {inner_e}")
                    
        return f"📡 [Last 30 Days 輿情報告原始數據]：\n\n{report_data}\n\n🚨 請根據以上網民真實討論、正反意見，為老闆總結出一份「外國科技圈民意與趨勢分析報告」！"

    except Exception as e:
        return f"❌ 輿情雷達出錯：{str(e)}"
