# -*- coding: utf-8 -*-
"""
rag.py — 轻量典籍检索（RAG，检索增强）
========================================
把 data/books/ 下的 21 本中医经典切成文本块，建立词频索引。
辨证时可按症状/关键词检索相关典籍原文，作为调养建议的出处参考。

⚠️ 这是"关键词/词频"轻量检索版（零第三方依赖、离线、别人下载即用）。
   后续可升级为语义向量检索（sentence-transformers + chromadb）。

设计：query 症状词 → 统计每个文本块中命中词频 → 加权打分 → 返回 TopK 块。
"""
import os, re
from functools import lru_cache

BOOKS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "books")

# 去掉 markdown 标记
_MD_STRIP = re.compile(r"[#>*`\-|]")
# 连续空白 → 单空格
_WS = re.compile(r"\s+")

# ---------- 文本切块 ----------
def _clean(text):
    """去掉 markdown 标记，压缩多余空白（保留语义）。"""
    text = _MD_STRIP.sub("", text)
    return _WS.sub(" ", text).strip()

def _chunk_text(raw, min_len=150):
    """
    按行切块：空行/标题行作为分隔，非空行合并到 min_len 左右。
    保留段落边界，避免整本书被压成一块。
    """
    chunks, cur = [], ""
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            if cur:
                chunks.append(cur); cur = ""
            continue
        cleaned = _clean(line)
        if not cleaned:
            continue
        cur = (cur + " " + cleaned).strip()
        if len(cur) >= min_len:
            chunks.append(cur); cur = ""
    if cur:
        chunks.append(cur)
    return chunks

@lru_cache(maxsize=1)
def build_index():
    """
    读取全部书 → 切块 → 建 [ (book, chunk_text), ... ] 列表。
    返回 (chunks, total_books)。
    """
    chunks = []
    if not os.path.isdir(BOOKS_DIR):
        return chunks, 0
    for fn in sorted(os.listdir(BOOKS_DIR)):
        if not fn.endswith(".md"):
            continue
        book = fn[:-3]  # 去掉 .md
        try:
            raw = open(os.path.join(BOOKS_DIR, fn), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for c in _chunk_text(raw):
            chunks.append((book, c))
    return chunks, len([f for f in os.listdir(BOOKS_DIR) if f.endswith(".md")])

# ---------- 检索 ----------
def _word_candidates(w):
    """完整词 + 2字子串候选，用于覆盖古籍/口语用词差异。"""
    if len(w) < 2:
        return [w]
    out = [w]
    if len(w) >= 3:
        out += [w[i:i+2] for i in range(len(w) - 1)]
    return out

def search(query_words, top_k=3):
    """
    query_words: list[str] 症状/关键词
    返回 [{书, 片段, 得分}]，按得分降序。
    匹配策略：完整词命中优先；未命中时退化为 2 字子串打折匹配（覆盖"舌苔腻"vs"苔腻"类差异）。
    """
    chunks, _ = build_index()
    if not chunks:
        return []
    scored = []
    for book, text in chunks:
        score = 0
        for w in query_words:
            if not w or len(w) < 2:
                continue
            full = text.count(w) * len(w)
            if full > 0:
                score += full
            elif len(w) >= 3:
                for i in range(len(w) - 1):
                    sub = w[i:i+2]
                    score += text.count(sub) * len(sub) * 0.5  # 子串打折降噪
        if score > 0:
            scored.append({"书": book, "片段": text, "得分": round(score, 1)})
    scored.sort(key=lambda x: x["得分"], reverse=True)
    return scored[:top_k]

def enrich(query_words, top_k=3):
    """给辨证结果附上典籍参考片段（人类可读）。"""
    hits = search(query_words, top_k)
    if not hits:
        return []
    out = []
    for h in hits:
        # 截取命中片段附近文字，便于阅读
        snippet = _around_first_hit(h["片段"], query_words, window=90)
        out.append({"书": h["书"], "片段": snippet, "得分": h["得分"]})
    return out

def _around_first_hit(text, words, window=90):
    """截取第一次命中某个关键词（含2字子串变体）的上下文。"""
    pos = -1
    for w in words:
        if w and len(w) >= 2:
            for cand in ([w] + ([w[i:i+2] for i in range(len(w)-1)] if len(w) >= 3 else [])):
                i = text.find(cand)
                if i != -1 and (pos == -1 or i < pos):
                    pos = i
    if pos == -1:
        return text[: window * 2]
    start = max(0, pos - window // 2)
    return "…" + text[start : pos + window] + "…"
