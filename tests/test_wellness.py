# -*- coding: utf-8 -*-
"""test_wellness.py — 日常养生知识库自检
用法: python tests/test_wellness.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.wellness import DAILY_WELLNESS, daily_advice, pretty_wellness

P = F = 0
def ck(name, cond):
    global P, F
    if cond: P += 1; print(f"  ✅ {name}")
    else: F += 1; print(f"  ❌ {name}")

print(f"== 知识库完整性（{len(DAILY_WELLNESS)} 条日常养生）==")
ck("每条含 topic/keywords/advice", all(all(k in i for k in ["topic","keywords","advice"]) for i in DAILY_WELLNESS))
ck("每条有生活化建议", all(isinstance(i["advice"], dict) and i["advice"] for i in DAILY_WELLNESS))

print("== 匹配测试 ==")
def match_topic(text):
    r = daily_advice([text])
    return r[0]["条目"] if r else None
ck("失眠→失眠", match_topic("最近有点失眠") == "失眠·睡眠质量差")
ck("齿痕舌→齿痕", match_topic("舌头上有齿痕") == "舌边齿痕（脾虚湿盛常见表现）")
ck("手脚冰凉→手脚", match_topic("我手脚冰凉") == "手脚冰凉")
ck("大便不成形→脾虚湿盛", match_topic("大便不成形 黏腻") == "大便不成形·黏腻")
ck("眼干→眼干涩", match_topic("眼睛干涩") == "眼睛干涩")

print("== pretty_wellness 输出 ==")
p = pretty_wellness(["失眠"])
ck("输出含核心建议", "失眠" in p and "茶饮" in p)
ck("不含错误栈", "Traceback" not in p)

print("== 边界 ==")
ck("空输入", daily_advice([]) == [])
ck("未匹配返回空", daily_advice(["量子纠缠"]) == [])

print(f"\n总计: {P} 通过 / {F} 失败")
sys.exit(1 if F else 0)
