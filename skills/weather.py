import aiohttp

async def get_hk_weather_detailed(**kwargs):
    """獲取香港天文台最新天氣及未來預報"""
    flw_url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=tc"
    fnd_url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. 抓今日概況
            async with session.get(flw_url) as res1:
                data1 = await res1.json()
                today_desc = data1.get('generalSituation', '') + "\n" + data1.get('tcInfo', '')
            
            # 2. 抓未來預報 (取前 7 天)
            async with session.get(fnd_url) as res2:
                data2 = await res2.json()
                forecasts = data2.get('weatherForecast', [])[:7]
                
                future_desc = "\n\n【未來7天預報】：\n"
                for day in forecasts:
                    date = day.get('forecastDate')
                    temp = f"{day.get('forecastMintemp',{}).get('value')}°C - {day.get('forecastMaxtemp',{}).get('value')}°C"
                    weather = day.get('forecastWeather')
                    # 格式化日期顯示
                    date_str = f"{date[4:6]}月{date[6:]}日"
                    future_desc += f"- {date_str}: {temp}, {weather}\n"
                    
            return f"【香港天氣實況與預報】\n{today_desc}{future_desc}"
    except Exception as e:
        return f"❌ 獲取天氣失敗: {str(e)}"
