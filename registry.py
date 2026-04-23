from skills.scheduler import schedule_daily_weather
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
        desc = "設定未來的鬧鐘。當老闆要求「发信息给我」、「通知我」、「提醒我」、「叫我」時調用。",
        params = {
            "minutes": {
                "type": "number", 
                "description": "距離現在需要等待的分鐘數。請讀取系統注入的【當前香港時間】，心算出老闆指定的目標時間距離現在還有幾分鐘，並填入此數值。"
            },
            "message": {
                "type": "string", 
                "description": "要提醒的事情內容，例如『喝水』、『開會』"
            }
        },
        required = ["minutes", "message"]
    ),

    # 工具 4：每天定時天氣匯報
    "schedule_daily_weather": create_tool(
        func = schedule_daily_weather,
        name = "schedule_daily_weather",
        desc = "設定每天固定時間自動發送天氣報告。當老闆要求「每天早上X點報告天氣」時調用。",
        params = {
            "hour": {"type": "integer", "description": "小時 (0-23)，例如早上5點填5"},
            "minute": {"type": "integer", "description": "分鐘 (0-59)，例如半填30"}
        },
        required = ["hour", "minute"]
    )
}

GET_TOOLS_LIST = [tool["schema"] for tool in AGENT_TOOLS_REGISTRY.values()]
