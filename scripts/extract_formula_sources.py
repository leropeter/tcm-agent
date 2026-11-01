# -*- coding: utf-8 -*-
"""extract_formula_sources.py — 从 21 本典籍里抽取每个方剂的原文出处段落。

输出 docs/formula_sources_v2.json：
    { "桂枝汤": [ {"book": "伤寒论.md", "text": "...", "score": 3}, ... ], ... }

只保留"像方剂条文"的段落：命中方名 + 附近有煎/煮/服/丸/散/剂等字。
不做任何改写，原文照录——来源必须可查。
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from src.formulas import FORMULAS  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BOOKS = sorted(glob.glob(os.path.join(ROOT, "data", "books", "*.md")))

PRIORITY = ["伤寒论", "金匮要略", "千金要方", "千金翼方", "肘后备急方",
            "脾胃论", "本草纲目", "黄帝内经", "神农本草经"]

EXCLUDE_BOOKS = ["邹孟城", "自我调养", "中医养生学", "中医伤科按摩学", "动画图", "中医眼科备读"]

KEY_HINT = re.compile(r"[煎煮服丸散汤剂饮送下]")
DOSE = re.compile(r"[钱两升合枚铢斤克分盅撮把]")
MAKE = re.compile(r"煎|煮|为末|炼蜜|研末|杵|炮|咀")

OUT_NAME = "formula_sources_v2.json"


def clean(t):
    return re.sub(r"\s+", " ", t).strip()


def book_rank(name):
    for i, key in enumerate(PRIORITY):
        if key in name:
            return i
    return len(PRIORITY)


def load_books():
    out = []
    for p in BOOKS:
        base = os.path.basename(p)
        if any(k in base for k in EXCLUDE_BOOKS):
            continue
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        out.append((base, text))
    out.sort(key=lambda x: book_rank(x[0]))
    return out


def main():
    books = load_books()
    print(f"典籍 {len(books)} 本参与检索（原始 {len(BOOKS)} 本）")
    result = {}

    for f in FORMULAS:
        name = f["名"]
        hits = []
        for bname, text in books:
            positions = [m.start() for m in re.finditer(re.escape(name + "方"), text)]
            if not positions:
                positions = [m.start() for m in re.finditer(re.escape(name), text)]

            for pos in positions:
                if pos > 0 and "\u4e00" <= text[pos - 1] <= "\u9fff":
                    continue
                start = max(0, pos - 10)
                dot = text.rfind("。", max(0, start - 60), start)
                if dot > 0:
                    start = dot + 1
                end = min(len(text), pos + 460)
                seg = clean(text[start:end])
                if len(seg) < 60:
                    continue
                idx = seg.find(name)
                if idx < 0 or idx > 40:
                    continue
                if not MAKE.search(seg):
                    continue
                if len(DOSE.findall(seg)) < 3:
                    continue
                hints = len(KEY_HINT.findall(seg))
                if hints < 3:
                    continue
                bonus = 20 if book_rank(bname) < 6 else 0
                hits.append({
                    "book": bname,
                    "text": seg,
                    "score": hints + bonus + (5 if "主之" in seg else 0),
                })

        best = {}
        for h in hits:
            if h["book"] not in best or h["score"] > best[h["book"]]["score"]:
                best[h["book"]] = h
        picked = sorted(best.values(), key=lambda x: -x["score"])[:2]
        for p in picked:
            p.pop("score", None)
            p["text"] = p["text"][:380]
        result[name] = picked

    out = os.path.join(ROOT, "docs", OUT_NAME)
    with open(out, "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(out) / 1024
    covered = len([k for k, v in result.items() if v])
    print(f"写入 {out}  {size:.1f} KB")
    print(f"方剂 {len(FORMULAS)} 首，找到原文的 {covered} 首")
    for k, v in list(result.items())[:5]:
        print(f"  {k}: {len(v)} 条 · {v[0]['book'] if v else '无'}")


if __name__ == "__main__":
    main()
