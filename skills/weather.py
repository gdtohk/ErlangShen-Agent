import aiohttp

async def get_hk_weather_detailed(**kwargs):
    """獲取香港天文台最新天氣"""
    url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=tc"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # 抓取天氣概況和警告
                    forecast = data.get('generalSituation', '') + "\n" + data.get('tcInfo', '')
                    return f"【香港天文台實時數據】\n{forecast}\n(請根據此數據，用貼心的語氣向老闆匯報天氣)"
                return "❌ 無法連接天文台 API"
    except Exception as e:
        return f"❌ 獲取天氣失敗: {str(e)}"
