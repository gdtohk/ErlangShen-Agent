from flask import Flask, render_template_string, request, redirect, flash, session, jsonify
import os, json, urllib.request
from dotenv import load_dotenv, dotenv_values

# 載入 .env 檔案
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "erlangshen_super_secret")
ENV_PATH = ".env"
ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "Admin_Not_Set_999") 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>二郎神大腦 控制中心</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
        .login-container { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1, h3 { color: #1a73e8; text-align: center; }
        
        /* 聊天室 UI */
        .chat-container { max-width: 900px; margin: 20px auto; width: 95%; flex: 1; display: flex; flex-direction: column; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; position: relative; }
        .chat-header { background: #1a73e8; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; }
        .chat-box { flex: 1; padding: 20px; overflow-y: auto; background: #fafafa; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 75%; padding: 12px 18px; border-radius: 8px; line-height: 1.5; font-size: 15px; word-wrap: break-word; }
        .msg-user { background: #1a73e8; color: white; align-self: flex-end; border-bottom-right-radius: 0; }
        .msg-ai { background: #e9ecef; color: black; align-self: flex-start; border-bottom-left-radius: 0; }
        .chat-input-area { padding: 15px; background: white; border-top: 1px solid #ddd; display: flex; gap: 10px; }
        .chat-input-area input { flex: 1; padding: 12px; font-size: 15px; border: 1px solid #ccc; border-radius: 6px; outline: none; }
        .chat-input-area button { padding: 12px 24px; font-size: 15px; font-weight: bold; background: #34a853; color: white; border: none; border-radius: 6px; cursor: pointer; transition: 0.3s; }
        .chat-input-area button:hover { background: #2b8a44; }

        /* 左下角 Setting 按鈕 */
        .setting-btn { position: fixed; bottom: 20px; left: 20px; background: #5f6368; color: white; border: none; border-radius: 50px; padding: 12px 20px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: 0.3s; z-index: 100; }
        .setting-btn:hover { background: #3c4043; transform: scale(1.05); }

        /* Modal 設定視窗 */
        .modal { display: {% if show_settings %}block{% else %}none{% endif %}; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); overflow: auto; }
        .modal-content { background-color: #fff; margin: 5% auto; padding: 30px; border-radius: 12px; width: 90%; max-width: 800px; position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
        .close-btn { position: absolute; right: 20px; top: 15px; font-size: 28px; font-weight: bold; color: #aaa; cursor: pointer; }
        .close-btn:hover { color: black; }
        
        /* 表單元素 */
        textarea { width: 100%; height: 350px; font-family: 'Courier New', Courier, monospace; font-size: 14px; padding: 15px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; }
        input[type="password"], input[type="text"] { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; margin-bottom: 15px; }
        .btn-save { background-color: #34a853; color: white; padding: 12px; width: 100%; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 15px; }
        .btn-restart { background-color: #ea4335; color: white; padding: 12px; width: 100%; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 15px; }
        .btn-logout { display: block; text-align: center; background-color: #9aa0a6; color: white; padding: 10px; border-radius: 6px; text-decoration: none; margin-top: 30px; font-weight: bold; }
        .alert { padding: 15px; background-color: #e8f0fe; border-left: 5px solid #1a73e8; color: #1967d2; margin-bottom: 20px; border-radius: 4px; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <div style="position: absolute; top: 10px; width: 100%; z-index: 2000;">
            {% for message in messages %}
                <div class="alert" style="max-width: 600px; margin: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">{{ message }}</div>
            {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    {% if not logged_in %}
    <div class="login-container">
        <h1>⚙️ 二郎神 控制中心</h1>
        <form method="POST" action="/login">
            <h3>🔒 系統已鎖定，請登入：</h3>
            <input type="password" name="pwd" id="pwdInput" placeholder="請輸入管理員密碼..." required autofocus>
            <div style="text-align: right; margin-top: -10px; margin-bottom: 15px;">
                <label style="font-size: 14px; color: #5f6368; cursor: pointer;">
                    <input type="checkbox" onclick="document.getElementById('pwdInput').type = this.checked ? 'text' : 'password';"> 👁️ 顯示密碼
                </label>
            </div>
            <button type="submit" style="width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer;">登入系統</button>
        </form>
    </div>
    {% else %}
    
    <!-- 聊天室主畫面 -->
    <div class="chat-container">
        <div class="chat-header">🤖 二郎神大腦 - API 引擎測試頻道</div>
        <div class="chat-box" id="chatBox">
            <div class="message msg-ai">老闆，歡迎嚟到測試頻道！呢度可以幫你直接測試 .env 裡面嘅 API 引擎有無通。請隨便問我問題！</div>
        </div>
        <div class="chat-input-area">
            <input type="text" id="userInput" placeholder="輸入測試文字..." onkeypress="if(event.key === 'Enter') sendMessage()">
            <button onclick="sendMessage()">發送</button>
        </div>
    </div>

    <!-- 左下角設定按鈕 -->
    <button class="setting-btn" onclick="document.getElementById('settingsModal').style.display='block'">⚙️ Setting</button>

    <!-- 設定 Modal 彈出視窗 -->
    <div id="settingsModal" class="modal">
        <div class="modal-content">
            <span class="close-btn" onclick="document.getElementById('settingsModal').style.display='none'">&times;</span>
            <h1>⚙️ Configuration Panel</h1>
            <form method="POST" action="/save">
                <h3>📝 編輯 .env 設定檔：</h3>
                <textarea name="env_content">{{ env_content }}</textarea>
                <button type="submit" class="btn-save">💾 儲存並覆蓋設定</button>
            </form>
            <hr style="margin: 30px 0; border: 0; border-top: 1px solid #eee;">
            <form method="POST" action="/restart" onsubmit="return confirm('確定要強行重新啟動二郎神嗎？');">
                <h3>🚀 系統操作：</h3>
                <p style="color: #5f6368; font-size: 14px;">(修改 .env 後，必須點擊下方按鈕重啟大腦才會生效)</p>
                <button type="submit" class="btn-restart">🔄 重新啟動 bot.py</button>
            </form>
            <a href="/logout" class="btn-logout">🚪 安全登出</a>
        </div>
    </div>

    <script>
        // 聊天室發送訊息邏輯
        async function sendMessage() {
            const inputField = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const text = inputField.value.trim();
            if (!text) return;

            // 顯示用戶訊息
            const userMsg = document.createElement('div');
            userMsg.className = 'message msg-user';
            userMsg.textContent = text;
            chatBox.appendChild(userMsg);
            inputField.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            // 顯示 AI 思考中
            const aiMsg = document.createElement('div');
            aiMsg.className = 'message msg-ai';
            aiMsg.textContent = '⏳ 引擎連線中...';
            chatBox.appendChild(aiMsg);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                
                if (data.reply) {
                    aiMsg.innerHTML = data.reply.replace(/\\n/g, '<br>');
                } else {
                    aiMsg.textContent = '❌ ' + (data.error || '發生未知錯誤');
                }
            } catch (err) {
                aiMsg.textContent = '❌ 網絡錯誤或後端無回應。';
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        // 點擊 Modal 外圍自動關閉視窗
        window.onclick = function(event) {
            var modal = document.getElementById('settingsModal');
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }
    </script>
    {% endif %}
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
    
    # 判斷是否剛剛 Save 完需要自動彈出 Modal
    show_settings = request.args.get('show_settings') == '1'
    return render_template_string(HTML_TEMPLATE, logged_in=True, env_content=env_content, show_settings=show_settings)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('pwd') == ADMIN_PASSWORD:
        session['logged_in'] = True
        flash("✅ 登入成功！歡迎返嚟。")
    else:
        flash("❌ 密碼錯誤！")
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/save', methods=['POST'])
def save():
    if not session.get('logged_in'): return redirect('/')
    new_content = request.form.get('env_content', '')
    new_content = new_content.replace('\r\n', '\n')
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    flash("✅ 設定已儲存！請緊記點擊「重新啟動 bot.py」令新設定生效。")
    # 儲存後保持 Modal 開啟
    return redirect('/?show_settings=1')

@app.route('/restart', methods=['POST'])
def restart():
    if not session.get('logged_in'): return redirect('/')
    try:
        os.system('pkill -f "python3 bot.py"')
        os.system('nohup python3 bot.py > agent.log 2>&1 &')
        flash("🚀 前線大腦 (bot.py) 已成功重新啟動！")
    except Exception as e:
        flash(f"❌ 重啟失敗：{str(e)}")
    return redirect('/?show_settings=1')

# --- 新增：純文字 API 測試對話接口 ---
@app.route('/api/chat', methods=['POST'])
def api_chat():
    if not session.get('logged_in'): return jsonify({"error": "未授權訪問"}), 401
    
    user_text = request.json.get('message', '')
    if not user_text: return jsonify({"error": "內容不能為空"}), 400

    # 每次對話都實時讀取 .env，保證測試到最新設定
    config = dotenv_values(ENV_PATH)
    model = config.get("MODEL_NAME", "gemini-3.1-flash-lite-preview")
    
    # 尋找第一個未被 # 封印嘅引擎
    api_url, api_key = None, None
    for i in range(1, 11):
        u = config.get(f"API_URL_{i}")
        k = config.get(f"API_KEY_{i}")
        if u and k:
            api_url, api_key = u, k
            break
            
    if not api_url:
        api_url = config.get("API_URL_3")
        api_key = config.get("API_KEY_3")

    if not api_url or not api_key:
        return jsonify({"error": "找不到有效的 API 引擎，請打開 Setting 檢查配置！"}), 500

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_text}]
    }

    req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')
    if 'googleapis.com' in api_url:
        req.add_header('x-goog-api-key', api_key)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            reply = res_data['choices'][0]['message']['content']
            return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": f"連線失敗 (可能係 HTTP 400 / 429 錯誤) : {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
