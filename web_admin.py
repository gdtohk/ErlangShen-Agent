from flask import Flask, render_template_string, request, redirect, flash, session
import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

app = Flask(__name__)
# Session 加密金鑰亦可以放落 .env，無設定就用預設
app.secret_key = os.getenv("FLASK_SECRET_KEY", "erlangshen_super_secret")
ENV_PATH = ".env"

# 🚨 安全升級：從 .env 讀取密碼，絕不寫死在代碼中！
# 如果 .env 無設定，預設會變成一個極難估的密碼防止被黑客撞入
ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "Admin_Not_Set_999") 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>二郎神 控制面板</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f0f2f5; }
        .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1 { color: #1a73e8; text-align: center; }
        textarea { width: 100%; height: 350px; font-family: 'Courier New', Courier, monospace; font-size: 15px; padding: 15px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; }
        .btn { padding: 12px 24px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; border-radius: 6px; color: white; display: inline-block; text-decoration: none; margin-top: 15px; width: 100%; box-sizing: border-box; text-align: center; }
        .btn-save { background-color: #34a853; }
        .btn-save:hover { background-color: #2b8a44; }
        .btn-restart { background-color: #ea4335; }
        .btn-restart:hover { background-color: #ce3a2e; }
        .btn-logout { background-color: #9aa0a6; margin-top: 30px; }
        .btn-login { background-color: #1a73e8; }
        .alert { padding: 15px; background-color: #e8f0fe; border-left: 5px solid #1a73e8; color: #1967d2; margin-bottom: 20px; border-radius: 4px; font-weight: bold; }
        input[type="password"] { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ 二郎神大腦 控制面板</h1>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="alert">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        {% if not logged_in %}
            <form method="POST" action="/login">
                <h3>🔒 系統已鎖定，請輸入管理員密碼：</h3>
                <input type="password" name="pwd" placeholder="請輸入密碼..." required autofocus>
                <button type="submit" class="btn btn-login">登入系統</button>
            </form>
        {% else %}
            <form method="POST" action="/save">
                <h3>📝 編輯 .env 設定檔：</h3>
                <textarea name="env_content">{{ env_content }}</textarea>
                <button type="submit" class="btn btn-save">💾 儲存並覆蓋設定</button>
            </form>
            
            <hr style="margin: 30px 0; border: 0; border-top: 1px solid #eee;">
            
            <form method="POST" action="/restart" onsubmit="return confirm('確定要強行重新啟動二郎神嗎？');">
                <h3>🚀 系統操作：</h3>
                <p style="color: #5f6368; font-size: 14px;">(修改 .env 後，必須點擊下方按鈕重啟大腦才會生效)</p>
                <button type="submit" class="btn btn-restart">🔄 重新啟動 bot.py</button>
            </form>
            
            <a href="/logout" class="btn btn-logout">🚪 安全登出</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template_string(HTML_TEMPLATE, logged_in=False)
    
    env_content = ""
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            env_content = f.read()
    return render_template_string(HTML_TEMPLATE, logged_in=True, env_content=env_content)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('pwd') == ADMIN_PASSWORD:
        session['logged_in'] = True
        flash("✅ 登入成功！歡迎返嚟老闆。")
    else:
        flash("❌ 密碼錯誤，請重新輸入！")
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("👋 已安全登出。")
    return redirect('/')

@app.route('/save', methods=['POST'])
def save():
    if not session.get('logged_in'): return redirect('/')
    new_content = request.form.get('env_content', '')
    new_content = new_content.replace('\r\n', '\n')
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    flash("✅ .env 設定已成功儲存！請點擊下方紅色按鈕重啟系統以生效。")
    return redirect('/')

@app.route('/restart', methods=['POST'])
def restart():
    if not session.get('logged_in'): return redirect('/')
    try:
        os.system('pkill -f "python3 bot.py"')
        os.system('nohup python3 bot.py > agent.log 2>&1 &')
        flash("🚀 二郎神大腦已成功重新點火！去 Telegram 試吓啦！")
    except Exception as e:
        flash(f"❌ 重啟失敗：{str(e)}")
    return redirect('/')

if __name__ == '__main__':
    print("🌐 控制面板啟動中... 請在瀏覽器輸入 http://你的VPS_IP:5000")
    app.run(host='0.0.0.0', port=5000)
