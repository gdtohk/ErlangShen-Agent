#!/bin/bash

# 1. 進入腳本所在目錄 (確保路徑正確)
cd "$(dirname "$0")"

# 2. 倒數 3 秒 (極度重要：留時間畀二郎神喺 Telegram 講遺言)
echo "等待 3 秒讓主程式發送最後回覆..."
sleep 3

# 3. 獲取 GitHub 最新代碼
echo "📥 正在拉取 GitHub 最新裝備..."
git fetch --all
git reset --hard origin/main

# 放寬狙擊範圍 (移除 python3 字眼)，確保無論二郎神身處咩環境，只要叫 bot.py 都一定殺得死
echo "🔫 正在終止舊版二郎神與網頁後台..."
pkill -f "bot.py"
pkill -f "web_admin.py"

# 確保進程死透
sleep 2

# 核心修復！強制使用 ./venv/bin/python3 絕對路徑啟動，防止二郎神靈魂出竅跌入系統底層嘅平行時空
echo "🚀 浴火重生！正在喚醒新版二郎神..."
nohup ./venv/bin/python3 bot.py > agent.log 2>&1 &
nohup ./venv/bin/python3 web_admin.py > admin.log 2>&1 &

echo "✅ 全自動升級與重啟完畢！"
