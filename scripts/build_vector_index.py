# -*- coding: utf-8 -*-
"""
build_vector_index.py — 预构建语义检索索引
用法: python scripts/build_vector_index.py
（需先 pip install sentence-transformers）
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from src.rag_semantic import build_index

if __name__ == "__main__":
    print("正在构建语义检索索引（首次较慢，之后秒级加载）...")
    vec, meta = build_index(force=True)
    if meta is None:
        print("❌ 构建失败（可能未安装 sentence-transformers，或模型下载失败）")
        print("   请先: pip install sentence-transformers")
        sys.exit(1)
    print(f"✅ 索引构建完成，共 {len(meta)} 个文本块")
    print("   Web 界面的「典籍参考」将使用语义检索")
