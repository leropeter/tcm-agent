# -*- coding: utf-8 -*-
"""parse_fangjixue.py — 从《方剂学》教材 PDF 提取方剂的组成/用法/功用/主治。

只提取事实性字段（组成、用法、功用、主治），不搬运教材的方解、方论等论述性内容。
输出 docs/formula_textbook.json。

用法: python scripts/parse_fangjixue.py
"""
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

PDF = os.path.join(ROOT, "data", "fangjixue.pdf")
OUT = os.path.join(ROOT, "docs", "formula_textbook.json")

FIELDS = ["组成", "用法", "功用", "主治"]
FIELD_RE = re.compile(r"【\s*(" + "|".join(FIELDS) + r")\s*】")
ANY_FIELD = re.compile(r"【\s*[^】]{1,8}?\s*】")


def load_text():
    from pypdf import PdfReader
    r = PdfReader(PDF)
    parts = []
    for p in r.pages:
        t = p.extract_text() or ""
        parts.append(t)
    text = "\n".join(parts)
    # 保留换行：方名标题是独立一行，合并断行会把锚点破坏掉
    return text


def extract_for(name, text):
    """锚点：方名 + 紧随的《书名》 + 【组成】。"""
    pat = re.compile(
        r"\n\s*" + re.escape(name) + r"\s*[（(]?[^【《\n]{0,6}《([^》]{2,20})》[^【]{0,40}【\s*组成\s*】")
    for m in pat.finditer(text):
        seg = text[m.start(): m.start() + 1600]
        out = {}
        for fm in FIELD_RE.finditer(seg):
            field = fm.group(1)
            if field in out:
                continue
            start = fm.end()
            nm = ANY_FIELD.search(seg, start)
            end = nm.start() if nm else min(len(seg), start + 500)
            val = re.sub(r"\s+", "", seg[start:end]).strip("：:;；")
            if len(val) > 2:
                out[field] = val

        if out.get("组成") and out.get("功用"):
            # 功用偶尔会把主治串进来（跨页丢字段），截到第一个句号
            if "。" in out["功用"]:
                out["功用"] = out["功用"].split("。")[0] + "。"
            out["出处"] = m.group(1)
            return out
    return None


def main():
    if not os.path.exists(PDF):
        print("PDF 不存在:", PDF)
        return 1

    text = load_text()
    print(f"PDF 文本 {len(text)} 字")

    result = {}
    ok = 0
    for f in FORMULAS:
        name = f["名"]
        got = extract_for(name, text)
        if got:
            result[name] = got
            ok += 1

    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(OUT) / 1024
    print(f"写入 {OUT}  {size:.1f} KB")
    print(f"匹配 {ok}/{len(FORMULAS)} 首")
    for k, v in list(result.items())[:3]:
        print(f"\n== {k} · {v.get('出处')}")
        for f in FIELDS:
            if f in v:
                print(f"   【{f}】{v[f][:90]}")


if __name__ == "__main__":
    sys.exit(main())
