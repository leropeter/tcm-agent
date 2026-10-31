# -*- coding: utf-8 -*-
"""置信度三档是否真的分得开 —— 典型/中等/模糊/泛化四组对照

用法: python scripts/show_confidence.py
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.agent import diagnose, assess

ADULT = {"男性": True}

GROUPS = [
    ("典型（信息充足，应给「较高」）", [
        ("头痛 怕冷 流清涕 无汗", "风寒束表"),
        ("吃不下饭 人也没劲 大便稀 面色萎黄", "脾气虚"),
        ("心烦 失眠 口舌生疮 小便黄", "心火亢盛"),
        ("腰膝酸软 畏寒肢冷 夜尿多", "肾阳虚"),
        ("干咳无痰 口燥咽干 舌红少苔", "肺阴虚"),
        ("胁肋胀痛 爱叹气 情绪抑郁", "肝郁气滞"),
    ]),
    ("中等（2-3 个症状，应给「中等」或「较高」）", [
        ("失眠 多梦", None),
        ("头晕 乏力", None),
        ("口干 手脚心热", None),
        ("腹胀 便溏", None),
    ]),
    ("模糊（单个词，最多「较低」）", [
        ("总觉得渴", None),
        ("身上痒", None),
        ("记性差", None),
        ("嗓子有痰", None),
        ("心慌", None),
    ]),
    ("泛化（应走分诊，不给证型）", [
        ("不太舒服", None),
        ("最近状态不好", None),
        ("浑身不得劲", None),
    ]),
]

MARKS = {"较高": "✅", "中等": "🌤", "较低": "❔", "无": "➖"}
bad = []

for gname, cases in GROUPS:
    print("\n" + "=" * 78)
    print(gname)
    print("-" * 78)
    for text, expect in cases:
        r = diagnose(text, ADULT)
        conf = assess(r)
        lvl = conf["等级"]
        syn = r[0]["证型"] if r else "→ 分诊追问"
        print(f"{MARKS[lvl]} {lvl:4} {text:30} {syn:14} {conf['说明'][:26]}")
        if expect and syn != expect:
            bad.append((text, f"期望 {expect} 实得 {syn}"))
    # 组级断言
    levels = [assess(diagnose(t, ADULT))["等级"] for t, _ in cases]
    if gname.startswith("典型") and levels.count("较高") < len(cases) - 1:
        bad.append(("典型组", f"较高 仅 {levels.count('较高')}/{len(cases)}"))
    if gname.startswith("模糊") and "较高" in levels:
        bad.append(("模糊组", "出现了「较高」，过度自信"))
    if gname.startswith("泛化") and any(l != "无" for l in levels):
        bad.append(("泛化组", f"应全为「无」，实得 {levels}"))

print("\n" + "=" * 78)
print("分档结果：" + ("三档区分正常" if not bad else f"异常 {bad}"))
sys.exit(1 if bad else 0)
