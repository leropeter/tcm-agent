# -*- coding: utf-8 -*-
"""
app.py — TCM Agent Web 界面（Streamlit）
========================================
两种模式：
  🏠 日常养生  输入"有点失眠/舌头有齿痕/手脚凉" → 生活化调理建议
  🌡️ 辨证论治  输入"心烦 口舌生疮" → 中医证型 + 调养 + 典籍参考
启动:  streamlit run app.py
"""
import streamlit as st
from src.agent import diagnose, parse_symptoms
from src.wellness import daily_advice
from src import acupoints, recipes

st.set_page_config(page_title="TCM Agent 中医养生助手", page_icon="🌿", layout="centered")

st.markdown("""
<style>
    .tcm-title { text-align:center; font-size:2.2rem; color:#2e7d32; }
    .tcm-sub { text-align:center; color:#555; margin-bottom:1rem; }
    .syndrome-box { border-left:5px solid #2e7d32; background:#f1f8e9; padding:1rem 1.2rem; border-radius:8px; margin:1rem 0; }
    .syndrome-name { font-size:1.5rem; font-weight:bold; color:#2e7d32; }
    .advice-box { background:#fffde7; border-left:5px solid #f9a825; padding:1rem 1.2rem; border-radius:8px; margin:1rem 0; }
    .wellness-box { background:#e8f5e9; border-left:5px solid #43a047; padding:1rem 1.2rem; border-radius:8px; margin:1rem 0; }
    .warn { color:#b71c1c; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="tcm-title">🌿 TCM Agent 中医养生助手</div>', unsafe_allow_html=True)
st.markdown('<div class="tcm-sub">日常养生调理 + 中医辨证，给你的身体感受一个调理方向</div>', unsafe_allow_html=True)

st.warning("⚠️ 仅供中医知识学习与养生参考，不构成医疗诊断，不替代专业医师诊疗。身体不适请及时就医。")

# ---------- 模式切换 ----------
mode = st.radio("选择你想问的", ["🏠 日常养生", "🌡️ 辨证论治"], horizontal=True,
                help="日常养生：失眠/舌边齿痕/手脚凉等生活困扰；辨证论治：判断证型与调养")

# ---------- 问诊：因人制宜（中医整体观念） ----------
with st.expander("👤 先告诉我一些基本情况（因人制宜，会直接影响判断）", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        gender = st.radio("性别", ["男", "女", "不便透露"], horizontal=True)
    with c2:
        age_group = st.radio("年龄段", ["25岁以下", "26-45岁", "46岁以上", "不便透露"], horizontal=True)
    recent = st.multiselect(
        "近期情况（可多选，与症状一起看更准）",
        options=[
            "熬夜", "睡眠不规律", "压力大/焦虑", "情绪不好/生气", "思虑多",
            "受凉/吹风", "换季", "吃辛辣/烧烤/火锅", "吃生冷/冰饮", "饮食不规律",
            "久坐少动", "久用眼", "劳累", "经期/产后", "月经量多", "久咳",
        ],
        default=[],
        help="这些是中医辨证的重要线索，例如同样失眠，熬夜+口苦偏向肝火，经期+多梦偏向血虚。",
    )

# 把问诊信息转成辨证线索（因人制宜）
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
    }
    for opt in recent:
        if opt in clue_map:
            hints[clue_map[opt]] = True
    return hints

patient_hints = _build_hints(gender, age_group, recent)

# ---------- 输入区 ----------
st.markdown("### 📝 你的身体感受")
with st.form("symptom_form"):
    text = st.text_input(
        "用文字描述（用逗号/空格分隔）",
        placeholder="🏠例：有点失眠 或 🩺例：心烦 失眠 口舌生疮",
    )
    common = st.multiselect(
        "或从常见里点选：",
        options=[
            # 日常养生常用
            "失眠","入睡难","多梦","早醒","齿痕","舌头有齿痕","手脚冰凉","怕冷","容易累","乏力",
            "口干","口苦","脱发","便秘","大便不成形","大便黏腻","长痘","出油","眼干","眼涩",
            "腰酸","腰痛","没精神","困倦","食欲不振","食少",
            # 辨证常用
            "头痛","发热","恶寒","咳嗽","痰黄","痰白","咽喉肿痛","流清涕","鼻塞","口渴",
            "气短","自汗","盗汗","心悸","心烦","口舌生疮","头晕","耳鸣","胁肋胀痛","胸闷",
            "腹胀","便溏","腹泻","小便黄","夜尿多","腰膝酸软","畏寒肢冷","手足心热","潮热",
            "颧红","面色苍白","面色萎黄","唇甲色淡","月经量少","急躁易怒","易怒","烦躁",
            "情志抑郁","叹气","身体困重","头重如裹","舌苔厚腻","舌红","舌淡","阳痿","滑精早泄","健忘",
        ],
        default=[],
    )
    submitted = st.form_submit_button("💡 开始", use_container_width=True)

all_symptoms = []
if text:
    all_symptoms += parse_symptoms(text)
if common:
    all_symptoms += list(common)

# ---------- 结果区 ----------
if submitted:
    if not all_symptoms:
        st.error("请先输入你的困扰，或用点选的方式选择一些内容。")
    elif mode.startswith("🏠"):
        # ===== 日常养生模式 =====
        results = daily_advice(all_symptoms)
        st.markdown(f"**你的困扰**：{'、'.join(all_symptoms)}")
        applied = [k for k, v in patient_hints.items() if v]
        if applied:
            st.caption(f"👤 针对你的情况（{'、'.join(applied)}）给下面的调理建议参考")
        if not results:
            st.warning("暂未找到对应的日常养生条目。建议换个说法（如：失眠/大便不成形/眼干/腰酸），或描述更明确一些。")
        else:
            # 典籍食疗方（从《自我调养巧治病》提取的具体做法）
            recipe_hits = recipes.find(all_symptoms)
            if recipe_hits:
                st.markdown("#### 📖 典籍食疗方")
                seen = set()
                for rc in recipe_hits:
                    key = rc["名称"]
                    if key in seen:
                        continue
                    seen.add(key)
                    st.markdown(f"**{rc['名称']}**（{rc['病症']}）")
                    st.markdown(f"🛒 用料：{rc['用料']}")
                    st.markdown(f"🍳 做法：{rc['做法']}")
                st.caption("来源：《自我调养巧治病》· 仅供调养参考，用药请遵医嘱")
            for r in results:
                title = r["条目"]
                st.markdown(f'<div class="wellness-box"><b>🌿 {title}</b></div>', unsafe_allow_html=True)
                adv_icons = {"生活": "🛌", "饮食": "🍲", "茶饮": "🍵", "穴位": "💆", "情绪": "🧘", "运动": "🏃"}
                for k, v in r.items():
                    if k in ("条目", "命中词"):
                        continue
                    if k == "穴位":
                        v = acupoints.expand(v)
                    icon = adv_icons.get(k, "·")
                    st.markdown(f"**{icon} {k}**：{v}")
                if r.get("tcm_view"):
                    st.caption(f"🧭 中医怎么看：{r['tcm_view']}")
                if r.get("see_doctor"):
                    st.markdown(f'<div class="warn">🩺 {r["see_doctor"]}</div>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        # ===== 辨证论治模式 =====
        results = diagnose(all_symptoms, patient_hints)
        st.markdown(f"**输入症状**：{'、'.join(all_symptoms)}")
        applied = [k for k, v in patient_hints.items() if v]
        if applied:
            st.caption(f"👤 已结合你的情况：{'、'.join(applied)}（因人制宜加权）")
        if not results:
            st.warning("未找到匹配的证型。这不代表你没有问题，可能是症状描述不在知识库中。请补充更多症状，或咨询专业中医师。")
        else:
            top = results[0]
            st.markdown(
                f"""<div class="syndrome-box">
                    <div class="syndrome-name">{top['配图']} 最可能的证型：{top['证型']}</div>
                    <div style="color:#555">类别：{top['类别']} · 匹配 {top['得分']} 分</div>
                    <div style="margin-top:8px"><b>辨证依据：</b>{top['依据']}</div>
                    <div style="color:#777;margin-top:4px">命中症状：{'、'.join(top['命中'])}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown('<div class="advice-box"><b>🌿 养生调养建议</b><br>', unsafe_allow_html=True)
            adv_icons = {"饮食": "🍲", "茶饮": "🍵", "穴位": "💆", "生活": "💤"}
            for k, v in top["建议"].items():
                if k == "穴位":
                    v = acupoints.expand(v)
                st.markdown(f"**{adv_icons.get(k,'·')} {k}**：{v}")
            st.markdown("</div>", unsafe_allow_html=True)
            if len(results) > 1:
                others = "、".join(f"{r['证型']}({r['得分']}分)" for r in results[1:4])
                st.caption(f"其他可能证型：{others}")
            # 典籍参考（优先语义RAG，未预构建则降级关键词检索）
            refs = []
            try:
                from src import rag_semantic, rag
                sem = rag_semantic.search(all_symptoms, 2)
                refs = sem if sem else rag.enrich(all_symptoms, 2)
            except Exception:
                try:
                    from src.rag import enrich
                    refs = enrich(all_symptoms, 2)
                except Exception:
                    refs = []
            if refs:
                st.markdown("#### 📚 典籍参考")
                for r in refs:
                    st.markdown(f"**〔{r['书']}〕**　{r['片段']}")
                    st.caption(f"相关度 {r['得分']}")
            st.markdown('<div class="warn">以上仅供参考，不构成医疗诊断，不适请及时就医。</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("TCM Agent · 开源项目 · 日常养生11项 + 辨证31证型 + 21本典籍 · 基于《中医基础理论》整理")
