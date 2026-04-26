<div align="center">
  <img src="wukong_logo.png" alt="Wukong Logo" width="200" />
  <h1>ErlangShen Agent (二郎神AI助理)</h1>
</div>

這是一個專為香港建築行業 (QS & Rebar Detailer) 量身打造的 Telegram 專屬 AI 助理。基於強大的 Google Gemini 模型開發，具備視覺分析、語音對話、即時網絡搜尋、專業計算與定時排程能力。

## ✨ 核心功能 (Features)

* **🗣️ 多模態語音對話：** 支援接收 Telegram 語音訊息，並以地道廣東話語音回覆，實現無縫交流。
* **👁️ 工程圖紙視覺分析：** 支援上傳圖紙或截圖，AI 自動識別並分析複雜工程內容。
* **📰 全球即時資訊 (RSS)：** 內建無代碼新聞抓取通道，即時讀取世界各地頭條新聞，絕對防封鎖。
* **🧮 鋼筋重量精算：** 內建專屬建築工具，一鍵計算鋼筋重量 (Tool Calling 完美調用)。
* **🌤️ 本地與世界天氣：** 串接香港天文台 API 提供每日晨報，並支援隨時查詢全球任何城市的天氣狀況。
* **⏰ 定時提醒與排程：** 支援設定私人鬧鐘，系統底層注入動態時間，讓 AI 具備準確的時間觀念。

---

## 🛠️ 詳細部署指南 (Step-by-Step Deployment Guide)

本專案建議部署於 Linux 伺服器 (如 Ubuntu 24.04)。以下為從零開始的完整架設步驟。

###  系統底層環境準備
```bash
Step 1:為了讓機器人能夠處理 Telegram 的語音訊息 (接收與發送)，必須在系統底層安裝影音處理器與編碼器。請在終端機執行：
sudo apt update
sudo apt install ffmpeg flac -y

Step 2: 下載專案與建立虛擬環境
將代碼庫克隆到伺服器，並建立獨立的 Python 虛擬環境以避免套件衝突：
Bash
# 1. 複製專案到本地
git clone [https://github.com/gdtohk/ErlangShen-Agent.git](https://github.com/gdtohk/ErlangShen-Agent.git)
cd ErlangShen-Agent
# 2. 建立名為 venv 的虛擬環境
python3 -m venv venv
# 3. 啟動虛擬環境 (啟動後命令列前方會出現 (venv) 字樣)
source venv/bin/activate
# 4. 安裝所有必備的 Python 依賴套件
pip install -r requirements.txt

Step 3: 配置環境變數 (.env)
為了保護敏感資訊與方便未來切換模型，本專案全面實施「配置與代碼分離」，強制使用 .env 隱藏檔讀取配置。
請在專案根目錄下建立 .env 檔案：
Bash
nano .env
將以下內容貼入編輯器中，並替換為你自己的專屬數值：
Plaintext
TELEGRAM_TOKEN=你的_Telegram_Bot_Token
API_KEY=你的_Gemini_API_Key
API_URL=你的_API_中轉地址_或_官方地址
ALLOWED_USER_ID=你的_Telegram_使用者ID
# --- 以下為個性化設定 ---
BOT_NAME=ErlangShen                   # (可隨意填寫)
OWNER_NAME=HO                     # (可隨意填寫)
OWNER_ROLE=Rebar Detailer and QS  # (可隨意填寫)
TIMEZONE=Asia/Hong_Kong           # (英語填寫：洲/城市，必填且格式必須正確)
LOCATION=Hong Kong                # (英語填寫：城市)
MODEL_NAME=gemini-2.5-pro         # (你的模型名稱)
(提示：在 nano 編輯器中按 Ctrl+O 存檔，按 Enter 確認，再按 Ctrl+X 離開。)

Step 4: 背景常駐運行 (使用 tmux)
為了避免關閉 SSH 終端機後機器人停止運作，建議使用 tmux 建立背景常駐房間：
Bash
# 1. 建立一個名為 ErlangShen 的背景房間
tmux new -s ErlangShen
# 2. 確保虛擬環境已啟動
source venv/bin/activate
# 3. 啟動機器人
python bot.py
當看到控制台印出 🚀 ErlangShen 啟動成功！ 等字樣後，請按下鍵盤的 Ctrl + B 放開，然後按下 D 鍵。
這樣就能將機器人完美掛載於背景全天候運行！

(若未來需要重新進入房間查看日誌或更新代碼，請輸入：tmux attach -t ErlangShen)

👨‍💻 作者 (Author)
HO - QS & Rebar Detailer based in Hong Kong
