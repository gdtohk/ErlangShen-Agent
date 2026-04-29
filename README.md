<div align="center">
  <img src="ErlangShen_logo.png" alt="ErlangShen Logo" width="200" />
  <h1>ErlangShen Agent (二郎神AI助理)</h1>
</div>

這是一個專為香港建築行業 (QS & Rebar Detailer) 量身打造的 Telegram 專屬 AI 助理。基於強大的 Google Gemini 模型開發，具備視覺分析、語音對話、即時網絡搜尋、專業計算與定時排程能力。

## ✨ 核心功能 (Features)
🗣️ 多模態語音對話： 支援接收 Telegram 語音訊息，並以地道廣東話語音回覆，實現無縫交流。

👁️ 工程圖紙視覺分析： 支援上傳圖紙或截圖，AI 自動識別並分析複雜工程內容。

🌐 網頁截圖與瀏覽 (New!)： 支援訪問網頁並自動擷取即時截圖 (Screenshot)，讓 AI 能結合視覺畫面分析網頁資訊（如天文台天氣圖標、即時報價單）。

📺 YouTube 影片總結 (New!)： 只需提供網址，即可自動提取影片字幕 (Transcript)，支援多國語言與自動生成字幕，秒速總結影片精華。

📑 工程文件解析 (PDF/Excel)： 支援直接讀取 PDF 規格書及 Excel 數據表 (如 BBS 鋼筋表)，秒速歸納重點。

📰 全球即時資訊 (RSS)： 內建新聞抓取通道，即時讀取全球頭條，絕對防封鎖。

🧮 鋼筋重量精算： 內建專業計算工具，一鍵核對鋼筋重量 (d²/162.2)。

⏰ 定時提醒與排程： 支援設定私人鬧鐘與每日天氣晨報，具備精確的時間觀念。

🛠️ 詳細部署指南 (Step-by-Step Deployment Guide)
1. 系統底層環境準備
為了處理語音與瀏覽網頁，必須安裝影音處理器及瀏覽器內核：
Bash
# 安裝影音編碼器
sudo apt update && sudo apt install ffmpeg flac -y

2. 安裝瀏覽器引擎 (重要!)
本專案使用 Playwright 進行網頁擷取，必須安裝 Chromium 內核：
Bash
# 安裝 Python 依賴後執行
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

3. 下載專案與環境建立
Bash
git clone https://github.com/gdtohk/ErlangShen-Agent.git
cd ErlangShen-Agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

4. 配置環境變數 (.env)
在根目錄建立 .env 檔案並填寫配置：
Plaintext
TELEGRAM_TOKEN=你的_Token
API_KEY=你的_Gemini_API_Key
API_URL=你的_API_地址
ALLOWED_USER_ID=你的_ID
TIMEZONE=Asia/Hong_Kong
LOCATION=Hong Kong
MODEL_NAME=gemini-2.5-flash

5. 背景常駐運行 (標準指令)
建議使用 nohup 或 tmux 維持 24 小時運作。當更新代碼後，請執行以下組合指令：

Bash
git pull origin main && pkill -f bot.py && nohup python3 bot.py > agent.log 2>&1 &
👨‍💻 作者 (Author)
HO - QS & Rebar Detailer based in Hong Kong
