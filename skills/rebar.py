# skills/rebar.py
async def calc_rebar_weight(d: float, length: float, qty: float = 1.0, **kwargs):
    """計算鋼筋重量的純運算函數"""
    try:
        unit_weight = (d ** 2) / 162
        total_weight = unit_weight * length * qty
        return f"計算成功：直徑 {d}mm, 長度 {length}m, 數量 {qty}支。單支重量 {unit_weight * length:.2f} kg, 總重量 {total_weight:.2f} kg。"
    except Exception as e:
        return f"計算失敗：{str(e)}"
