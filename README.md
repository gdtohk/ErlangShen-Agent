<div align="center">
  <img src="ErlangShen_logo.png" alt="ErlangShen Logo" width="200" />
  <h1>ErlangShen Agent (二郎神 AI 助理)</h1>
  <p><i>專為香港建築行業 (QS & Rebar Detailer) 量身打造的 Telegram + Web 雙核驅動 AI 超級助理</i></p>
</div>

---

基於強大的 Google Gemini & Claude 模型生態開發。具備視覺分析、語音對話、即時網絡搜尋、專業計算、自動收發電郵，並搭載專屬 Web 控制中心與防殭屍熱更新系統。

## ✨ 核心進化功能 (Key Features)

*   **🗣️ 多模態語音對話**：支援接收 Telegram 原聲語音訊息，並以地道廣東話 (Edge TTS) 語音回覆，實現無縫交流。
*   **📐 專業工程圖紙視覺分析 (Upgraded)**：系統會將上傳的 PDF 圖紙 (如 BBS 報表、樁帽圖則) 轉換為高清視覺矩陣，以 QS 及鋼筋拆圖員的專業視角提取尺寸、鋼筋資訊及表格數據。
*   **📧 自動化背景收信 (New!)**：定時透過 IMAP 讀取 Gmail，自動下載附件至 `my_drive`，並針對工程相關電郵生成詳細的「QS 深度解讀報告」。
*   **🎛️ Web 專屬控制中心 (New!)**：獨立運行於 Port 5000 的網頁後台，支援「零秒熱更新」。管理員可隨時在網頁端一鍵切換底層大腦模型 (Gemini / Claude 系列)，無需重啟 Telegram 服務。
*   **🧠 超級大腦知識庫 (RAG)**：整合 ChromaDB 向量資料庫，可精準檢索本地工程規範 (如 Eurocode 2)，杜絕 AI 幻覺。
*   **🌐 網頁截圖與瀏覽**：支援訪問網址並自動擷取即時截圖，結合視覺畫面分析網頁資訊。搭配住宅 IP 代理 (如 VPNGate) 可完美繞過反爬蟲風控。
*   **📺 YouTube 影片總結**：提供網址即可自動提取影片字幕 (Transcript)，秒速總結影片精華。
*   **📰 全球即時資訊 (RSS)**：內建新聞抓取通道，即時讀取全球頭條，絕對防封鎖。

---

## 🛠️ 詳細部署指南 (Step-by-Step Deployment Guide)

### 1. 系統底層環境準備

為了處理語音與瀏覽網頁，必須安裝影音處理器及瀏覽器內核。建議於 Ubuntu / Debian 環境下執行：

```bash
# 安裝影音編碼器與進程管理工具 (fuser)
sudo apt update && sudo apt install ffmpeg flac psmisc -y

安裝瀏覽器引擎 (重要!)
本專案使用 Playwright 進行網頁擷取，必須安裝 Chromium 內核：

Bash
python3 -m playwright install chromium
python3 -m playwright install-deps chromium
2. 下載專案與環境建立
Bash
git clone [https://github.com/gdtohk/ErlangShen-Agent.git](https://github.com/gdtohk/ErlangShen-Agent.git)
cd ErlangShen-Agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. 配置環境變數 (.env)
在根目錄建立 .env 檔案並填寫配置。系統支援動態負載均衡，可設定多組 API Key：

Ini, TOML
# --- Telegram 與基礎設定 ---
TELEGRAM_TOKEN=你的_Telegram_Bot_Token
ALLOWED_USER_ID=你的_Telegram_ID
BOT_NAME=二郎神
OWNER_NAME=老闆
TIMEZONE=Asia/Hong_Kong

# --- Web 控制台設定 ---
FLASK_SECRET_KEY=自訂一串複雜密鑰
WEB_ADMIN_PASSWORD=網頁後台登入密碼

# --- AI 引擎設定 (支援多節點自動切換) ---
MODEL_NAME=gemini-2.5-flash
API_URL_1=你的_API_網址_1
API_KEY_1=你的_API_KEY_1
API_URL_2=你的_API_網址_2
API_KEY_2=你的_API_KEY_2

# --- 自動收信設定 (可選) ---
EMAIL_ACCOUNT=你的_Gmail_信箱
EMAIL_APP_PASSWORD=你的_Gmail_應用程式密碼
4. 系統啟動與自動化熱更新 (自動防殭屍機制)
⚠️ 警告：請勿再使用 killall -9 python3 進行手動重啟！這會導致 5000 端口被鎖死。

本專案內建了完美的自動更新腳本 update.sh，該腳本包含了代碼拉取、強制端口清場 (fuser) 以及安全的雙核喚醒機制。

首次啟動或手動重啟，只需執行：

Bash
bash update.sh
日常更新 (Telegram 遙距操控)：
系統運行後，只需在 Telegram 對機器人發送 「更新你自己」，系統即會在背景全自動執行 update.sh，完成無縫升級。

🚀 進階玩法 (Advanced)
住宅 IP 落地繞過風控：若遇到 browse_website 被 Cloudflare 攔截，建議在 VPS 本地部署 aimili-vpngate 獲取乾淨住宅 IP，並透過路由分流 (Policy Routing) 將抓取流量指向該本地端口 (如 127.0.0.1:7928)。

Web 模型熱切換：訪問 http://你的IP:5000 登入控制中心，可即時修改 .env 並套用，Telegram 端將即刻生效。

👨‍💻 作者 (Author)
HO - QS & Rebar Detailer based in Hong Kong
