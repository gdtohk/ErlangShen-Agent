from skills.rebar import calc_rebar_weight
from skills.weather import get_hk_weather_detailed
from skills.reminder import set_reminder

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

AGENT_TOOLS_REGISTRY = {
    # 工具 1：鋼筋計算
    "calc_rebar_weight": create_tool(
        func = calc_rebar_weight,
        name = "calc_rebar_weight",
        desc = "計算鋼筋的重量。當詢問鋼筋重量時調用。",
        params = {
            "d": {"type": "number", "description": "直徑 (mm)"},
            "length": {"type": "number", "description": "長度 (m)"},
            "qty": {"type": "number", "description": "數量"}
        },
        required = ["d", "length"]
    ),
    
    # 工具 2：天氣預報
    "get_hk_weather_detailed": create_tool(
        func = get_hk_weather_detailed,
        name = "get_hk_weather_detailed",
        desc = "獲取香港最新天氣。當老闆問天氣、會不會下雨時調用。",
        params = {},
        required = []
    ),

    # 工具 3：定時提醒鬧鐘
    "set_reminder": create_tool(
        func = set_reminder,
        name = "set_reminder",
        desc = "設定未來的鬧鐘。當老闆要求「提醒我」、「叫我」時調用。",
        params = {
            "minutes": {
                "type": "number", 
                "description": "距離現在需要等待的分鐘數。如果老闆說'1小時後'填60。如果是具體時間，請你自己心算距離現在大約差幾分鐘填入。"
            },
            "message": {
                "type": "string", 
                "description": "要提醒的事情內容，例如『喝水』、『開會』"
            }
        },
        required = ["minutes", "message"]
    )
}

GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]
