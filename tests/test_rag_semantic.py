# -*- coding: utf-8 -*-
"""test_rag_semantic.py — 语义检索(可选RAG)自检
仅验证纯逻辑(降级路径) + 有本地索引时的语义检索；无索引则跳过语义部分。
用法: python run_tests.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src import rag_semantic

P = F = 0
def ck(name, cond):
    global P, F
    if cond: P += 1; print(f"  ✅ {name}")
    else: F += 1; print(f"  ❌ {name}")

print("== 降级路径（无需模型/索引，纯逻辑）==")
_orig = rag_semantic.INDEX_DIR
rag_semantic.INDEX_DIR = os.path.join(rag_semantic.BASE, "..", "data", "_no_such_index_")
try:
    ck("未预构建索引时返回空(降级关键词)", rag_semantic.search(["肾虚"]) == [])
finally:
    rag_semantic.INDEX_DIR = _orig

print("== 语义检索（本地有索引时才验证）==")
vec = os.path.join(rag_semantic.INDEX_DIR, "vectors.npy")
meta = os.path.join(rag_semantic.INDEX_DIR, "meta.json")
if os.path.exists(vec) and os.path.exists(meta):
    r = rag_semantic.search(["肾虚 腰酸 夜尿多"], 3)
    ck("语义检索返回非空", bool(r))
    ck("结果含 书/片段/得分", bool(r) and all(all(k in x for k in ["书","片段","得分"]) for x in r))
    ck("命中肾虚相关典籍", bool(r) and any(k in " ".join(x["书"] for x in r) for k in ["千金要方","黄帝内经","素问"]))
else:
    print("  （本地无语义索引，跳过语义部分——默认走关键词检索）")

print(f"\n总计: {P} 通过 / {F} 失败")
sys.exit(1 if F else 0)
