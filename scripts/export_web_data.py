# -*- coding: utf-8 -*-
"""export_web_data.py — 把 Python 侧的知识库导出成静态站用的 JSON。

用法: python scripts/export_web_data.py
输出: docs/data.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from src.knowledge import TCM_SYNDROMES, SYNDROME_HINTS  # noqa: E402
from src.normalize import SYNONYMS, ALL_KEYWORDS  # noqa: E402
import src.formulas as F  # noqa: E402
import src.acupoints as A  # noqa: E402
import src.recipes as R  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

data = {
    "version": "0.3.0",
    "generated_by": "scripts/export_web_data.py",
    "syndromes": [
        {
            "id": s["id"],
            "category": s["category"],
            "symptoms": s["symptoms"],
            "evidence": s["evidence"],
            "advice": s["advice"],
            "image": s["image"],
        }
        for s in TCM_SYNDROMES
    ],
    "hints": SYNDROME_HINTS,
    "synonyms": SYNONYMS,
    "keywords": sorted(ALL_KEYWORDS),
    "formulas": F.FORMULAS,
    "acupoints": A.ACUPOINTS,
    "recipes": dict(R.RECIPES),
}

out = os.path.join(ROOT, "docs", "data.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

size = os.path.getsize(out) / 1024
print(f"写入 {out}  {size:.1f} KB")
print(f"证型 {len(data['syndromes'])} / 同义词 {len(data['synonyms'])} / "
      f"关键词 {len(data['keywords'])} / 方剂 {len(data['formulas'])} / "
      f"穴位 {len(data['acupoints'])} / 食疗 {len(data['recipes'])}")
