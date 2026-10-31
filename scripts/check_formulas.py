# -*- coding: utf-8 -*-
"""方剂库自检：证型 ID 是否都存在、覆盖了多少证型、字段是否齐全"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.formulas import FORMULAS, count, covered_syndromes, for_syndrome, DISCLAIMER
from src.knowledge import TCM_SYNDROMES

ids = {s["id"] for s in TCM_SYNDROMES}
cov = covered_syndromes()

print(f"方剂数: {count()}")
print(f"覆盖证型: {len(cov)}/{len(ids)}")
print(f"未覆盖证型: {sorted(ids - cov)}")
print(f"不存在的证型（写错了）: {sorted(cov - ids)}")
print(f"缺字段: {[f['名'] for f in FORMULAS if not all(f.get(k) for k in ('名','出处','组成','功用','主治','证型'))]}")
print(f"含毒性提示的方: {[f['名'] for f in FORMULAS if '有毒' in f.get('注意','') or '禁用' in f.get('注意','')]}")
print(f"\n脾阳虚样例 → {[f['名'] for f in for_syndrome('肾阳虚')]}")
print(f"未知证型 → {for_syndrome('不存在的证型')}")
print(f"\n免责声明: {DISCLAIMER}")
