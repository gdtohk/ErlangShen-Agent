# registry.py
from skills.rebar import calc_rebar_weight

# 🛠️ 自動生成說明書的輔助工具
def create_tool(func, name, desc, params, required):
    return {
        "func": func,
        "schema": {
            "type": "function",
            "function": {
                "name": name,
                "description": desc,
                "parameters": {"type": "object", "properties": params, "required": required}
            }
        }
    }

# --- 【智能工具註冊表】 ---
AGENT_TOOLS_REGISTRY = {
    # 工具 1：鋼筋計算機
    "calc_rebar_weight": create_tool(
        func = calc_rebar_weight,
        name = "calc_rebar_weight",
        desc = "計算鋼筋的重量。當老闆詢問鋼筋重量、公斤數或噸數時調用。",
        params = {
            "d": {"type": "number", "description": "直徑 (mm)"},
            "length": {"type": "number", "description": "長度 (m)"},
            "qty": {"type": "number", "description": "數量"}
        },
        required = ["d", "length"]
    )
}

# 自動匯出給 Gemini 大腦
GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]
