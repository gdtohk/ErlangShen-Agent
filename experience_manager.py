import json
import os
from datetime import datetime

class ExperienceManager:
    def __init__(self, file_path="experience.json"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    def add_experience(self, content):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                experiences = json.load(f)

            new_exp = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "content": content
            }
            experiences.append(new_exp)

            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(experiences, f, ensure_ascii=False, indent=4)
            return f"✅ 經驗已成功寫入大腦長期記憶庫！內容：{content}"
        except Exception as e:
            return f"❌ 寫入經驗失敗：{str(e)}"

    def get_all_experiences_formatted(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                experiences = json.load(f)

            if not experiences:
                return ""

            formatted_str = "\n\n【🧠 核心工作經驗與約束（你必須嚴格遵守以下過往教訓）】：\n"
            for exp in experiences:
                formatted_str += f"- [{exp['date']}] {exp['content']}\n"
            return formatted_str
        except:
            return ""

exp_manager = ExperienceManager()
