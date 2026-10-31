# -*- coding: utf-8 -*-
"""cases.py（医案库）+ probe.py（关键词追问）自检"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.cases import count, search, render
from src.probe import PROBES, probes_for, all_option_words
from src.normalize import ALL_KEYWORDS
from src.knowledge import SYNDROME_HINTS

PASS = FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {extra}")


clue_keys = {k for d in SYNDROME_HINTS.values() for k in d}

print("== 医案库 ==")
check("医案总数 250", count() == 250, count())
items = search(["头晕", "耳鸣", "腰酸"], top=2)
check("能检索到医案", len(items) == 2, len(items))
check("按覆盖度排序（首条覆盖度最高）",
      len(items) > 1 and items[0]["覆盖度"] >= items[1]["覆盖度"],
      [i["覆盖度"] for i in items])
check("返回字段齐全", all(k in items[0] for k in ("id", "主诉", "病机", "证型", "体会", "匹配数")))
check("医案有临证体会", bool(items[0]["体会"]))
check("命中词非空", bool(items[0]["命中词"]))
check("无匹配返回空（不硬凑）", search(["肝风内动xyz不存在"]) == [])
check("空输入返回空", search([]) == [])
check("render 非空", len(render(items, 100)) > 100)
check("render 带免责说明", "不能照搬" in render(items))

# 不同查询应给出不同医案
a = search(["失眠", "多梦"], top=1)
b = search(["咳嗽", "痰黄"], top=1)
check("不同症状检索到不同医案", bool(a) and bool(b) and a[0]["id"] != b[0]["id"],
      (a[0]["id"] if a else None, b[0]["id"] if b else None))

print("== 关键词追问表 ==")
check("覆盖 23 个关键词", len(PROBES) == 23, len(PROBES))
check("每个关键词至少 1 问", all(len(v) >= 1 for v in PROBES.values()))
check("每问至少 2 个选项", all(len(q["选项"]) >= 2 for v in PROBES.values() for q in v))
dead = [w for w in all_option_words() if w not in ALL_KEYWORDS and w not in clue_keys]
check("选项词零死词", not dead, str(dead[:5]))
check("选项词数 > 300", len(all_option_words()) > 300, len(all_option_words()))

print("== 追问命中逻辑（跟着关键词走）==")
kp = probes_for(["头晕"])
check("说「头晕」→ 命中头晕追问", bool(kp) and kp[0]["关键词"] == "头晕", kp and kp[0]["关键词"])
kp = probes_for(["头痛"])
check("说「头痛」→ 命中头痛追问", bool(kp) and kp[0]["关键词"] == "头痛")
kp = probes_for(["有点晕"], expanded={"头晕"})
check("同义词展开也能命中", bool(kp))
kp = probes_for(["吃不下饭"])
check("无对应关键词返回空（不硬凑）", kp == [], kp)
kp = probes_for(["头晕", "乏力", "失眠"], max_kw=2)
check("max_kw 限制生效", len(kp) == 2, len(kp))

print("== 方剂库 ==")
from src.formulas import (FORMULAS, count as fcount, for_syndrome,
                          covered_syndromes, DISCLAIMER)
from src.knowledge import TCM_SYNDROMES as _SYN
_ids = {s["id"] for s in _SYN}
check("方剂数 61", fcount() == 61, fcount())
check("41 证型全覆盖", covered_syndromes() == _ids, sorted(_ids - covered_syndromes()))
check("无写错的证型 ID", not (covered_syndromes() - _ids), sorted(covered_syndromes() - _ids))
check("字段齐全",
      all(all(f.get(k) for k in ("名", "出处", "组成", "功用", "主治", "证型")) for f in FORMULAS))
check("组成不含剂量（无克/g）",
      all("克" not in f["组成"] for f in FORMULAS)
      and all(not any(ch.isdigit() for ch in f["组成"]) for f in FORMULAS),
      [f["名"] for f in FORMULAS if any(ch.isdigit() for ch in f["组成"])][:3])
check("含毒/禁忌药者必带注意",
      all(f.get("注意") for f in FORMULAS
          if any(k in f["组成"] for k in ("附子", "朱砂", "细辛", "水蛭"))),
      [f["名"] for f in FORMULAS if any(k in f["组成"] for k in ("附子", "朱砂")) and not f.get("注意")])
check("免责声明强调不给剂量", "不给剂量" in DISCLAIMER)
check("未知证型返回空", for_syndrome("不存在") == [])
check("每个证型至少 1 方", all(for_syndrome(s) for s in _ids),
      [s for s in _ids if not for_syndrome(s)])

print(f"\n总计: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
