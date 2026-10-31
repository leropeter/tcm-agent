# -*- coding: utf-8 -*-
"""模糊/似是而非输入的覆盖率 + 精确度基线

用法: python scripts/regress_vague.py
判据（三档，不再只看有没有结论）：
  较高  可以当结论用
  中等  方向清楚，可参考
  较低  只算"倾向"，不得当结论（这是精准的底线）
  无    不猜证型，走分诊追问
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.agent import diagnose, assess

VAGUE = [
    "最近状态不好", "浑身不得劲", "睡不好", "吃不下", "总觉得累", "身体发沉",
    "不太舒服", "有点上火", "没精神，也不想吃饭", "老是感冒", "手脚发凉",
    "掉头发厉害", "脸色不好", "肚子老是不舒服", "晚上睡不好白天没劲",
    "心里烦，静不下来", "身上痒", "嘴里没味", "眼睛干涩，看东西模糊", "腰酸背痛",
    "总想叹气", "一累就头晕", "大便不成形", "总觉得渴", "睡觉出汗",
    "冬天特别怕冷", "吃一点就胀", "心慌，容易紧张", "记性变差了", "嗓子老有痰",
]

ADULT = {"男性": True}
MARKS = {"较高": "✅", "中等": "🌤", "较低": "❔", "无": "➖"}

cnt = {"较高": 0, "中等": 0, "较低": 0, "无": 0}
print("=" * 92)
print(f"{'':3}{'把握':5}{'输入':24}{'证型/去向':18}{'分':>4}  说明")
print("=" * 92)
for text in VAGUE:
    r = diagnose(text, ADULT)
    conf = assess(r)
    lvl = conf["等级"]
    cnt[lvl] += 1
    syn = r[0]["证型"] if r else "→ 分诊追问"
    sc = r[0]["得分"] if r else 0
    note = conf["说明"] if r else "不猜证型，给通用调理+追问"
    print(f"{MARKS[lvl]:3}{lvl:5}{text:24}{syn:18}{sc:>3}  {note[:34]}")

n = len(VAGUE)
print("=" * 92)
print(f"较高 {cnt['较高']}  中等 {cnt['中等']}  较低 {cnt['较低']}  无 {cnt['无']}   (共 {n})")
print(f"能给出方向（不含「无」）= {(n-cnt['无'])/n*100:.0f}%   可当结论（较高）= {cnt['较高']/n*100:.0f}%")
