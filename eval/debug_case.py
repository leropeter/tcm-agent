# -*- coding: utf-8 -*-
"""看失败用例到底归一化成了什么，用来定位是哪一层丢的。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.agent import parse_symptoms, diagnose
from src.normalize import expand_symptoms

data = json.load(open(os.path.join(HERE, "cases_oral.json"), encoding="utf-8"))
ids = [int(x) for x in sys.argv[1:]] or [1, 2, 14, 37, 45, 47, 50, 59, 62, 67, 73, 78]

for c in data["cases"]:
    if c["id"] not in ids:
        continue
    toks = parse_symptoms(c["input"])
    expanded, trace = expand_symptoms(toks)
    res = diagnose(c["input"])
    print(f"#{c['id']} {c['input']}")
    print(f"   切词: {toks}")
    print(f"   归一: {expanded}")
    top = [(r['证型'], r['得分'], r['命中']) for r in res[:3]]
    print(f"   Top3: {top}")
    print(f"   期望: {c['expect']}")
    print()
