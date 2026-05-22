import os
import asyncio

async def update_from_github(chat_id, context, **kwargs):
    """
    執行全自動脫殼升級：觸發外部 update.sh 腳本，
    並留下遺言，讓主程式有時間將回覆發送至 Telegram。
    """
    print("🔄 [System] 收到升級指令，正在啟動浴火重生程序...")
    
    try:
        # 使用 nohup 喺背景觸發 update.sh，令腳本脫離當前 Python 進程獨立運行
        # 咁樣就算 Python 被 kill，腳本都會繼續執行落去
        os.system("nohup bash update.sh > update_script.log 2>&1 &")
        
        # 呢句就係二郎神嘅「遺言」，會即刻 Send 返畀你
        return "✅ 老闆收到！我依家即刻進行「浴火重生」升級程序！我會喺後台自己殺死自己、拉取代碼然後重啟。預計 10 秒後帶住新代碼回歸，到時見！😎"
        
    except Exception as e:
        return f"❌ 啟動自動升級程序失敗：{str(e)}。請老闆手動登入 VPS 檢查。"
