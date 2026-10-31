# -*- coding: utf-8 -*-
"""
run_eval.py — 口语评测集跑分
==============================
用法:
    python eval/run_eval.py            # 跑分并打印
    python eval/run_eval.py --md       # 同时写 eval/RESULTS.md

口径（写死在代码里，避免事后解释）:
    有结论   = diagnose() 返回非空，取第 1 名为"结论"
    命中     = 第 1 名出现在期望证型列表里
    过度诊断 = 期望为 null（证据不足）却给出了"较高/中等"把握的证型
    倾向     = 期望为 null 但只给了"较低"把握（不算过度诊断，单独统计）
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agent import diagnose, assess  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CASES_FILE = os.path.join(HERE, "cases_oral.json")


def load_cases():
    with open(CASES_FILE, encoding="utf-8") as f:
        return json.load(f)


def evaluate(data):
    rows = []
    for c in data["cases"]:
        res = diagnose(c["input"])
        top = res[0]["证型"] if res else None
        info = assess(res) if res else {"等级": "无", "说明": "没匹配到任何证型"}
        expect = c.get("expect")
        level = info["等级"]

        if expect is None:
            if top is None:
                verdict = "ok"          # 正确地不给结论
            elif level in ("较高", "中等"):
                verdict = "over"        # 过度诊断
            else:
                verdict = "lean"        # 给了倾向但标了证据不足
        else:
            if top is None:
                verdict = "miss"
            elif top in expect:
                verdict = "ok"
            else:
                verdict = "wrong"

        rows.append({
            "id": c["id"], "group": c.get("group", "core"), "input": c["input"],
            "expect": expect, "got": top, "level": level,
            "second": res[1]["证型"] if len(res) > 1 else None,
            "verdict": verdict, "note": info.get("说明", ""),
        })
    return rows


def summarize(rows):
    def pct(a, b):
        return f"{a}/{b} ({a / b * 100:.0f}%)" if b else "0/0"

    scored = [r for r in rows if r["expect"] is not None]
    vague = [r for r in rows if r["expect"] is None]
    ok = [r for r in scored if r["verdict"] == "ok"]
    high = [r for r in ok if r["level"] in ("较高", "中等")]
    over = [r for r in vague if r["verdict"] == "over"]
    lean = [r for r in vague if r["verdict"] == "lean"]

    return {
        "total": len(rows),
        "scored": len(scored),
        "top1": pct(len(ok), len(scored)),
        "confident": pct(len(high), len(scored)),
        "vague": len(vague),
        "over": pct(len(over), len(vague)),
        "lean": len(lean),
        "miss": len([r for r in scored if r["verdict"] == "miss"]),
        "wrong": len([r for r in scored if r["verdict"] == "wrong"]),
    }


def render(rows, s):
    L = []
    L.append("# 口语评测集跑分结果\n")
    L.append("> 用例集：`eval/cases_oral.json`（100 条，作者手工标注）")
    L.append("> 复跑：`python eval/run_eval.py --md`\n")
    L.append("## 汇总\n")
    L.append("| 指标 | 数值 |")
    L.append("|---|---|")
    L.append(f"| 用例总数 | {s['total']}（有期望值 {s['scored']} / 应无结论 {s['vague']}） |")
    L.append(f"| **Top1 命中率** | **{s['top1']}** |")
    L.append(f"| 其中把握「较高/中等」 | {s['confident']} |")
    L.append(f"| 判错（给了错证型） | {s['wrong']} |")
    L.append(f"| 漏判（没给出结论） | {s['miss']} |")
    L.append(f"| **过度诊断率**（该不给却给了中高把握） | **{s['over']}** |")
    L.append(f"| 只给倾向并声明证据不足 | {s['lean']} |")
    L.append("")
    L.append("口径说明：期望值由作者按八纲+脏腑辨证人工判定，**不是临床金标准**，只用于回归对比。")
    L.append("「倾向」不算过度诊断——系统已显式声明证据不足。\n")

    bad = [r for r in rows if r["verdict"] in ("wrong", "over", "miss")]
    L.append(f"## 未通过明细（{len(bad)} 条）\n")
    L.append("| # | 组 | 输入 | 期望 | 实际 | 把握 |")
    L.append("|---|---|---|---|---|---|")
    for r in bad:
        exp = "（不应给结论）" if r["expect"] is None else " / ".join(r["expect"])
        L.append(f"| {r['id']} | {r['group']} | {r['input']} | {exp} | {r['got'] or '—'} | {r['level']} |")
    L.append("")
    return "\n".join(L)


def main():
    data = load_cases()
    rows = evaluate(data)
    s = summarize(rows)

    print(f"用例 {s['total']} 条：Top1 命中 {s['top1']}，其中中高把握 {s['confident']}")
    print(f"过度诊断 {s['over']}（{s['lean']} 条只给倾向）");
    print(f"判错 {s['wrong']} 条，漏判 {s['miss']} 条")

    if "--md" in sys.argv:
        out = os.path.join(HERE, "RESULTS.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(render(rows, s))
        print(f"已写入 {out}")

    if "--verbose" in sys.argv:
        for r in rows:
            if r["verdict"] != "ok":
                print(f"  [{r['verdict']}] #{r['id']} {r['input']} -> {r['got']} "
                      f"(期望 {r['expect']}, {r['level']})")


if __name__ == "__main__":
    main()
