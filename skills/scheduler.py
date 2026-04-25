import datetime
import os
import aiohttp
from zoneinfo import ZoneInfo

async def schedule_daily_weather(hour: int, minute: int, chat_id: int, context, **kwargs):
    """設定每天定時發送天氣報告"""
    try:
        # 定義每天時間一到，要偷偷在背景執行的動作
        async def daily_weather_job(ctx):
            from skills.weather import get_hk_weather_detailed
            # 1. 獲取最新天氣
            weather_data = await get_hk_weather_detailed()
            
            # 2. 讓大腦自己生成每天不同的早晨問候 (自我對話機制)
            API_KEY = os.getenv("API_KEY")
            API_URL = os.getenv("API_URL")
            payload = {
                "model": "gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": "你是悟空(Wukong)，何生的專屬智能助理。請根據以下天氣數據，寫一段大約150字的廣東話早晨問候，提醒他今日和未來幾天的天氣變化、帶傘或穿衣。語氣要精神、貼心、專業。"},
                    {"role": "user", "content": weather_data}
                ]
            }
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            reply = data['choices'][0]['message']['content']
                        else:
                            reply = f"🌅 老闆您好！今日天氣匯報：\n\n{weather_data}"
            except:
                reply = f"🌅 老闆您好！今日天氣匯報：\n\n{weather_data}"
            
            # 3. 發送給老闆
            await ctx.bot.send_message(chat_id=chat_id, text=reply)

        # 設定香港時間的執行點
        hk_tz = ZoneInfo("Asia/Hong_Kong")
        target_time = datetime.time(hour=hour, minute=minute, tzinfo=hk_tz)
        
        # 加入系統 JobQueue (每天自動循環執行)
        context.job_queue.run_daily(
            daily_weather_job,
            time=target_time,
            chat_id=chat_id,
            name=f"daily_weather_{chat_id}_{hour}_{minute}"
        )
        
        return f"✅ 已經成功幫老闆設定每天早上 {hour:02d}:{minute:02d} 自動匯報當天與未來7天天氣！"
    except Exception as e:
        return f"❌ 設定定時任務失敗：{str(e)}"
