# -*- coding: utf-8 -*-
"""
app.py — TCM Agent Web 界面（Streamlit）
========================================
两种模式：
  🏠 日常养生  输入"有点失眠 / 舌头有齿痕 / 手脚凉" → 生活化调理建议
  🌡️ 辨证论治  输入"心烦 口舌生疮" → 中医证型 + 调养 + 方剂 + 医案 + 典籍

启动:  streamlit run app.py
"""
import streamlit as st
from src.agent import diagnose, parse_symptoms, assess
from src.wellness import daily_advice
from src import acupoints, recipes, constitution, formulas
from src.advice import build_plan

st.set_page_config(
    page_title="中医药辨证调养助手",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================ 样式
st.markdown("""
<style>
  .stApp { background: linear-gradient(180deg, #faf8f3 0%, #f3efe4 100%); }
  #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] { visibility: hidden; height: 0; }
  .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 900px; }

  /* ---- 品牌头 ---- */
  .brand { text-align: center; margin: 0 0 1.4rem; }
  .brand h1 { font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
              font-size: 2.05rem; color: #1f5c3a; letter-spacing: .1em;
              margin: 0; font-weight: 700; }
  .brand .sub { color: #7d7a6b; font-size: .9rem; margin-top: .45rem; letter-spacing: .02em; }
  .brand .rule { width: 58px; height: 3px; background: #b08d3f; margin: .85rem auto 0;
                 border-radius: 2px; opacity: .85; }

  /* ---- 证型卡 ---- */
  .syn-card { border-radius: 16px; padding: 1.1rem 1.3rem; margin: .5rem 0 1rem;
              background: #fff; border: 1px solid rgba(31,92,58,.10);
              box-shadow: 0 3px 14px rgba(31,92,58,.07); }
  .syn-name { font-family: "Songti SC", "Noto Serif SC", serif;
              font-size: 1.5rem; font-weight: 700; line-height: 1.35; }
  .syn-meta { color: #6b6b5e; font-size: .86rem; margin-top: .3rem; }
  .badge { display: inline-block; padding: .16rem .62rem; border-radius: 999px;
           font-size: .74rem; font-weight: 700; letter-spacing: .02em; }
  .chip { display: inline-block; background: #edf3ee; color: #2c4a38;
          border-radius: 999px; padding: .15rem .58rem; font-size: .78rem;
          margin: .16rem .28rem .16rem 0; }
  .bar-out { height: 6px; background: #eceae1; border-radius: 999px; margin: .55rem 0 .2rem;
             overflow: hidden; }
  .bar-in { height: 100%; border-radius: 999px; }

  /* ---- 建议块 ---- */
  .adv { background: #fff; border-radius: 12px; padding: .78rem 1rem; margin: .45rem 0;
         border-left: 4px solid #b08d3f; box-shadow: 0 1px 6px rgba(0,0,0,.035);
         font-size: .93rem; line-height: 1.65; }
  .adv .k { color: #1f5c3a; font-weight: 700; margin-right: .35rem; }
  .sec { font-family: "Songti SC", "Noto Serif SC", serif; font-size: 1.08rem;
         color: #1f5c3a; font-weight: 700; margin: 1.3rem 0 .5rem;
         padding-left: .55rem; border-left: 4px solid #1f5c3a; }

  /* ---- 提示 ---- */
  .warnbox { background: #fdf3f2; border-left: 4px solid #b3261e; border-radius: 10px;
             padding: .7rem .95rem; font-size: .88rem; color: #8a1f18; margin: .5rem 0; }
  .okbox { background: #eef6f0; border-left: 4px solid #2e7d5b; border-radius: 10px;
           padding: .7rem .95rem; font-size: .88rem; color: #245c42; margin: .5rem 0; }
  .hintbox { background: #fbf7ec; border: 1px dashed #d9c9a3; border-radius: 10px;
             padding: .7rem .95rem; font-size: .88rem; color: #6d5c33; margin: .5rem 0; }

  /* ---- 方剂卡 ---- */
  .fml { background: #fffdf7; border: 1px solid #e8dfc6; border-radius: 12px;
         padding: .85rem 1rem; margin: .5rem 0; }
  .fml .n { font-family: "Songti SC", serif; font-size: 1.06rem; font-weight: 700; color: #8a6d1f; }
  .fml .s { color: #7d7a6b; font-size: .8rem; margin-left: .4rem; }
  .fml .row { font-size: .9rem; line-height: 1.6; color: #3c3c36; margin-top: .3rem; }

  /* ---- 侧边栏 ---- */
  [data-testid="stSidebar"] { background: #f5f1e6; border-right: 1px solid #e7e1d1; }
  [data-testid="stSidebar"] .side-h { font-family: "Songti SC", serif;
        font-size: 1.02rem; color: #1f5c3a; font-weight: 700; margin: .2rem 0 .6rem; }
  [data-testid="stSidebar"] .side-note { color: #857f6c; font-size: .78rem; line-height: 1.55; }

  /* ---- 控件 ---- */
  .stButton > button { border-radius: 10px; font-weight: 600; }
  .stButton > button[kind="primary"] { background: #1f5c3a; border-color: #1f5c3a; }
  .stTabs [data-baseweb="tab-list"] { gap: .3rem; }
  .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: .92rem; }
  div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #e8e3d5; }
</style>
""", unsafe_allow_html=True)

BOLD = "#1f5c3a"


def _html(s):
    st.markdown(s, unsafe_allow_html=True)


# ============================================================ 侧边栏：问诊
with st.sidebar:
    _html('<div class="side-h">👤 基本情况（选填，但会明显影响判断）</div>')
    gender = st.radio("性别", ["男", "女", "不便透露"], horizontal=True, key="q_gender")
    age_group = st.radio("年龄段", ["25岁以下", "26-45岁", "46岁以上", "不便透露"],
                         horizontal=True, key="q_age")
    recent = st.multiselect(
        "近期情况（可多选）",
        options=[
            "熬夜", "睡眠不规律", "压力大/焦虑", "情绪不好/生气", "思虑多",
            "受凉/吹风", "换季", "吃辛辣/烧烤/火锅", "吃生冷/冰饮", "饮食不规律",
            "久坐少动", "久用眼", "劳累", "经期/产后", "月经量多", "久咳", "怀孕/哺乳",
        ],
        default=[], key="q_recent",
        placeholder="点这里多选（可以留空）",
    )
    st.markdown("---")
    _html('<div class="side-note">本工具基于中医证型规则库 + 250 例真实医案 + 21 部典籍，'
          '用于学习与养生参考。<b>不构成诊断，不替代医师。</b></div>')


def _build_hints(gender, age_group, recent):
    hints = {}
    if gender == "女":
        hints["女性"] = True
    elif gender == "男":
        hints["男性"] = True
    if age_group == "25岁以下":
        hints["年轻"] = True
    elif age_group == "46岁以上":
        hints["中老年"] = True
    clue_map = {
        "熬夜": "熬夜", "睡眠不规律": "熬夜", "压力大/焦虑": "压力大", "情绪不好/生气": "情绪不好",
        "思虑多": "思虑多", "受凉/吹风": "受凉", "换季": "换季", "吃辛辣/烧烤/火锅": "吃辛辣",
        "吃生冷/冰饮": "吃生冷", "饮食不规律": "饮食不节", "久坐少动": "久坐", "久用眼": "久视",
        "劳累": "劳累", "经期/产后": "经期", "月经量多": "月经量多", "久咳": "久咳",
        "怀孕/哺乳": "孕期",
    }
    for opt in recent:
        if opt in clue_map:
            hints[clue_map[opt]] = True
    return hints


patient_hints = _build_hints(gender, age_group, recent)


# ============================================================ 渲染函数
def _render_diagnosis(results, hints, all_symptoms, allow_probe=True):
    """辨证结果渲染（主流程与追问复判共用）。"""
    top = results[0]
    conf = assess(results)
    _lvl = conf["等级"]
    _bd, _bg, _head, _mark = {
        "较高": ("#1f5c3a", "#e9f2ec", "最可能的证型", "🌡️"),
        "中等": ("#c47f1a", "#fdf5e6", "可能是", "🌤️"),
        "较低": ("#8a6d4a", "#f8f5f0", "证据不足，暂偏向", "❔"),
    }.get(_lvl, ("#1f5c3a", "#e9f2ec", "可能是", "🌤️"))

    # --- 证型卡
    score_pct = min(100, int(top["得分"] / 20 * 100))
    chips = "".join(f'<span class="chip">{h}</span>' for h in top["命中"][:10])
    _html(f"""
    <div class="syn-card" style="border-color:{_bd}33">
      <div class="syn-name" style="color:{_bd}">{_mark} {_head}：{top['证型']}</div>
      <div class="syn-meta">{top['类别']}　·　匹配 {top['得分']} 分
        <span class="badge" style="background:{_bg};color:{_bd};margin-left:.4rem">把握{_lvl}</span>
      </div>
      <div class="bar-out"><div class="bar-in" style="width:{score_pct}%;background:{_bd}"></div></div>
      <div style="color:#7d7a6b;font-size:.82rem">{conf['说明']}</div>
      <div style="margin-top:.65rem;font-size:.92rem;color:#3c3c36">
        <b style="color:{BOLD}">辨证依据：</b>{top['依据']}</div>
      <div style="margin-top:.5rem">{chips}</div>
    </div>""")
    if conf.get("冲突"):
        _html(f'<div class="warnbox">⚠️ 需鉴别：{conf["冲突"]}</div>')

    # --- 就医红旗（置顶）
    plan = build_plan(results, hints, all_symptoms)
    for _w in plan.get("就医", []):
        st.error(f"🚨 {_w}")

    # --- 基础调养（常显，不必点开）
    _html('<div class="sec">🌿 基础调养</div>')
    _icons = {"饮食": "🍲", "茶饮": "🍵", "穴位": "💆", "生活": "💤"}
    for k, v in top["建议"].items():
        if k == "穴位":
            v = acupoints.expand(v)
        _html(f'<div class="adv"><span class="k">{_icons.get(k,"·")} {k}</span>{v}</div>')

    # --- 体质倾向
    cons = constitution.assess(top.get("命中", []))
    if cons:
        _cs = "　".join(f"<b>{c['name']}</b>" for c in cons[:2])
        _html(f'<div class="hintbox">🧬 体质倾向：{_cs}　'
              + cons[0]["advice"] + "</div>")

    # --- 分组标签：因人调整 / 方剂 / 医案 / 典籍
    _pop = plan.get("因人") or []
    _clue = plan.get("因线索") or []
    _sym = plan.get("对症") or []
    _minor = plan.get("兼证") or []
    _contra = plan.get("禁忌") or []
    _ph = plan.get("阶段")
    _s = plan.get("因时")

    try:
        from src.cases import search as _case_search
        _cs = _case_search(all_symptoms, 2)
    except Exception:
        _cs = []
    _fml = formulas.for_syndrome(top["证型"], 3)

    tab_names = ["🧭 因人因时调整", "💊 参考方剂", "📂 相似医案", "📚 典籍原文"]
    tabs = st.tabs(tab_names)

    # --- tab1：因人因时
    with tabs[0]:
        if _ph:
            _html(f'<div class="okbox"><b>⏳ 调理节奏 · {_ph["阶段"]}</b><br>{_ph["策略"]}'
                  f'<br><span style="color:#5f7a6a">{_ph["预期"]}</span></div>')
        if _s:
            _html(f'<div class="sec">🗓️ 因时 · {_s["季节"]}季</div>')
            _html(f'<div class="adv"><span class="k">要点</span>{_s["重点"]}</div>')
            _html(f'<div class="adv"><span class="k">🍲 饮食</span>{_s["饮食"]}</div>')
            _html(f'<div class="adv"><span class="k">🛌 起居</span>{_s["起居"]}</div>')
            _html(f'<div class="adv"><span class="k">🍵 茶饮</span>{_s["茶饮"]}　'
                  f'<span class="k" style="margin-left:1rem">💆 穴位</span>{acupoints.expand(_s["穴位"])}</div>')
        if _pop:
            _html('<div class="sec">👤 因人</div>')
            for _p in _pop:
                _html(f'<div class="adv"><span class="k">{_p["人群"]}</span>{_p["要点"]}<br>'
                      f'<span style="color:#6b6b5e">🍲 {_p["饮食"]}　💆 {acupoints.expand(_p["穴位"])}</span><br>'
                      f'<span style="color:#8a1f18">⚠️ {_p["提醒"]}</span></div>')
        if _clue:
            _html('<div class="sec">🔍 针对你的诱因</div>')
            for _p in _clue:
                _html(f'<div class="adv"><span class="k">{_p["线索"]}</span>{_p["要点"]}<br>'
                      f'<span style="color:#2e7d5b">✅ {_p["做"]}</span><br>'
                      f'<span style="color:#8a1f18">🚫 {_p["忌"]}</span></div>')
        if _sym:
            _html('<div class="sec">➕ 兼顾你的其他不适</div>')
            for _p in _sym:
                _bits = []
                if _p.get("做"):
                    _bits.append(f'✅ {_p["做"]}')
                if _p.get("穴位"):
                    _bits.append(f'💆 {acupoints.expand(_p["穴位"])}')
                if _p.get("食疗"):
                    _bits.append(f'🍲 {_p["食疗"]}')
                _html(f'<div class="adv"><span class="k">{_p["对应"]}</span>{_p["要点"]}'
                      + (f'<br><span style="color:#6b6b5e">{"　".join(_bits)}</span>' if _bits else "")
                      + "</div>")
                if _p.get("提醒"):
                    _html(f'<div class="warnbox">⚠️ {_p["提醒"]}</div>')
        if _minor:
            _html('<div class="sec">🧩 兼证参考</div>')
            for _m in _minor:
                _html(f'<div class="adv"><span class="k">{_m["证型"]}｜{_m["得分"]}分</span>'
                      f'{_m["要点"]}</div>')
        if _contra:
            for _c in _contra:
                _html(f'<div class="warnbox"><b>🚫 本证型最忌</b>：{_c["忌口"]}<br>'
                      f'<span style="color:#8a5f5a">为什么：{_c["理由"]}</span></div>')

    # --- tab2：方剂
    with tabs[1]:
        if _fml:
            _html('<div class="hintbox">以下为该证型的<b>历代代表方</b>，用于了解"中医通常从哪个方向'
                  '用药"。<b>不给剂量</b>——剂量须由医师按体质与兼证加减，请勿自行抓药。</div>')
            for _f in _fml:
                _html(f"""<div class="fml">
                  <span class="n">{_f['名']}</span><span class="s">{_f['出处']}</span>
                  <div class="row"><b>组成</b>：{_f['组成']}</div>
                  <div class="row"><b>功用</b>：{_f['功用']}</div>
                  <div class="row"><b>主治</b>：{_f['主治']}</div>
                  {f'<div class="row" style="color:#8a1f18"><b>注意</b>：{_f["注意"]}</div>' if _f.get("注意") else ""}
                </div>""")
        else:
            st.caption("该证型暂未收录对应方剂。")

    # --- tab3：医案
    with tabs[2]:
        if _cs:
            st.caption("别人出现类似症状时，医生是怎么辨、怎么想的 —— 用来理解思路，别照搬。")
            for _k, _c in enumerate(_cs):
                with st.expander(f"{_c['id']}｜{_c['证型']}｜匹配 {_c['匹配数']} 个症状",
                                 expanded=(_k == 0)):
                    if _c["症状串"]:
                        st.markdown(f"**病历要点**：{_c['症状串']}")
                    st.markdown(f"**病机**：{_c['病机']}　**证型**：{_c['证型']}")
                    if _c["体会"]:
                        st.markdown(f"**医生是怎么想的**：{_c['体会']}")
        else:
            st.caption("没有找到足够相似的医案（不硬凑）。")

    # --- tab4：典籍
    with tabs[3]:
        _refs = []
        try:
            from src import rag_semantic, rag
            _sem = rag_semantic.search(all_symptoms, 2)
            _refs = _sem if _sem else rag.enrich(all_symptoms, 2)
        except Exception:
            try:
                from src.rag import enrich as _enrich
                _refs = _enrich(all_symptoms, 2)
            except Exception:
                _refs = []
        if _refs:
            for _r in _refs:
                st.markdown(f"**〔{_r['书']}〕**　{_r['片段']}")
        else:
            st.caption("暂无典籍片段。")

    # --- 其他可能证型
    if len(results) > 1:
        st.caption("其他可能证型：" + "、".join(f"{r['证型']}({r['得分']}分)"
                                                 for r in results[1:4]))

    # --- 追问（低置信时）
    if allow_probe and _lvl == "较低":
        _html('<div class="hintbox">👇 想把方向定下来？回答下面几个问题即可当场复判。</div>')
        _probe_block(all_symptoms, hints, tag="low")

    # --- 导出
    try:
        _md = _export_markdown(results, plan, _cs, _fml)
        st.download_button("⬇️ 下载这份调理方案（Markdown）", _md,
                           file_name=f"中医调养方案_{top['证型']}.md",
                           mime="text/markdown")
    except Exception:
        pass

    st.markdown('<div style="color:#b3261e;font-size:.84rem;margin-top:1rem">'
                '以上仅供参考，不构成医疗诊断，不适请及时就医。</div>', unsafe_allow_html=True)


def _export_markdown(results, plan, cases, fmls):
    """把结果拼成可保存的 Markdown。"""
    top = results[0]
    L = [f"# 中医调养方案：{top['证型']}", "",
         f"- 类别：{top['类别']}", f"- 匹配得分：{top['得分']}", f"- 辨证依据：{top['依据']}",
         f"- 命中症状：{'、'.join(top['命中'])}", ""]
    L.append("## 基础调养")
    for k, v in top["建议"].items():
        L.append(f"- **{k}**：{v}")
    if plan.get("阶段"):
        L += ["", "## 调理节奏", plan["阶段"]["阶段"] + "：" + plan["阶段"]["策略"]]
    s = plan.get("因时")
    if s:
        L += ["", f"## 因时（{s['季节']}）", s["重点"],
              f"- 饮食：{s['饮食']}", f"- 起居：{s['起居']}"]
    for p in plan.get("因线索", []):
        L += ["", f"## 针对「{p['线索']}」", p["要点"], f"- 做：{p['做']}", f"- 忌：{p['忌']}"]
    for p in plan.get("因人", []):
        L += ["", f"## 因人（{p['人群']}）", p["要点"]]
    for p in plan.get("对症", []):
        L += ["", f"## 兼顾「{p['对应']}」", p["要点"]]
    if fmls:
        L += ["", "## 参考方剂（不给剂量，须医师处方）"]
        for f in fmls:
            L.append(f"- **{f['名']}**（{f['出处']}）：{f['功用']}｜组成：{f['组成']}")
    if cases:
        L += ["", "## 相似医案"]
        for c in cases:
            L.append(f"- {c['id']}（{c['证型']}）：{c['症状串']}")
    for w in plan.get("就医", []):
        L += ["", f"> 🚨 {w}"]
    L += ["", "---", "> 本方案仅供调养参考，不构成医疗诊断，不适请及时就医。"]
    return "\n".join(L)


def _probe_block(all_symptoms, hints, tag="main"):
    """追问 + 当场复判：优先按关键词追问，其次按症状域。"""
    from src.normalize import ALL_KEYWORDS, expand_symptoms
    from src.probe import probes_for
    from src.triage import triage

    try:
        _exp, _ = expand_symptoms(all_symptoms)
    except Exception:
        _exp = set()
    kws = probes_for(all_symptoms, _exp)

    _opts = {}
    if kws:
        _html('<div class="sec">❓ 针对性追问（跟着你说的关键词）</div>'
              + "".join(f'<span class="chip">{_k["关键词"]}</span>' for _k in kws))
        for _k in kws:
            for q in _k["追问"]:
                for label, words in q["选项"].items():
                    if words:
                        _opts[f"{q['问']}·{label}"] = words
    else:
        _t0 = triage("、".join(all_symptoms))
        for d in _t0["域"]:
            for q in d["追问"]:
                for label, words in q["选项"].items():
                    if words:
                        _opts[f"{d['名']}·{label}"] = words
        if _opts:
            _html('<div class="sec">❓ 回答几个问题，我就能给出证型</div>')

    if not _opts:
        return kws, False

    _picks = st.multiselect("选符合你的（可多选）", list(_opts.keys()), key=f"probe_pick_{tag}")
    done = False
    if st.button("按这些再判断", key=f"probe_btn_{tag}", use_container_width=True):
        if not _picks:
            st.info("先选至少一项。")
        else:
            _adds, _clues = [], []
            for _p in _picks:
                for _w in _opts[_p]:
                    (_adds if _w in ALL_KEYWORDS else _clues).append(_w)
            _hs = dict(hints)
            for _c in _clues:
                _hs[_c] = True
            _new = all_symptoms + [w for w in _adds if w not in all_symptoms]
            _r = diagnose(_new, _hs)
            if _r:
                st.success(f"补充后把握：{assess(_r)['等级']} —— 结论见下")
                st.session_state["probe_add"] = _adds
                _render_diagnosis(_r, _hs, _new, allow_probe=False)
                done = True
            else:
                st.info("还是不够明确，再选几项。")
    return kws, done


def _show_triage(all_symptoms, hints):
    """无证型可判时的兜底：关键词追问 + 症状域通用调理。"""
    from src.triage import triage

    t = triage("、".join(all_symptoms))
    if t["笼统"]:
        _html('<div class="hintbox">你这次的描述比较笼统。单凭它我不会硬给你安一个证型 —— 那样不负责。'
              '下面按方向先给建议，再问你几个关键问题。</div>')
    _, done = _probe_block(all_symptoms, hints, tag="triage")
    if not done:
        if t["域"]:
            _html(f'<div class="sec">🔎 相关方向：{"、".join(d["名"] for d in t["域"])}</div>')
        for d in t["域"]:
            _html(f'<div class="adv"><span class="k">{d["名"]}</span>{d["生活"]}</div>')
            _html(f'<div class="warnbox">⚠️ {d["就医"]}</div>')
        _html('<div class="sec">🧱 基础四条（不分证型，先做到这些）</div>')
        for _k, _v in t["底盘"].items():
            _html(f'<div class="adv"><span class="k">{_k}</span>{_v}</div>')


# ============================================================ 头部
_html("""
<div class="brand">
  <h1>中医药辨证调养助手</h1>
  <div class="sub">用身体感受说话，给你一个可执行的调养方向</div>
  <div class="rule"></div>
</div>""")

mode = st.radio("模式", ["🏠 日常养生", "🌡️ 辨证论治"], horizontal=True,
                key="ui_mode", label_visibility="collapsed")

# ============================================================ 输入区
if "pending_example" in st.session_state and st.session_state["pending_example"]:
    st.session_state["symptom_text"] = st.session_state.pop("pending_example")
if "symptom_text" not in st.session_state:
    st.session_state["symptom_text"] = ""

text = st.text_input(
    "你的身体感受",
    key="symptom_text",
    placeholder="例：最近总睡不着，白天没劲，大便也不成形　（用逗号/空格分隔更准）",
)
common = st.multiselect(
    "或直接点选常见症状：",
    options=[
        "失眠", "入睡难", "多梦", "早醒", "齿痕", "手脚冰凉", "怕冷", "容易累", "乏力",
        "口干", "口苦", "脱发", "便秘", "大便不成形", "大便黏腻", "长痘", "眼干",
        "腰酸", "没精神", "食欲不振", "头痛", "发热", "恶寒", "咳嗽", "痰黄", "痰白",
        "咽喉肿痛", "流清涕", "鼻塞", "气短", "自汗", "盗汗", "心悸", "心烦", "口舌生疮",
        "头晕", "耳鸣", "胁肋胀痛", "胸闷", "腹胀", "便溏", "腹泻", "小便黄", "夜尿多",
        "腰膝酸软", "畏寒肢冷", "手足心热", "潮热", "面色萎黄", "月经量少", "急躁易怒",
        "情绪抑郁", "叹气", "身体困重", "舌苔厚腻", "舌红", "舌淡",
    ],
    default=[], key="ui_common",
    placeholder="点选你有的症状（可多选，也可以直接在上面输入）",
)

_c1, _c2 = st.columns([1, 2.2])
submitted = _c1.button("💡 开始分析", type="primary", use_container_width=True)
with _c2:
    _html('<div style="color:#7d7a6b;font-size:.82rem;padding-top:.55rem">'
          '试试：</div>')
_ec = st.columns(4)
_EXAMPLES = [
    ("最近总睡不着，还老做梦", "失眠多梦"),
    ("吃不下饭，人也没劲，大便稀", "脾虚乏力"),
    ("一吹风就头疼，还流清鼻涕", "风寒感冒"),
    ("脾气大、爱叹气、两肋胀", "肝郁气滞"),
]
for _i, (_ex_text, _ex_label) in enumerate(_EXAMPLES):
    if _ec[_i].button(_ex_label, key=f"ex_{_i}", use_container_width=True):
        st.session_state["pending_example"] = _ex_text
        st.session_state["analysis_go"] = True
        st.rerun()

# 追问闭环：把上轮勾选的补充并进来
all_symptoms = []
if text:
    all_symptoms += parse_symptoms(text)
if common:
    all_symptoms += list(common)
if st.session_state.get("probe_add"):
    all_symptoms += [w for w in st.session_state["probe_add"] if w not in all_symptoms]

# ============================================================ 结果区
if submitted:
    st.session_state["analysis_go"] = True

if st.session_state.get("analysis_go"):
    st.markdown("---")
    if not all_symptoms:
        st.error("请先输入你的困扰，或点选常见症状。")
    elif mode.startswith("🏠"):
        results = daily_advice(all_symptoms)
        _html(f'<div class="sec">你的困扰：{"、".join(all_symptoms)}</div>')
        _applied = [k for k, v in patient_hints.items() if v]
        if _applied:
            st.caption(f"👤 已结合：{'、'.join(_applied)}")

        _dplan = build_plan([], patient_hints, all_symptoms)
        for _w in _dplan.get("就医", []):
            st.error(f"🚨 {_w}")

        if not results:
            _fb = diagnose(all_symptoms, patient_hints)
            if _fb:
                _html(f'<div class="hintbox">日常养生条目里没有直接对应项。'
                      f'切到「🌡️ 辨证论治」可看完整分析：最可能是「{_fb[0]["证型"]}」'
                      f'（{_fb[0]["类别"]}）。先把通用建议给你：</div>')
                _s1 = _dplan.get("因时")
                if _s1:
                    _html(f'<div class="adv"><span class="k">🗓️ {_s1["季节"]}季</span>{_s1["提醒"]}</div>')
                for _p in _dplan.get("因人", []):
                    _html(f'<div class="adv"><span class="k">👤 {_p["人群"]}</span>{_p["要点"]}</div>')
                for _p in _dplan.get("因线索", []):
                    _html(f'<div class="adv"><span class="k">🔍 {_p["线索"]}</span>{_p["要点"]}<br>'
                          f'<span style="color:#2e7d5b">✅ {_p["做"]}</span><br>'
                          f'<span style="color:#8a1f18">🚫 {_p["忌"]}</span></div>')
            else:
                st.warning("暂未找到对应条目，换个说法试试（如：失眠 / 大便不成形 / 眼干 / 腰酸）。")
        else:
            _rc = recipes.find(all_symptoms)
            if _rc:
                _html('<div class="sec">📖 典籍食疗方</div>')
                _seen = set()
                for rc in _rc:
                    if rc["名称"] in _seen:
                        continue
                    _seen.add(rc["名称"])
                    _html(f'<div class="adv"><span class="k">{rc["名称"]}</span>'
                          f'（{rc["病症"]}）<br>🛒 用料：{rc["用料"]}<br>🍳 做法：{rc["做法"]}</div>')
            for r in results:
                _html(f'<div class="sec">🌿 {r["条目"]}</div>')
                for k, v in r.items():
                    if k in ("条目", "命中词"):
                        continue
                    if k == "穴位":
                        v = acupoints.expand(v)
                    _icons = {"生活": "🛌", "饮食": "🍲", "茶饮": "🍵", "穴位": "💆",
                              "情绪": "🧘", "运动": "🏃"}
                    _html(f'<div class="adv"><span class="k">{_icons.get(k,"·")} {k}</span>{v}</div>')
                if r.get("tcm_view"):
                    st.caption(f"🧭 中医怎么看：{r['tcm_view']}")
                if r.get("see_doctor"):
                    _html(f'<div class="warnbox">🩺 {r["see_doctor"]}</div>')
    else:
        results = diagnose(all_symptoms, patient_hints)
        _html(f'<div class="sec">输入症状：{"、".join(all_symptoms)}</div>')
        _applied = [k for k, v in patient_hints.items() if v]
        if _applied:
            st.caption(f"👤 已结合你的情况：{'、'.join(_applied)}（因人制宜加权）")
        if not results:
            _show_triage(all_symptoms, patient_hints)
        else:
            _render_diagnosis(results, patient_hints, all_symptoms)

st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#a09a88;font-size:.78rem;line-height:1.7">'
    '中医药辨证调养助手 · 41 证型 · 61 方 · 250 例医案 · 21 部典籍<br>'
    '仅供中医知识学习与养生参考，不构成医疗诊断，不替代专业医师诊疗</div>',
    unsafe_allow_html=True,
)
