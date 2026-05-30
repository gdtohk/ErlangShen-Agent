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
