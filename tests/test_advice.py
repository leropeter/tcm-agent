# -*- coding: utf-8 -*-
"""advice.py 差异化建议层自检：维度齐全 / 红旗识别 / 季节切换 / 人群禁忌"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.agent import diagnose
from src.advice import build_plan, current_season, render_text, SEASONS
from src.knowledge import TCM_SYNDROMES

PASS = FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


print("== 因时：四季齐全且可切换 ==")
check("四季定义齐全", set(SEASONS) == {"春", "夏", "长夏", "秋", "冬"})
for m, want in [(3, "春"), (6, "夏"), (9, "秋"), (12, "冬"), (1, "冬")]:
    check(f"{m}月->{want}", current_season(m) == want)
p = build_plan([], {}, [], month=7)
check("因时字段完整", all(k in p["因时"] for k in ("重点", "饮食", "起居", "茶饮", "穴位", "提醒")))

print("== 因人：人群要点正确落地 ==")
for pop, needle in [("中老年", "缓"), ("年轻", "实"), ("女性", "血"), ("男性", "酒"), ("经期", "寒"), ("孕期", "产科")]:
    p = build_plan([], {pop: True}, [])
    hit = next((x for x in p["因人"] if x["人群"] == pop), None)
    blob = (hit["要点"] + hit.get("穴位", "") + hit.get("饮食", "")) if hit else ""
    check(f"{pop} 出现且含关键词「{needle}」", hit is not None and needle in blob)

print("== 孕期安全：禁活血/峻下穴位 ==")
p = build_plan(diagnose(["月经量少"]), {"孕期": True}, ["月经量少"])
pw = next(x for x in p["因人"] if x["人群"] == "孕期")
banned = ["合谷", "三阴交", "至阴", "关元", "气海", "血海", "昆仑"]
check("孕期穴位不含禁用穴", not any(b in pw["穴位"] for b in banned))
check("孕期饮食明确忌薏米山楂", "薏米" in pw["饮食"] and "山楂" in pw["饮食"])

print("== 因线索：16 条诱因全部可触发 ==")
from src.advice import LIFESTYLE_FIX
for clue in LIFESTYLE_FIX:
    p = build_plan([], {clue: True}, [])
    check(f"线索 {clue}", any(x["线索"] == clue for x in p["因线索"]))

print("== 对症：常见伴随症状可追加 ==")
from src.advice import SYMPTOM_EXTRA
for key in ["失眠", "便秘", "腹泻", "头晕", "口干", "怕冷", "水肿", "心悸", "腰"]:
    p = build_plan([], {}, [key])
    check(f"对症 {key}", any(x["对应"] == key for x in p["对症"]))

print("== 兼证：次要证型也给要点 ==")
r = diagnose("吃不下饭，人也没劲，大便稀", {"男性": True})
p = build_plan(r, {"男性": True}, ["吃不下饭", "人也没劲", "大便稀"])
check("兼证非空", len(p["兼证"]) >= 1)
check("兼证有点要", all(m["要点"] for m in p["兼证"]))
check("兼证不超过2条", len(p["兼证"]) <= 2)

print("== 禁忌：按证型性质给对应禁项 ==")
r = diagnose("头痛 怕冷 流清涕 无汗")
p = build_plan(r, {}, ["头痛", "怕冷", "流清涕", "无汗"])
check("外感证有禁忌", len(p["禁忌"]) == 1 and "进补" in p["禁忌"][0]["忌口"])
r = diagnose("心烦 失眠 口舌生疮")
p = build_plan(r, {}, ["心烦", "失眠", "口舌生疮"])
check("热证禁忌含辛辣", any("辛辣" in c["忌口"] for c in p["禁忌"]))

print("== 阶段：外感=急性，虚证=慢性 ==")
p = build_plan(diagnose("头痛 怕冷 流清涕"), {}, ["头痛"])
check("外感->急性期", "急性" in p["阶段"]["阶段"])
p = build_plan(diagnose("吃不下饭 没劲 大便稀"), {}, ["吃不下饭"])
check("虚证->慢性调理", "慢性" in p["阶段"]["阶段"])

print("== 就医红旗：命中与不命中 ==")
cases_hit = [
    (["胸痛", "出汗"], "急诊"),
    (["黑便"], "出血"),
    (["痰中带血"], "胸片"),
    (["晕厥"], "急诊"),
    (["说话不清", "麻木"], "120"),
]
for syms, needle in cases_hit:
    p = build_plan(diagnose(syms), {}, syms)
    check(f"红旗 {'+'.join(syms)}", any(needle in w for w in p["就医"]))
for syms in (["咽痛"], ["乏力"], ["失眠"]):
    p = build_plan(diagnose(syms), {}, syms)
    check(f"非红旗 {'+'.join(syms)} 不误报", p["就医"] == [])

print("== 渲染：非空且包含各维度标题 ==")
r = diagnose("吃不下饭，人也没劲，大便稀，失眠，怕冷", {"中老年": True, "熬夜": True})
p = build_plan(r, {"中老年": True, "熬夜": True}, ["吃不下饭", "人也没劲", "大便稀", "失眠", "怕冷"])
txt = render_text(p)
for tag in ["调理节奏", "因时", "因人", "针对", "兼顾", "兼证", "忌"]:
    check(f"渲染含「{tag}」", tag in txt)
check("渲染长度充足(>500字)", len(txt) > 500)

print("== 规模数字（防止文档与汇报手数错：改动数据表后这里会红，提醒同步更新说明）==")
from src.advice import CONTRA, RED_FLAGS, POPULATION
for label, actual, expected in [
    ("四季(+长夏)", len(SEASONS), 5),
    ("人群", len(POPULATION), 6),
    ("诱因线索", len(LIFESTYLE_FIX), 14),
    ("对症症状", len(SYMPTOM_EXTRA), 20),
    ("禁忌", len(CONTRA), 6),
    ("就医红旗", len(RED_FLAGS), 10),
]:
    check(f"{label} = {expected}（实际 {actual}）", actual == expected)

print("== 全证型不崩 ==")
crash = []
for s in TCM_SYNDROMES:
    try:
        k = max(s["symptoms"], key=s["symptoms"].get)
        rr = diagnose([k])
        build_plan(rr, {"女性": True, "熬夜": True}, [k])
    except Exception as e:
        crash.append((s["id"], repr(e)))
check("41 证型 build_plan 全部不崩", not crash)

print(f"\n总计: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
