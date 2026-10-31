# -*- coding: utf-8 -*-
"""
cases.py — 医案库检索（真实临床案例）
=====================================
资料来源：data/Train_TCM_Data_v1.json（200 例）+ data/Validation_TCM_Data_v1.json（50 例）
        原始出处：TCMEval-SDT 数据集（对应 Nature 论文 s41597-025-04772-9 配套数据）

每例含：完整病史与舌脉、病机、证型、**临证体会（Explanatory Summary）**。
其中"临证体会"是原医师的辨证思路白话说明，最适合给普通人看——
这正是原来项目里最缺、也最有用的参考：别人出现类似症状时，医生是怎么想的。

用法：
    from src.cases import search
    search(["失眠", "多梦"])   # → [{"id","主诉","病机","证型","体会","匹配数",...}]
"""
import json
import os
import re

from .normalize import ALL_KEYWORDS, expand_symptoms

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(_HERE, "..", "data")
_FILES = ["Train_TCM_Data_v1.json", "Validation_TCM_Data_v1.json"]

_CASES = None          # 惰性加载
_CASE_SYMS = None      # 预计算的每例命中症状集合

# 从"临床数据"里剥掉年代、性别年龄等硬信息，只留主诉与诊查
_STRIP = re.compile(r"初诊[:：]\s*\d{4}年?|诊查[:：]|主诉及病史[:：]")


def _load():
    global _CASES, _CASE_SYMS
    if _CASES is not None:
        return
    cases = []
    for fn in _FILES:
        p = os.path.join(_DATA, fn)
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            continue
        for x in raw:
            clinical = (x.get("Clinical Data") or "").strip()
            info = (x.get("Clinical Information") or "").strip()
            # 症状扫描文本：Clinical Information 最规整，缺失时退回 Clinical Data
            scan = info if info else clinical
            cases.append({
                "id": x.get("Medical Record ID", ""),
                "原文": clinical,
                "症状串": info,
                "病机": (x.get("TCM Pathogenesis") or "").replace(";", "、"),
                "证型": (x.get("TCM Syndrome") or "").replace(";", "、"),
                "辨证": (x.get("Syndrome Differentiation") or ""),
                "体会": (x.get("Explanatory Summary") or ""),
            })
    _CASES = cases

    # 预计算：每例命中了哪些知识库症状词（避免每次检索都全量扫描）
    syms = []
    for c in _CASES:
        text = c["症状串"] + "；" + c["原文"]
        syms.append({kw for kw in ALL_KEYWORDS if kw in text})
    _CASE_SYMS = syms


def count():
    _load()
    return len(_CASES)


def _brief(text, n=110):
    """截断成一句可读主诉，去掉年份等噪声。"""
    t = _STRIP.sub(" ", text or "")
    t = re.sub(r"\s+", " ", t).strip(" ，。;；")
    return (t[:n] + "…") if len(t) > n else t


def search(symptoms, top=3, min_hit=1):
    """按症状检索相似医案。

    symptoms: list[str] 或 str（用户输入）
    返回按匹配度排序的医案列表，每项含 匹配数/共几个症状/命中词。
    只返回真实命中的案例，不做"凑相似"——匹配不到就是空。
    """
    _load()
    if isinstance(symptoms, str):
        from .agent import parse_symptoms
        symptoms = parse_symptoms(symptoms)
    expanded, _ = expand_symptoms(symptoms)
    if not expanded or not _CASES:
        return []

    scored = []
    for i, cs in enumerate(_CASE_SYMS):
        hit = expanded & cs
        if len(hit) < min_hit:
            continue
        # 覆盖度：命中数 / 用户症状展开数；再按命中数微调，避免长案例占优
        cover = len(hit) / max(len(expanded), 1)
        scored.append((round(cover, 3), len(hit), i, sorted(hit)))

    # 覆盖度高优先，其次命中数多
    scored.sort(key=lambda x: (-x[0], -x[1]))

    out = []
    for cover, n_hit, i, hit in scored[:top]:
        c = _CASES[i]
        out.append({
            "id": c["id"],
            "主诉": _brief(c["原文"]),
            "症状串": c["症状串"].replace(";", "、") if c["症状串"] else "",
            "病机": c["病机"],
            "证型": c["证型"],
            "体会": c["体会"],
            "匹配数": n_hit,
            "覆盖度": cover,
            "命中词": hit,
        })
    return out


def render(items, max_body=260):
    """纯文本渲染（命令行用）。"""
    if not items:
        return ""
    L = ["📂 相似医案（真实临床记录，来自 TCMEval-SDT 数据集）"]
    for k, c in enumerate(items, 1):
        L.append("")
        L.append(f"{k}. 【{c['id']}】匹配 {c['匹配数']} 个症状"
                 f"（{'、'.join(c['命中词'][:6])}）")
        if c["症状串"]:
            L.append(f"   病历要点：{c['症状串']}")
        L.append(f"   病机：{c['病机']}　证型：{c['证型']}")
        body = (c["体会"] or "").strip()
        if body:
            if len(body) > max_body:
                body = body[:max_body] + "…"
            L.append(f"   医生是怎么想的：{body}")
    L.append("")
    L.append("   ※ 医案是「别人」的经历，用于理解思路，不能照搬到自己身上。")
    return "\n".join(L)
