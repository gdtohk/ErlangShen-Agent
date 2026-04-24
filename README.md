# 🐵 Wukong Agent (悟空智能助理)

這是一個專為香港建築行業 (QS / 紮鐵拆圖工程師) 量身打造的 Telegram 專屬 AI 助理。
基於 Google Gemini 模型開發，具備視覺分析、語音對話、專業計算與定時排程能力。

## ✨ 核心功能 (Features)
* **🗣️ 多模態語音對話**：支援接收 Telegram 語音訊息，並以地道廣東話語音回覆。
* **👁️ 工程圖紙視覺分析**：上傳圖紙或截圖，AI 自動識別並分析內容。
* **🧮 鋼筋重量精算**：內建自定義工具，一鍵計算鋼筋重量 (Tool Calling)。
* **🌤️ 天氣與定時排程**：串接香港天文台 API，支援設定鬧鐘與每日自動天氣簡報。
* **🧠 動態時間感知**：系統底層注入動態時間，讓 AI 具備準確的時間觀念。

---

## 🛠️ 部署指南 (Deployment Guide)

### 1. 系統環境準備 (System Requirements)
在開始之前，請確保你的 Linux 伺服器 (如 Ubuntu) 已安裝底層的影音處理工具。這對於處理 Telegram 的語音訊息是必須的：

sudo apt update
sudo apt install ffmpeg flac -y


### 2. 下載專案與安裝依賴 (Installation)

# 複製專案
git clone https://github.com/gdtohk/Wukong-Agent.git
cd Wukong-Agent

# 建議使用虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝 Python 依賴套件
pip install -r requirements.txt


### 3. 環境變數配置 (Configuration)
請在專案根目錄創建一個 `.env` 檔案，並填入以下資訊：

TELEGRAM_TOKEN=你的_Telegram_Bot_Token
API_KEY=你的_Gemini_API_Key
API_URL=你的_API_中轉地址_或_官方地址
ALLOWED_USER_ID=你的_Telegram_使用者ID (用於安全攔截)


### 4. 啟動機器人 (Run)
建議使用 `tmux` 或 `nohup` 將其掛載於背景全天候運行：

python bot.py


## 👨‍💻 作者 (Author)
* **HO** - *QS & Rebar Detailer based in Hong Kong*
