# -*- coding: utf-8 -*-
"""
app.py — TCM Agent Web 界面（Streamlit）
========================================
启动:  streamlit run app.py
功能:  输入症状 → 中医辨证 → 调养建议 + 配图
"""
import streamlit as st
from src.agent import diagnose, parse_symptoms

# ---------- 页面配置 ----------
st.set_page_config(page_title="TCM Agent 中医辨证助手", page_icon="🌿", layout="centered")

# ---------- 样式 ----------
st.markdown("""
<style>
    .tcm-title { text-align:center; font-size:2.2rem; color:#2e7d32; }
    .tcm-sub { text-align:center; color:#555; margin-bottom:1.5rem; }
    .syndrome-box { border-left:5px solid #2e7d32; background:#f1f8e9; padding:1rem 1.2rem; border-radius:8px; margin:1rem 0; }
    .syndrome-name { font-size:1.6rem; font-weight:bold; color:#2e7d32; }
    .advice-box { background:#fffde7; border-left:5px solid #f9a825; padding:1rem 1.2rem; border-radius:8px; margin:1rem 0; }
    .warn { color:#b71c1c; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="tcm-title">🌿 TCM Agent 中医辨证助手</div>', unsafe_allow_html=True)
st.markdown('<div class="tcm-sub">输入你的身体感受，基于中医辨证理论给出可能的证型与养生建议</div>', unsafe_allow_html=True)

# ---------- 免责声明 ----------
st.warning("⚠️ 仅供中医知识学习与养生参考，不构成医疗诊断，不替代专业医师诊疗。身体不适请及时就医。")

# ---------- 输入区 ----------
st.markdown("### 📝 你的身体感受")
with st.form("symptom_form"):
    text = st.text_input(
        "用文字描述你的症状（用逗号/空格分隔，如：头痛 怕冷 流清涕 无汗）",
        placeholder="例：心烦 失眠 口舌生疮",
    )
    common = st.multiselect(
        "或从常见症状里点选：",
        options=[
            "头痛","发热","恶寒","怕冷","咳嗽","痰黄","痰白","咽喉肿痛","流清涕","鼻塞",
            "口干","口渴","咽干","乏力","疲倦","气短","自汗","盗汗","失眠","多梦","心悸",
            "心烦","口苦","口舌生疮","头晕","耳鸣","胁肋胀痛","胸闷","腹胀","食欲不振","食少",
            "便溏","腹泻","便秘","小便黄","夜尿多","腰膝酸软","畏寒肢冷","手足心热","潮热",
            "颧红","面色苍白","面色萎黄","唇甲色淡","月经量少","急躁易怒","易怒","烦躁",
            "情志抑郁","叹气","大便黏腻","身体困重","头重如裹","舌苔厚腻","舌红","舌淡",
            "阳痿","滑精早泄","健忘","身重困倦","口淡不渴","胸胁胀痛","刺痛",
        ],
        default=[],
    )
    submitted = st.form_submit_button("💡 开始辨证", use_container_width=True)

# 合并文本输入 + 点选
all_symptoms = []
if text:
    all_symptoms += parse_symptoms(text)
if common:
    all_symptoms += list(common)

# ---------- 结果区 ----------
if submitted:
    if not all_symptoms:
        st.error("请先输入症状，或用点选的方式选择一些常见症状。")
    else:
        results = diagnose(all_symptoms)
        st.markdown(f"**输入症状**：{'、'.join(all_symptoms)}")
        if not results:
            st.warning("未找到匹配的证型。这不代表你没有问题，可能是症状描述不在知识库中。请补充更多症状，或咨询专业中医师。")
        else:
            top = results[0]
            # 主证型卡片
            st.markdown(
                f"""<div class="syndrome-box">
                    <div class="syndrome-name">{top['配图']} 最可能的证型：{top['证型']}</div>
                    <div style="color:#555">类别：{top['类别']} · 匹配 {top['得分']} 分</div>
                    <div style="margin-top:8px"><b>辨证依据：</b>{top['依据']}</div>
                    <div style="color:#777;margin-top:4px">命中症状：{'、'.join(top['命中'])}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            # 调养建议
            st.markdown('<div class="advice-box"><b>🌿 养生调养建议</b><br>', unsafe_allow_html=True)
            adv_icons = {"饮食": "🍲", "茶饮": "🍵", "穴位": "💆", "生活": "💤"}
            for k, v in top["建议"].items():
                st.markdown(f"**{adv_icons.get(k,'·')} {k}**：{v}")
            st.markdown("</div>", unsafe_allow_html=True)
            # 次要证型
            if len(results) > 1:
                others = "、".join(f"{r['证型']}({r['得分']}分)" for r in results[1:4])
                st.caption(f"其他可能证型：{others}")
            # 典籍参考（RAG）
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
            # 底部安全提示
            st.markdown('<div class="warn">以上仅供参考，不构成医疗诊断，不适请及时就医。</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("TCM Agent · 开源项目 · 知识库 31 个证型 · 基于《中医基础理论》整理")
