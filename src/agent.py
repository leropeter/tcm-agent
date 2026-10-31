# -*- coding: utf-8 -*-
"""
agent.py — 辨证引擎（核心逻辑）
================================
输入：用户症状描述（如"头痛 怕冷 流清涕"）
输出：可能的证型（按匹配得分排序）+ 辨证依据 + 调养建议 + 配图

⚠️ 仅供中医知识学习与养生参考，不构成医疗诊断，不替代专业医师诊疗。
"""
import re
from .knowledge import TCM_SYNDROMES, SYNDROME_HINTS
from .normalize import expand_symptoms

# 症状分隔符：中英文逗号、顿号、空格、换行、分号
_DELIM = re.compile(r"[,，、;\s；]+")


def parse_symptoms(text):
    """把用户输入拆成症状关键词列表（去重、去空白，保持原顺序）。"""
    parts = _DELIM.split(text.strip())
    seen, out = set(), []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _match(symptoms, syndrome, trace=None):
    """返回 (得分, 命中的症状列表)。

    trace: {标准词: [用户原话...]}。用于"同源最长匹配优先"：
      用户说"头晕耳鸣"，若该证型同时有"头晕耳鸣"(3) 和"头晕"(2)+"耳鸣"(2)，
      原来会叠加成 7 分，把一个复合词重复计三次。
      这里规定：同一句原话上，被更长关键词覆盖的短关键词不再计分。
    """
    score = 0
    hits = []
    trace = trace or {}
    kw_table = syndrome["symptoms"]
    for kw, w in kw_table.items():
        if kw not in symptoms:
            continue
        if trace:
            superseded = False
            for src in (trace.get(kw) or []):
                for other, _w in kw_table.items():
                    if other == kw or len(other) <= len(kw) or kw not in other:
                        continue
                    if other in symptoms and src in (trace.get(other) or []):
                        superseded = True
                        break
                if superseded:
                    break
            if superseded:
                continue
        score += w
        hits.append(kw)
    return score, hits


def diagnose(symptoms, hints=None):
    """
    symptoms: list[str] 或 str
    hints: dict[str, bool] 可选，问诊线索（因人制宜），如 {"女性":True,"熬夜":True,"中老年":True}
    返回排序后的结果列表：
    [{证型, 类别, 得分, 命中, 依据, 建议, 配图}, ...]
    """
    if isinstance(symptoms, str):
        symptoms = parse_symptoms(symptoms)

    # 口语 → 标准术语 归一化（同义词 + 知识库关键词回捞），并保留"原话←标准词"追溯
    expanded, trace = expand_symptoms(symptoms)

    results = []
    # 儿科证型只在"可能涉及儿童"时参与：经问诊且明确成人（未勾选年轻/儿童）才排除。
    # 无问诊信息（hints=None，如命令行调用）时保持原有全量行为。
    _adult = bool(hints) and not hints.get("儿童") and not hints.get("年轻")
    for s in TCM_SYNDROMES:
        if s["category"].startswith("儿科") and _adult:
            continue
        score, hits = _match(expanded, s, trace)
        # 因人制宜：问诊线索加权
        if hints and hits:
            for clue, on in hints.items():
                if on:
                    score += SYNDROME_HINTS.get(s["id"], {}).get(clue, 0)
        if score > 0 and hits:
            results.append({
                "证型": s["id"],
                "类别": s["category"],
                "得分": score,
                "命中": hits,
                "命中原词": {h: trace.get(h, []) for h in hits},
                "依据": s["evidence"],
                "建议": s["advice"],
                "配图": s["image"],
            })
    # 按得分降序
    results.sort(key=lambda x: x["得分"], reverse=True)
    return results


_COLD = ("寒", "阳虚", "外感", "表证")
_HOT = ("热", "火", "阴虚", "燥")


def _nature(syndrome, category):
    """粗分寒热属性，用于"结论冲突"提示。"""
    s = (syndrome or "") + (category or "")
    if any(k in s for k in _HOT):
        return "热"
    if any(k in s for k in _COLD):
        return "寒"
    return None


def assess(results, trace=None):
    """判断这份结论有多可信 —— 这是"不乱说"的核心闸门。

    返回 {"等级": 较高|中等|较低|无, "领先": int, "信号数": int, "冲突": str|None, "说明": str}

    判据不是只看分数，而是三个一起看：
      score  证据总量
      lead   与第二名的差距（差距小说明几个证型都像 → 不能下结论）
      信号数  用户给了几个不同症状（只有一个"渴"就给证型 = 乱说）
    """
    if not results:
        return {"等级": "无", "领先": 0, "信号数": 0, "冲突": None,
                "说明": "没有足够的证型匹配信号。"}

    top = results[0]
    score = top["得分"]
    second = results[1]["得分"] if len(results) > 1 else 0
    lead = score - second

    # 信号数：命中的关键词来自多少个不同的用户原话。
    # 中文无分隔符时（"晚上睡不好白天没劲"）整句会是一个 token，
    # 若该句较长且命中 ≥2 个关键词，按 2 个信号计（启发式，宁保守不虚高）。
    srcs = set()
    tr = trace or (top.get("命中原词") or {})
    for kw in top.get("命中", []):
        for s in (tr.get(kw) or [kw]):
            srcs.add(s)
    n_signal = len(srcs)
    _long_src = any(len(s) >= 6 for s in srcs)
    if n_signal <= 1 and _long_src and len(top.get("命中", [])) >= 2:
        n_signal = 2

    # 冲突：前两名寒热相反且分差很小
    conflict = None
    if len(results) > 1:
        n1, n2 = _nature(top["证型"], top.get("类别")), _nature(
            results[1]["证型"], results[1].get("类别"))
        if n1 and n2 and n1 != n2 and lead <= 2:
            conflict = (f"「{top['证型']}」（偏{n1}）与「{results[1]['证型']}」（偏{n2}）"
                        f"方向相反且分数接近（{score} vs {results[1]['得分']}），需鉴别后再调养。")

    # 三档：分数 + 领先幅度 + 信号数，三个一起看
    # 门槛说明：allow lead=2 是因为"风寒束表 vs 风寒束肺"这类易混对天然只差 2 分，
    #          要求 lead>=3 会把大量典型输入压成"中等"，反而失真。
    if score >= 8 and lead >= 2 and n_signal >= 2:
        level, note = "较高", f"命中 {n_signal} 个独立症状、领先第二名 {lead} 分。"
    elif score >= 6 and lead >= 2:
        level, note = "中等", f"方向较清楚（{score} 分，领先 {lead} 分）。"
    elif score >= 4 and lead >= 1:
        level, note = "较低", f"只有 {score} 分、领先 {lead} 分，只能算倾向。"
    elif n_signal <= 1:
        level, note = "较低", "只有 1 个症状线索，不足以确定证型。"
    else:
        level, note = "较低", f"证据分散（{score} 分，领先 {lead} 分），多个证型都像。"
    if n_signal <= 1 and level == "较高":
        level, note = "中等", note + "（但仅 1 个症状线索，暂不给最高把握）"

    return {"等级": level, "领先": lead, "信号数": n_signal,
            "冲突": conflict, "说明": note}


def pretty_report(symptoms, hints=None):
    """生成人类可读的纯文本报告（命令行用）。"""
    syms = parse_symptoms(symptoms) if isinstance(symptoms, str) else symptoms
    if not syms:
        return "没有识别到症状，请用逗号/空格分隔输入，例如：头痛 怕冷 流清涕"
    results = diagnose(syms, hints)
    if not results:
        # 没有证型也不留死路：走分诊 → 症状域通用调理 + 鉴别追问
        try:
            from .triage import triage, render_triage
            _t = triage("、".join(syms))
            return (f"输入：{'、'.join(syms)}\n\n" + render_triage(_t)
                    + "\n\n⚠️ 以上仅供参考，不构成医疗诊断，不适请就医。")
        except Exception:
            return (
                f"未找到匹配的证型（你输入：{'、'.join(syms)}）。\n"
                "⚠️ 这不代表你没有问题，可能是症状描述不在知识库中。\n"
                "建议补充更多症状，或咨询专业中医师。"
            )
    lines = [f"输入症状：{'、'.join(syms)}", ""]
    top = results[0]
    conf = assess(results)
    _head = {"较高": "最可能的证型", "中等": "可能是", "较低": "证据不足，暂偏向"}.get(
        conf["等级"], "可能是")
    _mark = {"较高": "🌡️ ", "中等": "🌤️ ", "较低": "❔ "}.get(conf["等级"], "")
    lines.append(
        f"{_mark} {_head}：{top['证型']}（{top['类别']}，匹配{top['得分']}分 · "
        f"把握{conf['等级']}｜{conf['说明']}）"
    )
    if conf["冲突"]:
        lines.append(f"⚠️  鉴别提示：{conf['冲突']}")
    if conf["等级"] == "较低":
        lines.append("   把握不足时，请别把它当结论 —— 补充更多症状后重判更可靠。")
    lines.append(f"📋  辨证依据：{top['依据']}")
    # 命中症状 + 追溯（哪句原话被采信），保证可解释
    _trace = top.get("命中原词") or {}
    _parts = []
    for h in top["命中"]:
        _src = [x for x in (_trace.get(h) or []) if x != h]
        _parts.append(f"{h}（你说:{'/'.join(_src)}）" if _src else h)
    lines.append(f"   命中症状：{'、'.join(_parts)}")
    for k, v in top["建议"].items():
        lines.append(f"{k}：{v}")
    lines.append(f"🖼️  配图：{top['配图']}")
    # 若存在并列/兼证
    if len(results) > 1:
        lines.append("")
        lines.append("（次要可能证型：" + "、".join(f"{r['证型']}({r['得分']}分)" for r in results[1:4]) + "）")
    # 差异化调养方案（因时/因人/因线索/对症/兼证/禁忌/就医）
    try:
        from .advice import build_plan, render_text
        _plan = build_plan(results, hints, syms)
        _warn = _plan.pop("就医", [])
        for _w in reversed(_warn):        # 红旗提到最前，安全优先
            lines.insert(2, f"🚨 {_w}")
        _extra = render_text(_plan)
        if _extra:
            lines.append("")
            lines.append("──────── 按你的具体情况调整 ────────")
            lines.append(_extra)
    except Exception:
        pass
    # 置信度不足时，告诉用户"补哪一句就能定下来"（复用关键词追问表）
    if conf["等级"] in ("较低", "中等"):
        try:
            from .normalize import expand_symptoms as _ex2
            from .probe import probes_for as _probes_for
            _e2, _ = _ex2(syms)
            _kws = _probes_for(syms, _e2, max_kw=2)
            if _kws:
                lines.append("")
                lines.append("🔍 想更准？补充这几个就能定下来：")
                for _k in _kws:
                    for _q in _k["追问"][:2]:
                        lines.append(f"   · {_q['问']}（{'／'.join(_q['选项'].keys())}）")
        except Exception:
            pass
    # 相似医案（真实临床记录，比古籍片段更贴近"人话"）
    try:
        from .cases import search as _case_search, render as _case_render
        _cs = _case_search(syms, 2)
        if _cs:
            lines.append("")
            lines.append(_case_render(_cs))
    except Exception:
        pass
    # 典籍参考（RAG，data/books 缺失时优雅降级）
    refs = []
    try:
        from .rag import enrich
        refs = enrich(syms, 2)
    except Exception:
        refs = []
    if refs:
        lines.append("")
        lines.append("📚 典籍参考：")
        for r in refs:
            lines.append(f"  〔{r['书']}〕{r['片段']}")
    lines.append("")
    lines.append("⚠️ 以上仅供参考，不构成医疗诊断，不适请就医。")
    return "\n".join(lines)
