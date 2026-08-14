# -*- coding: utf-8 -*-
"""
rag_semantic.py — 语义检索（真正 RAG）
========================================
用 sentence-transformers 把 21 本中医经典切块向量化，语义检索（余弦相似度）。
相比 src/rag.py 的关键词硬匹配，能理解同义/近义表达（如"舌苔腻"≈"苔腻"≈"舌苔厚腻"）。

设计：
- 依赖可选：未安装 sentence-transformers / 无模型 / 构建失败时，search() 返回空，
  由调用方降级到关键词检索（src/rag.py）。
- 索引持久化到 data/vector_index/，首次构建较慢，之后秒级加载。

⚠️ 仅供调养参考，不构成医疗诊断。
"""
import os, json, sys, time

# 模型下载走国内镜像（在 import sentence_transformers 之前设置）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

BASE = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(BASE, "..", "data", "books")
INDEX_DIR = os.path.join(BASE, "..", "data", "vector_index")
MODEL_CACHE = os.path.join(BASE, "..", "models", "semantic")
# 模型：优先本地，否则 hf 名
MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_model = None
_vectors = None
_meta = None


def _load_model():
    """加载 embedding 模型（走 hf-mirror 下载，自动复用缓存）。失败返回 None。"""
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE)
        return _model
    except Exception as e:
        print(f"[rag_semantic] 模型加载失败: {e}")
        return None


def _chunks():
    """复用 rag.py 的切块，返回 (book, text) 列表。"""
    sys.path.insert(0, BASE)
    from rag import build_index
    return build_index()[0]


def build_index(force=False):
    """
    构建/加载向量索引。
    返回 (vectors, meta) 或 (None, None) 失败。
    vectors: numpy 数组 [N, D]；meta: [ {书, 片段}, ... ]
    """
    global _vectors, _meta
    if _vectors is not None and not force:
        return _vectors, _meta
    os.makedirs(INDEX_DIR, exist_ok=True)
    vec_path = os.path.join(INDEX_DIR, "vectors.npy")
    meta_path = os.path.join(INDEX_DIR, "meta.json")
    model = _load_model()
    if model is None:
        return None, None
    if os.path.exists(vec_path) and os.path.exists(meta_path) and not force:
        try:
            import numpy as np
            _vectors = np.load(vec_path)
            _meta = json.load(open(meta_path, encoding="utf-8"))
            return _vectors, _meta
        except Exception:
            pass
    # 构建
    chunks = _chunks()
    if not chunks:
        return None, None
    print(f"[rag_semantic] 正在向量化 {len(chunks)} 个文本块（首次较慢）...")
    texts = [c for _, c in chunks]
    t0 = time.time()
    emb = model.encode(texts, show_progress_bar=True, batch_size=64, normalize_embeddings=True)
    _vectors = emb
    _meta = [{"书": b, "片段": c} for b, c in chunks]
    import numpy as np
    np.save(vec_path, _vectors)
    json.dump(_meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[rag_semantic] 索引构建完成，耗时 {time.time()-t0:.1f}s，共 {len(_meta)} 块")
    return _vectors, _meta


def search(query_texts, top_k=3):
    """
    query_texts: list[str] 症状/问题
    返回 [{书, 片段, 得分}] 或 []（未预构建索引/不可用，由调用方降级）。
    """
    vec_path = os.path.join(INDEX_DIR, "vectors.npy")
    meta_path = os.path.join(INDEX_DIR, "meta.json")
    if not (os.path.exists(vec_path) and os.path.exists(meta_path)):
        return []          # 未预构建索引：不现场卡顿，降级到关键词检索
    global _vectors, _meta
    vectors, meta = build_index()
    if vectors is None or not meta:
        return []
    model = _load_model()
    if model is None:
        return []
    import numpy as np
    q = model.encode(list(query_texts), normalize_embeddings=True).mean(axis=0)
    scores = np.dot(vectors, q)          # 余弦相似度（已归一化）
    top = np.argsort(-scores)[:top_k]
    return [{"书": meta[i]["书"], "片段": meta[i]["片段"], "得分": round(float(scores[i]), 3)} for i in top]
