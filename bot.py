import random
import os, json, base64, logging, aiohttp, datetime, pandas as pd, fitz
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
from registry import GET_TOOLS_LIST, AGENT_TOOLS_REGISTRY

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
load_dotenv() 

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEYS = [os.getenv("API_KEY_1"), os.getenv("API_KEY_2")]
API_KEYS = [k for k in API_KEYS if k]  # 過濾掉空白嘅 Key
API_URL = os.getenv("API_URL")
GEMINI_MODEL = os.getenv("MODEL_NAME", "gemini-2.5-flash")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", 0))
BOT_NAME = os.getenv("BOT_NAME", "二郎神")
OWNER_NAME = os.getenv("OWNER_NAME", "老闆")
TIMEZONE_STR = os.getenv("TIMEZONE", "Asia/Hong_Kong")

user_memory = {}
MAX_HISTORY = 10 

SYSTEM_PROMPT = f"""
你是{BOT_NAME}，{OWNER_NAME}的專屬 AI 助理。請用地道廣東話回答。
你具備語音對話、視覺圖片分析、文件解析 (PDF/Excel)、網頁瀏覽與截圖功能。

【🚨 真理指令】：
1. 絕對服從時間：系統在每次對話都會注入「現在時間」，你必須 100% 相信這就是真實的當前時間，並以此為基準回答所有問題，忘記你訓練資料庫中的時間。
2. 資訊直出原則：當調用 search_web 獲取新聞時，無論結果顯示什麼年份，請直接當作「最新資訊」向老闆匯報。絕對禁止補充「年份有衝突」、「未有今日新聞」或「來源是 2026 年」等無謂的解釋！
3. 如果工具調用失敗，請老實告訴老闆，絕對禁止憑空編造！
4. 調用 browse_website 後，系統會為你注入網頁截圖，請務必進行視覺分析。
5. ⚠️ 重要：你目前並不具備觀看 YouTube 影片的能力。如果老闆給你 YouTube 連結，請婉轉告知無法觀看。
"""

async def daily_morning_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = ALLOWED_USER_ID
    local_time = datetime.datetime.now(ZoneInfo(TIMEZONE_STR))
    date_str = local_time.strftime("%Y年%m月%d日")
    await context.bot.send_message(chat_id=chat_id, text=f"🌅 早晨{OWNER_NAME}！今日係 {date_str}。祝你今日工作順利！")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if user_id != ALLOWED_USER_ID: return

    is_voice = False
    content_payload = ""
    temp_ogg, temp_wav, reply_mp3 = f"temp_{user_id}.ogg", f"temp_{user_id}.wav", f"reply_{user_id}.mp3"
    original_memory_len = len(user_memory.get(user_id, []))

    if update.message.voice:
        is_voice = True
        status_msg = await update.message.reply_text("🎧 努力聽緊...")
        try:
            voice_file = await update.message.voice.get_file()
            await voice_file.download_to_drive(temp_ogg)
            AudioSegment.from_file(temp_ogg).export(temp_wav, format="wav")
            with sr.AudioFile(temp_wav) as source:
                content_payload = sr.Recognizer().recognize_google(sr.Recognizer().record(source), language="yue-Hant-HK")
            await status_msg.edit_text(f"🗣️ 你講咗：\n「{content_payload}」")
        except: return await status_msg.edit_text("❌ 聽唔清楚。")
        finally:
            if os.path.exists(temp_ogg): os.remove(temp_ogg)
            if os.path.exists(temp_wav): os.remove(temp_wav)
    elif update.message.photo:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        try:
            byte_array = await (await update.message.photo[-1].get_file()).download_as_bytearray()
            content_payload = [
                {"type": "text", "text": update.message.text or update.message.caption or "分析這張圖片。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(byte_array).decode('utf-8')}"}}
            ]
        except: return await update.message.reply_text("❌ 圖片處理失敗")
    elif update.message.document:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        doc = update.message.document
        file_ext = os.path.splitext(doc.file_name)[1].lower()
        status_msg = await update.message.reply_text(f"📑 閱讀：{doc.file_name}...")
        current_file_path = f"temp_{doc.file_id}{file_ext}"
        await (await doc.get_file()).download_to_drive(current_file_path)
        try:
            if file_ext == '.pdf': extracted_content = "".join([page.get_text() for page in fitz.open(current_file_path)])
            elif file_ext in ['.xlsx', '.xls']: extracted_content = pd.read_excel(current_file_path).to_markdown(index=False)
            else: return await status_msg.edit_text("❌ 未支援格式")
            content_payload = f"【文件內容】：\n{extracted_content}\n\n【問題】：{update.message.caption or '請分析文件'}"
            await status_msg.edit_text("✅ 讀完。")
        except: return await status_msg.edit_text("❌ 解析失敗")
        finally:
            if os.path.exists(current_file_path): os.remove(current_file_path)
    else:
        content_payload = update.message.text or ""

    local_time = datetime.datetime.now(ZoneInfo(TIMEZONE_STR))
    dynamic_prompt = SYSTEM_PROMPT + f"\n\n現在時間：{local_time.strftime('%Y-%m-%d %H:%M')}。"
    if user_id not in user_memory: user_memory[user_id] = [{"role": "system", "content": dynamic_prompt}]
    else: user_memory[user_id][0]["content"] = dynamic_prompt
    
    user_memory[user_id].append({"role": "user", "content": content_payload})
    
    # 🚨 補回遺失的 payload 定義 🚨
    payload = {"model": GEMINI_MODEL, "messages": user_memory[user_id], "tools": GET_TOOLS_LIST, "tool_choice": "auto"}
    
    current_key = random.choice(API_KEYS)
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": current_key,            # 這是 Google 官方專用認證
        "Authorization": f"Bearer {current_key}"  # 這是兼容舊版 Proxy 認證 (可同時保留)
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as response:
                if response.status != 200: raise Exception(f"API錯誤 ({response.status})")
                data = await response.json()
                if 'choices' not in data: raise Exception("代理返回異常")
                msg = data['choices'][0]['message']

                if msg.get('tool_calls'):
                    user_memory[user_id].append(msg)
                    for tc in msg['tool_calls']:
                        fn = tc['function']['name']
                        args = json.loads(tc['function']['arguments'])
                        res = await AGENT_TOOLS_REGISTRY[fn]["func"](chat_id=chat_id, context=context, **args)
                        
                        is_ss = False
                        try:
                            rj = json.loads(str(res))
                            if rj.get("type") == "webpage_with_screenshot":
                                user_memory[user_id].append({"role": "tool", "tool_call_id": tc['id'], "name": fn, "content": f"文字：{rj['text']}"})
                                user_memory[user_id].append({"role": "user", "content": [{"type": "text", "text": "請參考網頁截圖。"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{rj['image_base64']}"}}]})
                                is_ss = True
                        except: pass

                        if not is_ss:
                            tool_out = str(res)
                            user_memory[user_id].append({"role": "tool", "tool_call_id": tc['id'], "name": fn, "content": tool_out})
                    
                    payload["messages"] = user_memory[user_id]
                    payload.pop("tools", None)
                    async with session.post(API_URL, headers=headers, json=payload) as res2:
                        final_reply = (await res2.json())['choices'][0]['message']['content']
                else:
                    final_reply = msg.get('content', "唔明。")

                user_memory[user_id].append({"role": "assistant", "content": final_reply})
                
                if final_reply is None or str(final_reply).strip() == "":
                    final_reply = "✅ 指令已處理！"
                    
                await update.message.reply_text(final_reply)

                if is_voice:
                    try:
                        gTTS(text=final_reply, lang='yue').save(reply_mp3)
                        with open(reply_mp3, "rb") as vo: await update.message.reply_voice(voice=vo)
                        os.remove(reply_mp3)
                    except: pass
                
                if len(user_memory[user_id]) > MAX_HISTORY * 2 + 1:
                    user_memory[user_id].pop(1)
                    user_memory[user_id].pop(1)

    except Exception as e:
        user_memory[user_id] = user_memory.get(user_id, [])[:original_memory_len]
        await update.message.reply_text(f"❌ 系統錯誤：{str(e)}")

def main():
    print("⏳ 正在啟動二郎神大腦...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VOICE | filters.Document.ALL, handle_message))
    
    t = datetime.time(hour=5, minute=30, tzinfo=ZoneInfo(TIMEZONE_STR))
    app.job_queue.run_daily(daily_morning_report, t)
    
    print(f"🚀 {BOT_NAME} 啟動成功！我已經喺 Telegram 等緊老闆你啦！")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
