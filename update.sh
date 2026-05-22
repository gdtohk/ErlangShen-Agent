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

# 4. 精準狙擊舊進程 (放棄 killall 地圖炮，改用 pkill 精準擊殺，唔會傷及無辜)
echo "🔫 正在終止舊版二郎神與網頁後台..."
pkill -f "python3 bot.py"
pkill -f "python3 web_admin.py"

# 確保進程死透
sleep 2

# 5. 重新喚醒新大腦
echo "🚀 浴火重生！正在喚醒新版二郎神..."
nohup python3 bot.py > agent.log 2>&1 &
nohup python3 web_admin.py > admin.log 2>&1 &

echo "✅ 全自動升級與重啟完畢！"
