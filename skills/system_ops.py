import subprocess

async def update_from_github(**kwargs):
    """從 GitHub 拉取最新代碼 (git pull)"""
    print("🔄 [Debug] 準備執行 git pull 拉取更新...")
    try:
        # 使用 subprocess 執行 shell 指令
        result = subprocess.run(
            ['git', 'pull'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        reply_msg = (
            "✅ **成功從 GitHub 拉取最新代碼！**\n\n"
            "**系統輸出：**\n"
            f"```text\n{result.stdout.strip()}\n```\n"
            "⚠️ **老闆注意：** 代碼已更新，但你需要喺 VPS 重新啟動一次程式 (`python3 bot.py`) 新功能先會正式生效喔！"
        )
        print(f"✅ [Debug] git pull 成功: {result.stdout.strip()}")
        return reply_msg

    except subprocess.CalledProcessError as e:
        error_msg = f"❌ 拉取代碼失敗！\n\n**錯誤信息：**\n```text\n{e.stderr.strip()}\n```"
        print(f"❌ [Debug] git pull 失敗: {e.stderr.strip()}")
        return error_msg
    except Exception as e:
        return f"❌ 發生未知錯誤：{str(e)}"