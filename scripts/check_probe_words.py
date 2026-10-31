# -*- coding: utf-8 -*-
"""检查 triage 与 probe 的追问选项词，是否真能驱动引擎（症状词 or 问诊线索）"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.triage import DOMAINS
from src.probe import PROBES, all_option_words
from src.normalize import ALL_KEYWORDS
from src.knowledge import SYNDROME_HINTS

clue_keys = {k for d in SYNDROME_HINTS.values() for k in d}


def dead_of(pairs):
    return [(src, w) for src, w in pairs if w not in ALL_KEYWORDS and w not in clue_keys]


triage_pairs = [(d["名"] + "/" + lb, w) for d in DOMAINS for q in d["追问"]
                for lb, ws in q["选项"].items() for w in ws]
probe_pairs = [(kw + "/" + q["问"][:10], w) for kw, qs in PROBES.items()
               for q in qs for ws in q["选项"].values() for w in ws]

print(f"症状词库 {len(ALL_KEYWORDS)}；线索键 {len(clue_keys)}")
print(f"triage 选项词 {len(triage_pairs)} 个 → 死词 {len(dead_of(triage_pairs))}")
for x in dead_of(triage_pairs):
    print("   ", x)
print(f"probe  选项词 {len(probe_pairs)} 个 → 死词 {len(dead_of(probe_pairs))}")
for x in dead_of(probe_pairs):
    print("   ", x)
print(f"probe 覆盖关键词 {len(PROBES)} 个，追问问题共 "
      f"{sum(len(v) for v in PROBES.values())} 个")
