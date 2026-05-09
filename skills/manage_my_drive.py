import os
import pandas as pd
import fitz
import re

async def manage_my_drive(chat_id, context, path: str = "") -> str:
    """
    瀏覽或讀取 my_drive 中的文件。
    """
    base_path = "/home/ubuntu/ErlangShen-Agent/my_drive"
    # 過濾並確保路徑安全，處理繁簡體及空白
    safe_path = path.replace("my_drive/", "").replace("铁", "鐵").lstrip("/")
    full_path = os.path.join(base_path, safe_path)

    if not os.path.exists(full_path):
        return f"❌ 找不到路徑：{safe_path}。請先叫我『睇下目錄』確認準確檔名。"

    # 如果是資料夾，返回目錄清單
    if os.path.isdir(full_path):
        try:
            items = os.listdir(full_path)
            if not items:
                return f"📂 資料夾 '{safe_path}' 是空的。"
            res = f"📂 資料夾 '{safe_path}' 內容清單：\n" + "\n".join([f"- {item}" for item in items])
            return res
        except Exception as e:
            return f"❌ 無法讀取資料夾：{str(e)}"
            
    # 如果是文件，讀取內容
    else:
        ext = os.path.splitext(full_path)[1].lower()
        try:
            if ext == '.pdf':
                doc = fitz.open(full_path)
                total_pages = len(doc)
                text = f"【PDF 文件：{safe_path} (共 {total_pages} 頁)】\n"
                
                # 優化：只提取前 5 頁，且總字數限制在 3500 字內，避免觸發 AI 安全審查
                raw_content = ""
                for i in range(min(5, total_pages)):  
                    raw_content += doc[i].get_text("text")
                
                # 清理多餘換行及特殊空白字元
                clean_content = re.sub(r'\n+', '\n', raw_content)
                clean_content = re.sub(r' +', ' ', clean_content)
                
                text += clean_content[:3500] 
                if len(raw_content) > 3500:
                    text += "\n\n...(內容過長，已截取前段供分析)..."
                return text
                
            elif ext in ['.xlsx', '.xls', '.csv']:
                if ext == '.csv':
                    df = pd.read_csv(full_path)
                else:
                    df = pd.read_excel(full_path)
                # 表格同樣截取前 50 行
                return f"【表格文件：{safe_path}】\n" + df.head(50).to_markdown(index=False)[:4000]
                
            elif ext in ['.txt', '.md', '.log']:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f"【文字文件：{safe_path}】\n" + f.read()[:4000]
            else:
                return f"❌ 暫時不支援解析 {ext} 格式的內容。"
                
        except Exception as e:
            return f"❌ 讀取文件失敗：{str(e)}"
