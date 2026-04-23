import asyncio

async def set_reminder(minutes: float, message: str, chat_id: int, context, **kwargs):
    """設定鬧鐘提醒"""
    try:
        seconds = int(minutes * 60)
        
        # 建立一個背景任務來倒數計時並發送訊息
        async def alarm_task():
            await asyncio.sleep(seconds) # 默默等待
            # 時間到！主動發訊息給老闆
            await context.bot.send_message(chat_id=chat_id, text=f"⏰ 【老闆，時間到！】\n提提你：{message}")
        
        # 將任務丟到背景執行，不卡住現在的聊天
        asyncio.create_task(alarm_task())
        
        return f"鬧鐘設定成功：系統將在 {minutes} 分鐘後自動發送提醒「{message}」給老闆。"
    except Exception as e:
        return f"❌ 設定提醒失敗：{str(e)}"
