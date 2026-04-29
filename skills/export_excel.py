import os
import pandas as pd

async def generate_rebar_excel(chat_id, context, report_name, records, **kwargs):
    """將鋼筋數據生成 Excel 報表並發送給用戶"""
    print(f"📊 [Debug] 準備生成 Excel 報表: {report_name}")
    try:
        # 將大腦傳入的數據清單轉換為 DataFrame
        df = pd.DataFrame(records)
        
        # 重新命名欄位，令報表符合 QS 專業格式
        rename_map = {
            "d": "鋼筋直徑 (mm)",
            "length": "長度 (m)",
            "qty": "數量 (支)",
            "weight": "總重量 (kg)"
        }
        df.rename(columns=rename_map, inplace=True)

        # 設定檔案名稱
        file_name = f"{report_name}.xlsx"
        
        # 生成 Excel 檔案 (index=False 代表唔要最左邊嗰行數字排序)
        df.to_excel(file_name, index=False)
        
        # 透過 Telegram 發送檔案俾老闆
        with open(file_name, "rb") as file:
            await context.bot.send_document(
                chat_id=chat_id, 
                document=file, 
                caption=f"老闆，你要嘅【{report_name}】已經整理好啦！📊"
            )
        
        # 傳送完畢後，刪除 VPS 上嘅暫存檔，保持硬碟乾淨
        if os.path.exists(file_name):
            os.remove(file_name)
            
        return f"✅ 成功生成並發送 Excel 報表：{file_name}"
        
    except Exception as e:
        error_msg = f"❌ 生成 Excel 失敗：{str(e)}"
        print(f"❌ [Debug] {error_msg}")
        return error_msg