# -*- coding: utf-8 -*-
"""
demo.py — 命令行演示
用法：
    python examples/demo.py
    python examples/demo.py --symptom "头痛 怕冷 流清涕"
"""
import argparse, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.agent import pretty_report, diagnose

DEFAULT = "头痛 怕冷 流清涕 无汗"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symptom", default=DEFAULT, help="症状描述，用逗号/空格分隔")
    ap.add_argument("--json", action="store_true", help="以JSON输出")
    args = ap.parse_args()

    if args.json:
        import json
        print(json.dumps(diagnose(args.symptom), ensure_ascii=False, indent=2))
    else:
        print(pretty_report(args.symptom))
