# -*- coding: utf-8 -*-
"""列出全部证型 ID（写方剂库/映射表时对照用）: python scripts/list_ids.py"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from src.knowledge import TCM_SYNDROMES

for i, s in enumerate(TCM_SYNDROMES, 1):
    print(f"{i:2} | {s['id']} | {s['category']} | 症状{len(s['symptoms'])}个")
print(f"\n合计 {len(TCM_SYNDROMES)} 个证型")
