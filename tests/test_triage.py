# -*- coding: utf-8 -*-
"""triage.py 分诊层自检：域完整性 / 追问词全部可驱动引擎 / 追问闭环真能判出证型"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.triage import (DOMAINS, BASELINE, GENERIC_WORDS, detect_domains, is_generic,
                        triage, render_triage, probe_symptom_words)
from src.normalize import ALL_KEYWORDS
from src.knowledge import SYNDROME_HINTS
from src.agent import diagnose, assess

PASS = FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {extra}")


clue_keys = set()
for d in SYNDROME_HINTS.values():
    clue_keys.update(d.keys())

print("== 域结构完整性 ==")
check("域数量 = 10", len(DOMAINS) == 10, len(DOMAINS))
check("域名称唯一", len({d["名"] for d in DOMAINS}) == len(DOMAINS))
for d in DOMAINS:
    check(f"[{d['名']}] 有触发词/生活/就医/3问",
          bool(d["触发"]) and bool(d["生活"]) and bool(d["就医"]) and len(d["追问"]) == 3,
          f"{len(d['触发'])}/3问={len(d['追问'])}")
    for q in d["追问"]:
        check(f"[{d['名']}] 问句非空且有选项", bool(q["问"]) and len(q["选项"]) >= 2,
              f"选项={len(q['选项'])}")

print("== 追问选项不许有死词（既非症状词也非线索键 = 选了没用）==")
dead = [(d["名"], label, w)
        for d in DOMAINS for q in d["追问"]
        for label, ws in q["选项"].items() for w in ws
        if w not in ALL_KEYWORDS and w not in clue_keys]
check("无死词", not dead, str(dead[:5]))

print("== 触发与泛化判定 ==")
for text, want in [("肚子胀、吃不下", "消化"), ("睡不着、多梦", "睡眠"),
                   ("腰酸背痛", "疼痛"), ("月经量少", "妇科"),
                   ("小便黄", "二便"), ("头晕眼花", "头面五官")]:
    names = [d["名"] for d, _ in detect_domains(text)]
    check(f"「{text}」→ {want}", want in names, str(names))
check("不相关文本不命中域", detect_domains("今天天气不错") == [])
check("泛化词识别", is_generic("最近状态不好") and is_generic("浑身不得劲"))
check("非泛化词不误判", not is_generic("肚子胀 吃不下"))

print("== triage() 结构 ==")
t = triage("肚子老是不舒服")
check("返回 3 个键", set(t) == {"笼统", "域", "底盘"}, sorted(t))
check("命中消化域", t["域"] and t["域"][0]["名"] == "消化", str([d["名"] for d in t["域"]]))
check("带追问", len(t["域"][0]["追问"]) == 3)
check("底盘 4 条", len(t["底盘"]) == 4)
t2 = triage("不太舒服")
check("泛化输入 笼统=True", t2["笼统"] is True)
t3 = triage("今天天气不错")
check("无域时仍给底盘", t3["域"] == [] and len(t3["底盘"]) == 4)
check("render_triage 非空", len(render_triage(t)) > 100)
check("probe_symptom_words 非空", len(probe_symptom_words("消化")) > 5)

print("== 追问闭环：答完必须能判出证型 ==")
# 模拟用户：主诉笼统 + 按追问勾选 → 应能得到一个有把握的证型
CASES = [
    ("肚子老是不舒服", ["胀（吃一点就胀）", "会，怕凉、喜欢热的", "稀、不成形"]),
    ("睡不好", ["躺下睡不着", "心里烦、停不下来", "口干、手心脚心热"]),
    ("总觉得累", ["睡了也不解乏、整天没劲", "吃不下、大便稀", "长期熬夜或睡不够"]),
    ("腰酸背痛", ["腰（酸软）", "酸软无力", "怕冷"]),
    ("月经不太正常", ["量少、色淡", "小腹冷痛、热敷缓解", "怕冷、手脚凉"]),
]
for main_text, picks in CASES:
    t = triage(main_text)
    adds, clues = [], []
    for d in t["域"]:
        for q in d["追问"]:
            for label, ws in q["选项"].items():
                if label in picks:
                    for w in ws:
                        (adds if w in ALL_KEYWORDS else clues).append(w)
    hs = {}
    for c in clues:
        hs[c] = True
    r = diagnose(adds, hs)
    conf = assess(r) if r else {"等级": "无"}
    ok = bool(r) and conf["等级"] in ("较高", "中等")
    check(f"「{main_text}」补 {len(picks)} 项 → {r[0]['证型'] if r else '无'}（{conf['等级']}）", ok,
          f"adds={adds} clues={clues}")

print(f"\n总计: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
