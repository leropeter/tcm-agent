# -*- coding: utf-8 -*-
"""口语输入回归测试：评估"用户随口说话"条件下的辨证命中率。
用法：python scripts/regress_slang.py
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.agent import diagnose, parse_symptoms

# (口语输入, 期望证型关键词)  —— 期望为空表示"只要给出诊断即可"
CASES = [
    ("最近总睡不着，还老做梦", ["心"]),
    ("吃不下饭，人也没劲，大便稀", ["脾"]),
    ("一吹风就头疼，还流清鼻涕", ["风寒"]),
    ("脾气特别大，爱叹气，两肋胀", ["肝郁"]),
    ("手脚冰凉，特别怕冷，腰也酸", ["肾阳"]),
    ("手心脚心老是发热，晚上出汗", ["阴虚"]),
    ("嗓子疼，吐黄痰，还发烧", ["风热"]),
    ("肚子胀，吃一点就胀，老打嗝", ["脾", "胃"]),   # 脾虚气滞 / 胃气上逆 临床均可
    ("头晕，耳朵嗡嗡响，腰酸", ["肝肾", "肾", "肝阳"]),  # 肝阳上亢(本虚标实) 与 肝肾亏虚 需鉴别
    ("老想叹气，胸口闷，心情差", ["肝郁", "肝"]),
    ("舌边有齿痕，人容易累", ["脾"]),
    ("尿黄，嘴里苦，爱发火", ["肝火", "肝"]),
    ("咳嗽没什么痰，嗓子干，晚上咳得厉害", ["肺"]),
    ("早上起来脸肿，腿也肿", ["脾", "肾"]),
    ("一动就一身汗，还特别容易感冒", ["气", "表"]),
    ("胃里反酸，烧心，嘴里还苦", ["胃", "肝"]),
]

hit = 0
ADULT = {"男性": True}   # 模拟网页端"成人"默认问诊信息（会排除儿科证型）

# 自检：同义词表不得指向知识库里不存在的词（死映射会让整条规则空转）
from src.normalize import SYNONYMS, ALL_KEYWORDS
_dead = {s: [x for x in v if x not in ALL_KEYWORDS] for s, v in SYNONYMS.items()}
_dead = {s: v for s, v in _dead.items() if v}
print("=" * 78)
print(f"[自检] 同义词表 {len(SYNONYMS)} 条，死映射: {_dead or '无'}")
if _dead:
    print("!! 请修正上述映射目标，否则对应口语输入无效")
print("=" * 78)
for text, expect in CASES:
    res = diagnose(text, ADULT)
    got = res[0]["证型"] if res else None
    ok = bool(got) and (not expect or any(e in got for e in expect))
    hit += 1 if ok else 0
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {text}")
    print(f"        -> {got or '（未匹配到任何证型）'}   期望≈{expect or '任意'}")
print("=" * 78)
print(f"命中 {hit}/{len(CASES)} = {hit/len(CASES)*100:.0f}%")
