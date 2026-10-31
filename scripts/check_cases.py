# -*- coding: utf-8 -*-
"""医案检索效果抽查"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.cases import count, search, render

print(f"医案总数：{count()}")
QUERIES = [
    ["失眠", "多梦"],
    ["头晕", "耳鸣", "腰酸"],
    ["吃不下", "便溏", "乏力"],
    ["咳嗽", "痰黄", "发热"],
    ["痛经", "小腹冷痛"],
    ["口苦", "烦躁", "易怒"],
]
for q in QUERIES:
    items = search(q, top=2)
    print("\n" + "=" * 74)
    print(f"查询 {q} → 命中 {len(items)} 例")
    print(render(items, max_body=150) or "（无匹配）")
