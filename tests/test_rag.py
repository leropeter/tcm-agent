# -*- coding: utf-8 -*-
"""test_rag.py — 典籍检索(RAG)自检
用法: python tests/test_rag.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.rag import build_index, search, enrich

P = F = 0
def ck(name, cond):
    global P, F
    if cond: P += 1; print(f"  ✅ {name}")
    else: F += 1; print(f"  ❌ {name}")

chunks, total = build_index()
print(f"== 索引（{len(chunks)} 块 / {total} 本书）==")
ck("加载了21本书", total >= 20)
ck("切块非空", len(chunks) > 100)

print("== 检索命中 ==")
def has_hit(q):
    return len(search(q, 3)) > 0
ck("心烦失眠能命中", has_hit(["心烦","失眠"]))
ck("黄连能命中(本草纲目)", has_hit(["黄连"]))
ck("舌苔腻能命中", has_hit(["舌苔腻","大便黏腻"]))

print("== 结果结构 ==")
r = search(["心烦","失眠"], 2)
ck("返回字典含 书/片段/得分", bool(r) and all(all(k in h for k in ["书","片段","得分"]) for h in r))
ck("按得分降序", r == sorted(r, key=lambda x: x["得分"], reverse=True))

print("== enrich(供UI展示) ==")
e = enrich(["心烦","失眠"], 2)
ck("enrich非空且含片段", bool(e) and all("片段" in x for x in e))
ck("片段非空", all(len(x["片段"]) > 10 for x in e))

print("== 边界 ==")
ck("空查询返回空", search([]) == [])

print(f"\n总计: {P} 通过 / {F} 失败")
sys.exit(1 if F else 0)
