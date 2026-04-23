import os
import json
import base64
import logging
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 👉 匯入你的技能註冊表
from registry import GET_TOOLS_LIST, AGENT_TOOLS_REGISTRY

# --- 顯示日誌 ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= 配置區 =================
# 啟動時自動去讀取 .env 隱藏檔
load_dotenv() 

# 徹底移除所有 Hardcode 的預設值，全部強制從 .env 讀取
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")

# 安全處理 ALLOWED_USER_ID，如果沒讀到就設為 0 (拒絕所有人)
_allowed_user_str = os.getenv("ALLOWED_USER_ID")
ALLOWED_USER_ID = int(_allowed_user_str) if _allowed_user_str else 0

# 嚴格防護：缺少任何一個變數，程式直接終止，絕不帶病運行
if not TELEGRAM_TOKEN or not API_KEY or not API_URL or ALLOWED_USER_ID == 0:
    logging.error("❌ 系統啟動失敗：缺少必要的環境變數，請確認 .env 檔案是否填寫完整！")
    exit(1)

# ================= 記憶體系統 =================
user_memory = {}
MAX_HISTORY = 10 

SYSTEM_PROMPT = """
你是悟空 (Wukong)，何生（香港建築行業 QS 兼紮鐵拆圖工程師）的專屬智能代理。
請用繁體中文（適當夾雜地道廣東話）回答。
你具備視覺能力（可看工程圖紙）和工具調用能力（可計算數據）。
如果需要運算，請務必調用對應工具。
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # 🛡️ 安全攔截
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ 警告：未授權用戶，拒絕訪問。")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    # 1. 解析 Telegram 輸入 (視覺 + 文字)
    user_text = update.message.text or update.message.caption or "請幫我分析這張圖片。"
    content_payload = []

    if update.message.photo:
        try:
            photo_file = await update.message.photo[-1].get_file()
            byte_array = await photo_file.download_as_bytearray()
            base64_encoded = base64.b64encode(byte_array).decode('utf-8')
            content_payload = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_encoded}"}}
            ]
        except Exception as e:
            await update.message.reply_text(f"❌ 圖片處理失敗：{str(e)}")
            return
    else:
        content_payload = user_text

    # 2. 記憶體管理
    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    user_memory[user_id].append({"role": "user", "content": content_payload})

    # 3. 發送給大腦 (帶上工具箱)
    payload = {
        "model": "gemini-2.5-flash",
        "messages": user_memory[user_id],
        "tools": GET_TOOLS_LIST,
        "tool_choice": "auto"
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

    try:
        async with aiohttp.ClientSession() as session:
            # 第一回合：問大腦要不要用工具
            async with session.post(API_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    await update.message.reply_text(f"❌ API 錯誤: {await response.text()}")
                    user_memory[user_id].pop()
                    return
                
                data = await response.json()
                response_message = data['choices'][0]['message']

                # 如果大腦決定調用工具 (例如算鋼筋)
                if response_message.get('tool_calls'):
                    user_memory[user_id].append(response_message) # 記錄大腦的動作
                    
                    for tool_call in response_message['tool_calls']:
                        func_name = tool_call['function']['name']
                        args = json.loads(tool_call['function']['arguments'])
                        
                        # 動態執行工具
                        if func_name in AGENT_TOOLS_REGISTRY:
                            target_func = AGENT_TOOLS_REGISTRY[func_name]["func"]
                            result = await target_func(**args)
                            
                            user_memory[user_id].append({
                                "role": "tool",
                                "tool_call_id": tool_call['id'],
                                "name": func_name,
                                "content": str(result)
                            })
                    
                    # 第二回合：把計算結果給大腦，讓它組織語言
                    payload["messages"] = user_memory[user_id]
                    payload.pop("tools", None)
                    async with session.post(API_URL, headers=headers, json=payload) as res2:
                        data2 = await res2.json()
                        final_reply = data2['choices'][0]['message']['content']
                        user_memory[user_id].append({"role": "assistant", "content": final_reply})
                        await update.message.reply_text(final_reply)

                else:
                    # 如果不需要用工具 (普通聊天或看圖片)
                    reply = response_message.get('content')
                    if reply:
                        user_memory[user_id].append({"role": "assistant", "content": reply})
                        await update.message.reply_text(reply)

                # 清理過舊記憶，避免 Token 爆滿
                if len(user_memory[user_id]) > MAX_HISTORY * 2 + 1:
                    user_memory[user_id].pop(1)
                    user_memory[user_id].pop(1)

    except Exception as e:
        await update.message.reply_text(f"❌ 系統錯誤：{str(e)}")
        if user_memory[user_id]: user_memory[user_id].pop()

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    print("🚀 悟空 Agent 啟動成功！正在監聽 Telegram...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
