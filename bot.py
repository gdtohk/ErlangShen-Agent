import os
import json
import base64
import logging
import aiohttp
import datetime  # 👈 時間模組，讓悟空擁有「手錶」
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 🎧 新增語音模組
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS

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
你具備視覺能力（可看工程圖紙）和工具調用能力（可計算數據、查天氣、設定排程）。
如果需要運算或設定定時任務，請務必調用對應工具。
(注意：如果老闆用語音發問，請盡量簡短扼要回答，方便語音播報)
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # 🛡️ 安全攔截
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ 警告：未授權用戶，拒絕訪問。")
        return

    is_voice_mode = False  # 標記老闆這次是不是用語音說話
    content_payload = []
    
    # 定義專屬的暫存檔名，避免衝突
    temp_ogg = f"temp_voice_{user_id}.ogg"
    temp_wav = f"temp_voice_{user_id}.wav"
    reply_mp3 = f"reply_{user_id}.mp3"

    # 🎧 1. 解析 Telegram 輸入：如果收到的是「語音」
    if update.message.voice:
        is_voice_mode = True
        status_msg = await update.message.reply_text("🎧 收到語音，努力聽緊...")
        try:
            # 下載語音檔 (Telegram 預設是 .ogg)
            voice_file = await update.message.voice.get_file()
            await voice_file.download_to_drive(temp_ogg)
            
            # 轉換成 .wav 格式 (SpeechRecognition 需要 wav)
            audio = AudioSegment.from_file(temp_ogg)
            audio.export(temp_wav, format="wav")
            
            # 進行語音辨識 (指定為香港廣東話)
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_wav) as source:
                audio_data = recognizer.record(source)
                user_text = recognizer.recognize_google(audio_data, language="yue-Hant-HK")
            
            await status_msg.edit_text(f"🗣️ 你講咗：\n「{user_text}」")
            content_payload = user_text
            
        except sr.UnknownValueError:
            await status_msg.edit_text("❌ 聽唔清楚，老闆可以講大聲少少或者打字嗎？")
            return
        except Exception as e:
            await status_msg.edit_text(f"❌ 語音處理出錯：{str(e)}")
            return
        finally:
            # 🗑️ 清理語音暫存檔，釋放硬碟空間
            if os.path.exists(temp_ogg): os.remove(temp_ogg)
            if os.path.exists(temp_wav): os.remove(temp_wav)

    # 👁️ 2. 解析 Telegram 輸入：如果收到的是「圖片」
    elif update.message.photo:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        user_text = update.message.text or update.message.caption or "請幫我分析這張圖片。"
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

    # ✍️ 3. 解析 Telegram 輸入：如果收到的是純「文字」
    else:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        content_payload = update.message.text or ""

    # 👉 記憶體管理（動態時間注入）
    hk_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    current_time_str = hk_time.strftime("%Y年%m月%d日 %H:%M")
    dynamic_system_prompt = SYSTEM_PROMPT + f"\n\n【系統強制注入】：現在的準確香港時間是 {current_time_str}。"

    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": dynamic_system_prompt}]
    else:
        if user_memory[user_id][0]["role"] == "system":
            user_memory[user_id][0]["content"] = dynamic_system_prompt
    
    user_memory[user_id].append({"role": "user", "content": content_payload})

    # 發送給大腦 (帶上工具箱)
    payload = {
        "model": "gemini-3.1-flash-lite-preview", 
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

                # 如果大腦決定調用工具
                if response_message.get('tool_calls'):
                    user_memory[user_id].append(response_message) 
                    
                    for tool_call in response_message['tool_calls']:
                        func_name = tool_call['function']['name']
                        args = json.loads(tool_call['function']['arguments'])
                        
                        if func_name in AGENT_TOOLS_REGISTRY:
                            target_func = AGENT_TOOLS_REGISTRY[func_name]["func"]
                            result = await target_func(chat_id=chat_id, context=context, **args)
                            
                            user_memory[user_id].append({
                                "role": "tool",
                                "tool_call_id": tool_call['id'],
                                "name": func_name,
                                "content": str(result)
                            })
                    
                    # 第二回合：把計算或設定結果給大腦，讓它組織語言回覆你
                    payload["messages"] = user_memory[user_id]
                    payload.pop("tools", None)
                    async with session.post(API_URL, headers=headers, json=payload) as res2:
                        data2 = await res2.json()
                        final_reply = data2['choices'][0]['message']['content']
                        user_memory[user_id].append({"role": "assistant", "content": final_reply})

                else:
                    # 如果不需要用工具 (普通聊天或看圖片)
                    final_reply = response_message.get('content', "我唔太明白。")
                    user_memory[user_id].append({"role": "assistant", "content": final_reply})

                # 👄 判斷回覆方式：文字 or 語音
                await update.message.reply_text(final_reply)

                # 如果老闆是用語音問的，悟空就用語音回答！
                if is_voice_mode:
                    await context.bot.send_chat_action(chat_id=chat_id, action='record_voice')
                    try:
                        tts = gTTS(text=final_reply, lang='yue') 
                        tts.save(reply_mp3)
                        with open(reply_mp3, "rb") as voice_output:
                            await update.message.reply_voice(voice=voice_output)
                    except Exception as e:
                        logging.error(f"語音生成失敗: {e}")
                        await update.message.reply_text("❌ 語音生成出錯，請睇文字回覆啦老闆！")
                    finally:
                        # 🗑️ 發送完畢後，立即清理語音回覆檔
                        if os.path.exists(reply_mp3): os.remove(reply_mp3)

                # 清理過舊記憶，避免 Token 爆滿
                if len(user_memory[user_id]) > MAX_HISTORY * 2 + 1:
                    user_memory[user_id].pop(1)
                    user_memory[user_id].pop(1)

    except Exception as e:
        await update.message.reply_text(f"❌ 系統錯誤：{str(e)}")
        if user_memory[user_id]: user_memory[user_id].pop()

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    # ✅ 加入了 filters.VOICE，這樣它才不會無視你的語音訊息
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VOICE, handle_message))
    print("🚀 悟空 Agent 啟動成功！支援語音對話！")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
