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

## 🛠️ 詳細部署指南 (Step-by-Step Deployment Guide)

本專案建議部署於 Linux 伺服器 (如 Ubuntu 24.04)。以下為從零開始的完整架設步驟。

### Step 1: 系統底層環境準備
為了讓機器人能夠處理 Telegram 的語音訊息 (接收與發送)，必須在系統底層安裝影音處理器與編碼器。請在終端機執行：

```bash
sudo apt update
sudo apt install ffmpeg flac -y
Step 2: 下載專案與建立虛擬環境
將代碼庫克隆到伺服器，並建立獨立的 Python 虛擬環境以避免套件衝突：

Bash
# 1. 複製專案到本地
git clone [https://github.com/gdtohk/Wukong-Agent.git](https://github.com/gdtohk/Wukong-Agent.git)
cd Wukong-Agent

# 2. 建立名為 venv 的虛擬環境
python3 -m venv venv

# 3. 啟動虛擬環境 (啟動後命令列前方會出現 (venv) 字樣)
source venv/bin/activate

# 4. 安裝所有必備的 Python 依賴套件
pip install -r requirements.txt
Step 3: 配置環境變數 (.env)
為了保護敏感資訊（如 API 金鑰），本專案強制使用 .env 隱藏檔讀取配置。
請在專案目錄下建立 .env 檔案：

Bash
nano .env
將以下內容貼入編輯器中，並替換為你自己的數值：

代码段
TELEGRAM_TOKEN=你的_Telegram_Bot_Token
API_KEY=你的_Gemini_API_Key
API_URL=你的_API_中轉地址_或_官方地址
ALLOWED_USER_ID=你的_Telegram_使用者ID
(提示：在 nano 中按 Ctrl+O 存檔，按 Enter 確認，再按 Ctrl+X 離開。)

Step 4: 背景常駐運行 (使用 tmux)
為了避免關閉 SSH 終端機後機器人停止運作，建議使用 tmux 建立背景常駐房間：

Bash
# 1. 建立一個名為 wukong 的背景房間
tmux new -s wukong

# 2. 確保虛擬環境已啟動
source venv/bin/activate

# 3. 啟動機器人
python bot.py
當看到控制台印出 🚀 悟空 Agent 啟動成功！支援語音對話！ 後，請按下鍵盤的 Ctrl + B 放開，然後按下 D 鍵。這樣就能將機器人完美掛載於背景全天候運行！

(若未來需要重新進入房間查看日誌或更新代碼，請輸入：tmux attach -t wukong)

👨‍💻 作者 (Author)
HO - QS & Rebar Detailer based in Hong Kong
