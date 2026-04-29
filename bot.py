import os
import json
import base64
import logging
import aiohttp
import datetime
import pandas as pd
import fitz  # PyMuPDF
from zoneinfo import ZoneInfo
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

# ================= 配置區 (動態讀取 .env) =================
load_dotenv() 

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
GEMINI_MODEL = os.getenv("MODEL_NAME", "gemini-2.5-flash")

_allowed_user_str = os.getenv("ALLOWED_USER_ID")
ALLOWED_USER_ID = int(_allowed_user_str) if _allowed_user_str else 0

BOT_NAME = os.getenv("BOT_NAME", "AI 助理")
OWNER_NAME = os.getenv("OWNER_NAME", "老闆")
OWNER_ROLE = os.getenv("OWNER_ROLE", "專業人士")
TIMEZONE_STR = os.getenv("TIMEZONE", "UTC")
LOCATION = os.getenv("LOCATION", "Global")

if not TELEGRAM_TOKEN or not API_KEY or not API_URL or ALLOWED_USER_ID == 0:
    logging.error("❌ 系統啟動失敗：缺少必要的環境變數，請確認 .env 檔案是否填寫完整！")
    exit(1)

# ================= 記憶體系統 =================
user_memory = {}
MAX_HISTORY = 10 

SYSTEM_PROMPT = f"""
你是{BOT_NAME}，{OWNER_NAME}（{LOCATION}{OWNER_ROLE}）的專屬智能代理。
請用繁體中文（適當夾雜地道廣東話）回答。

【🤖 你的核心能力認知】：
1. 具備語音能力：老闆發語音你會聽，你亦會回傳語音。
2. 具備視覺能力：可分析圖片、PDF、Excel 表格。
3. 🌐 具備「網頁截圖」與「影片解讀」能力：
   - 當老闆要求總結 YouTube 影片，請立刻調用 `analyze_youtube_video` 工具獲取字幕文本，然後總結。不要再說你無法看影片。
   - 當調用 `browse_website` 工具時，系統會自動擷取網頁的截圖傳送給你，請你結合截圖畫面與文字數據進行深入的視覺分析。

【🛑 核心工作守則：PLAN (思考計劃模式)】
任務複雜時，請先使用以下格式匯報步驟：
📋 **施工方案：**
1. 我會先做...
2. 最後得出...

【🛠️ 系統除錯模式】
貼出 Bug 時，強制 4 步回覆：1.🚨發生咩事 2.📍邊行出錯 3.🕵️點解出錯 4.🔧修正方案
"""

async def daily_morning_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = ALLOWED_USER_ID
    local_time = datetime.datetime.now(ZoneInfo(TIMEZONE_STR))
    weekdays_tc = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    date_str = local_time.strftime(f"%Y年%m月%d日 ({weekdays_tc[local_time.weekday()]})")

    report = ""
    if LOCATION == "Hong Kong":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=tc") as resp:
                    flw_data = await resp.json()
                    forecast_desc = flw_data.get("generalSituation", "") + "\n" + flw_data.get("tcInfo", "")
                
                async with session.get("https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc") as resp:
                    fnd_data = await resp.json()
                    forecast_7days = fnd_data.get("weatherForecast", [])[:7]

            report = f"🌅 早晨{OWNER_NAME}！今日係 {date_str}。\n\n"
            report += "【🌩️ 本地最新天氣預報】\n"
            report += f"{forecast_desc}\n\n"
            report += "【📅 未來七天天氣展望】\n"
            
            for day in forecast_7days:
                date = day.get('forecastDate')
                week = day.get('forecastWeek')
                temp = f"{day.get('forecastMintemp', {}).get('value')}°C - {day.get('forecastMaxtemp', {}).get('value')}°C"
                weather = day.get('forecastWeather')
                report += f"🔹 {date[4:6]}月{date[6:]}日 ({week}): {temp}, {weather}\n"
            
            report += "\n祝你今日工作順利，出入平安！👷‍♂️"
        except Exception as e:
            logging.error(f"獲取天文台數據失敗: {e}")
            report = f"🌅 早晨{OWNER_NAME}！今日係 {date_str}。天文台數據暫時連線唔到，出門記得望下天呀！"
    else:
        report = f"🌅 早晨{OWNER_NAME}！今日係 {date_str}。新的一天開始了，祝你今日在 {LOCATION} 工作順利！"

    await context.bot.send_message(chat_id=chat_id, text=report)
    
    try:
        tts = gTTS(text=report.replace("°C", "度"), lang='yue') 
        tts.save("morning_weather.mp3")
        with open("morning_weather.mp3", "rb") as voice_output:
            await context.bot.send_voice(chat_id=chat_id, voice=voice_output)
        os.remove("morning_weather.mp3")
    except Exception as e:
        logging.error(f"晨報語音生成失敗: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ 警告：未授權用戶，拒絕訪問。")
        return

    is_voice_mode = False 
    content_payload = []
    
    temp_ogg = f"temp_voice_{user_id}.ogg"
    temp_wav = f"temp_voice_{user_id}.wav"
    reply_mp3 = f"reply_{user_id}.mp3"

    # --- 處理語音 ---
    if update.message.voice:
        is_voice_mode = True
        status_msg = await update.message.reply_text("🎧 收到語音，努力聽緊...")
        try:
            voice_file = await update.message.voice.get_file()
            await voice_file.download_to_drive(temp_ogg)
            
            audio = AudioSegment.from_file(temp_ogg)
            audio.export(temp_wav, format="wav")
            
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
            if os.path.exists(temp_ogg): os.remove(temp_ogg)
            if os.path.exists(temp_wav): os.remove(temp_wav)

    # --- 處理圖片 ---
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

    # --- 處理文件 ---
    elif update.message.document:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        doc = update.message.document
        file_name = doc.file_name
        file_ext = os.path.splitext(file_name)[1].lower()
        
        status_msg = await update.message.reply_text(f"📑 收到文件，正在閱讀：{file_name}...")
        
        file = await doc.get_file()
        current_file_path = f"temp_{doc.file_id}{file_ext}"
        await file.download_to_drive(current_file_path)
        
        extracted_text = ""
        try:
            if file_ext == '.pdf':
                with fitz.open(current_file_path) as pdf:
                    for page in pdf:
                        extracted_text += page.get_text()
                extracted_content = f"--- PDF 文件內容「{file_name}」---\n\n{extracted_text}"
            
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(current_file_path)
                extracted_text = df.to_markdown(index=False)
                extracted_content = f"--- Excel 數據表「{file_name}」---\n\n{extracted_text}"
            
            else:
                await status_msg.edit_text(f"❌ 暫時未支援 {file_ext} 格式。請改用 PDF 或 Excel 呀老闆！")
                return
            
            user_question = update.message.caption or "請幫我分析這份文件。"
            content_payload = f"【老闆的問題】：{user_question}\n\n{extracted_content}"
            await status_msg.edit_text("✅ 文件讀完啦，等我諗下點答你...")

        except Exception as e:
            await status_msg.edit_text(f"❌ 解析文件失敗：{str(e)}")
            return
        finally:
            if os.path.exists(current_file_path): os.remove(current_file_path)

    else:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        content_payload = update.message.text or ""

    # --- AI 推理 ---
    local_time = datetime.datetime.now(ZoneInfo(TIMEZONE_STR))
    current_time_str = local_time.strftime(f"%Y年%m月%d日 %H:%M")
    
    # 🚨 強化 System Prompt：禁止幻覺，強迫誠實
    dynamic_system_prompt = SYSTEM_PROMPT + f"""
    \n\n【系統強制注入】：現在的準確當地時間是 {current_time_str}。
    🚨【真理指令】：如果工具調用失敗（例如 analyze_youtube_video 或 search_web 返回錯誤），請老實告訴老闆失敗原因，絕對禁止憑空編造內容。
    禁止在獲取資訊失敗時作答任何不相關的內容（例如無故提及九龍城重建）。
    """

    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": dynamic_system_prompt}]
    else:
        if user_memory[user_id][0]["role"] == "system":
            user_memory[user_id][0]["content"] = dynamic_system_prompt
    
    user_memory[user_id].append({"role": "user", "content": content_payload})

    payload = {
        "model": GEMINI_MODEL,
        "messages": user_memory[user_id],
        "tools": GET_TOOLS_LIST,
        "tool_choice": "auto"
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    await update.message.reply_text(f"❌ API 錯誤: {await response.text()}")
                    user_memory[user_id].pop()
                    return
                
                data = await response.json()
                response_message = data['choices'][0]['message']

                if response_message.get('tool_calls'):
                    user_memory[user_id].append(response_message) 
                    
                    for tool_call in response_message['tool_calls']:
                        func_name = tool_call['function']['name']
                        args = json.loads(tool_call['function']['arguments'])
                        
                        if func_name in AGENT_TOOLS_REGISTRY:
                            target_func = AGENT_TOOLS_REGISTRY[func_name]["func"]
                            result = await target_func(chat_id=chat_id, context=context, **args)
                            
                            # 🚨 視覺截圖注入邏輯 (Image Injection Protocol)
                            is_screenshot = False
                            try:
                                result_dict = json.loads(str(result))
                                if isinstance(result_dict, dict) and result_dict.get("type") == "webpage_with_screenshot":
                                    user_memory[user_id].append({
                                        "role": "tool",
                                        "tool_call_id": tool_call['id'],
                                        "name": func_name,
                                        "content": f"成功訪問【{result_dict['title']}】並已擷取截圖，截圖將在下一條訊息提供供視覺分析。"
                                    })
                                    # 偽裝成 User 訊息把截圖餵給大腦
                                    user_memory[user_id].append({
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": f"（系統提示：這是一張由系統自動擷取的網頁截圖，輔助備用文字內容為：\n{result_dict['text']}\n\n請結合截圖與文字進行深度視覺分析。）"},
                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{result_dict['image_base64']}"}}
                                        ]
                                    })
                                    is_screenshot = True
                            except Exception:
                                pass
                                
                            # 如果不是截圖，就當作普通文字 Tool 結果處理
                            if not is_screenshot:
                                tool_text = str(result)
                                # 🚨 如果獲取失敗，在大腦記憶中加重語氣防止幻覺
                                if "❌" in tool_text:
                                    tool_text += " (警告：獲取資訊失敗，絕對不可憑空編造答案！)"
                                
                                user_memory[user_id].append({
                                    "role": "tool",
                                    "tool_call_id": tool_call['id'],
                                    "name": func_name,
                                    "content": tool_text
                                })
                    
                    payload["messages"] = user_memory[user_id]
                    payload.pop("tools", None)
                    async with session.post(API_URL, headers=headers, json=payload) as res2:
                        data2 = await res2.json()
                        final_reply = data2['choices'][0]['message']['content']
                        user_memory[user_id].append({"role": "assistant", "content": final_reply})

                else:
                    final_reply = response_message.get('content', "我唔太明白。")
                    user_memory[user_id].append({"role": "assistant", "content": final_reply})

                if final_reply is None or str(final_reply).strip() == "":
                    final_reply = "✅ 指令已處理！（如果冇收到 Excel 報表，請檢查 VPS 終端機有無紅字報錯）"
                    
                await update.message.reply_text(final_reply)

                # 語音回覆
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
                        if os.path.exists(reply_mp3): os.remove(reply_mp3)

                # 清理歷史記憶，避免超出長度
                if len(user_memory[user_id]) > MAX_HISTORY * 2 + 1:
                    user_memory[user_id].pop(1)
                    user_memory[user_id].pop(1)

    except Exception as e:
        await update.message.reply_text(f"❌ 系統錯誤：{str(e)}")
        if user_memory[user_id]: user_memory[user_id].pop()

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VOICE | filters.Document.ALL, handle_message))
    
    t = datetime.time(hour=5, minute=30, tzinfo=ZoneInfo(TIMEZONE_STR))
    app.job_queue.run_daily(daily_morning_report, t)
    
    print(f"🚀 {BOT_NAME} Agent 啟動成功！已支援 YouTube & 視覺截圖解析。")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()