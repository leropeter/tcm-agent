# -*- coding: utf-8 -*-
"""
agent.py — 辨证引擎（核心逻辑）
================================
输入：用户症状描述（如"头痛 怕冷 流清涕"）
输出：可能的证型（按匹配得分排序）+ 辨证依据 + 调养建议 + 配图

⚠️ 仅供中医知识学习与养生参考，不构成医疗诊断，不替代专业医师诊疗。
"""
import re
from .knowledge import TCM_SYNDROMES

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


def _match(symptoms, syndrome):
    """返回 (得分, 命中的症状列表)。"""
    score = 0
    hits = []
    for kw, w in syndrome["symptoms"].items():
        if kw in symptoms:
            score += w
            hits.append(kw)
    return score, hits


def diagnose(symptoms):
    """
    symptoms: list[str] 或 str
    返回排序后的结果列表：
    [{证型, 类别, 得分, 命中, 依据, 建议, 配图}, ...]
    """
    if isinstance(symptoms, str):
        symptoms = parse_symptoms(symptoms)

    results = []
    for s in TCM_SYNDROMES:
        score, hits = _match(symptoms, s)
        if score > 0 and hits:
            results.append({
                "证型": s["id"],
                "类别": s["category"],
                "得分": score,
                "命中": hits,
                "依据": s["evidence"],
                "建议": s["advice"],
                "配图": s["image"],
            })
    # 按得分降序
    results.sort(key=lambda x: x["得分"], reverse=True)
    return results


def pretty_report(symptoms):
    """生成人类可读的纯文本报告（命令行用）。"""
    syms = parse_symptoms(symptoms) if isinstance(symptoms, str) else symptoms
    if not syms:
        return "没有识别到症状，请用逗号/空格分隔输入，例如：头痛 怕冷 流清涕"
    results = diagnose(syms)
    if not results:
        return (
            f"未找到匹配的证型（你输入：{'、'.join(syms)}）。\n"
            "⚠️ 这不代表你没有问题，可能是症状描述不在知识库中。\n"
            "建议补充更多症状，或咨询专业中医师。"
        )
    lines = [f"输入症状：{'、'.join(syms)}", ""]
    top = results[0]
    lines.append(f"🌡️  最可能的证型：{top['证型']}（{top['类别']}，匹配{top['得分']}分）")
    lines.append(f"📋  辨证依据：{top['依据']}")
    lines.append(f"   命中症状：{'、'.join(top['命中'])}")
    for k, v in top["建议"].items():
        lines.append(f"{k}：{v}")
    lines.append(f"🖼️  配图：{top['配图']}")
    # 若存在并列/兼证
    if len(results) > 1:
        lines.append("")
        lines.append("（次要可能证型：" + "、".join(f"{r['证型']}({r['得分']}分)" for r in results[1:]) + "）")
    lines.append("")
    lines.append("⚠️ 以上仅供参考，不构成医疗诊断，不适请就医。")
    return "\n".join(lines)
