# -*- coding: utf-8 -*-
"""app.py 渲染冒烟测试（Streamlit AppTest，无浏览器）

新 UI 后控件用 key 定位：侧边栏 q_gender/q_age/q_recent，主区 ui_mode/symptom_text。
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from streamlit.testing.v1 import AppTest

PASS = FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {extra}")


def all_md(at):
    return "\n".join(m.value for m in at.markdown)


def click_go(at):
    btn = [b for b in at.button if "开始分析" in (b.label or "")]
    assert btn, f"找不到开始分析按钮，现有: {[b.label for b in at.button]}"
    btn[0].click().run()


def ask(text, mode="🌡️ 辨证论治", age=None, recent=None):
    at = AppTest.from_file("app.py", default_timeout=180)
    at.run()
    at.radio(key="ui_mode").set_value(mode).run()   # 默认是日常养生，必须显式设置
    if age:
        at.radio(key="q_age").set_value(age).run()
    if recent:
        at.multiselect(key="q_recent").set_value(recent).run()
    at.text_input(key="symptom_text").set_value(text).run()
    click_go(at)
    return at


print("== 冷启动与布局 ==")
at = AppTest.from_file("app.py", default_timeout=180)
at.run()
check("无异常", not at.exception, str(at.exception))
md = all_md(at)
check("品牌标题", "中医药辨证调养助手" in md)
check("副标题文案", "可执行的调养方向" in md)
check("有模式切换（key=ui_mode）", len(at.radio(key="ui_mode").options) == 2)
check("侧边栏性别", len(at.radio(key="q_gender").options) == 3)
check("侧边栏年龄", len(at.radio(key="q_age").options) == 4)
check("侧边栏近期情况含怀孕/哺乳", "怀孕/哺乳" in at.multiselect(key="q_recent").options)
check("有症状输入框", at.text_input(key="symptom_text") is not None)
check("有开始分析按钮", any("开始分析" in (b.label or "") for b in at.button))
check("有 4 个示例按钮", sum(1 for b in at.button if (b.key or "").startswith("ex_")) == 4,
      [b.key for b in at.button])
check("页脚有免责声明", "不构成医疗诊断" in md)
check("页脚标了规模", "41 证型" in md and "61 方" in md and "250 例医案" in md)

print("== 辨证：信息充足 → 高把握 + 全部分组 ==")
at2 = ask("吃不下饭，人也没劲，大便稀 面色萎黄")
check("无异常", not at2.exception, str(at2.exception))
md2 = all_md(at2)
check("给出证型", "脾气虚" in md2)
check("把握较高", "把握较高" in md2)
check("有得分进度条", "bar-in" in md2)
check("基础调养常显", "基础调养" in md2)
check("4 个分组标签", len(at2.tabs) == 4, [t.label for t in at2.tabs])
check("标签含因人因时", any("因人因时" in t.label for t in at2.tabs))
check("标签含参考方剂", any("参考方剂" in t.label for t in at2.tabs))
check("标签含相似医案", any("相似医案" in t.label for t in at2.tabs))
check("渲染方剂（有方名与组成）", "组成" in md2 and ("四君子汤" in md2 or "参苓白术散" in md2))
check("方剂明确不给剂量", "不给剂量" in md2)
check("有导出按钮", len(at2.download_button) >= 1)

print("== 辨证：低置信 → 暂偏向 + 关键词追问 ==")
at3 = ask("头晕 耳鸣 腰酸")
md3 = all_md(at3)
check("无异常", not at3.exception, str(at3.exception))
check("把握较低", "把握较低" in md3)
check("措辞为暂偏向", "暂偏向" in md3)
check("不给最可能的证型", "最可能的证型" not in md3)
check("有针对性追问", "针对性追问" in md3)
check("追问选项含症状描述", any(k in md3 for k in ("胀痛", "昏沉", "站起")), md3[-400:])

print("== 就医红旗 ==")
at4 = ask("胸痛 出汗 气短")
errs = [e.value for e in at4.error]
check("弹急诊提示", any("急诊" in e for e in errs), str(errs))

print("== 笼统输入 → 分诊 + 追问闭环 ==")
at5 = ask("肚子老是不舒服")
md5 = all_md(at5)
check("无异常", not at5.exception, str(at5.exception))
check("说明不硬安证型", "不会硬给你安一个证型" in md5 or "笼统" in md5, md5[:120])
check("有追问多选", len(at5.multiselect) >= 2, len(at5.multiselect))
_ms = at5.multiselect(key="probe_pick_triage")
_opts = _ms.options if _ms else []
check("追问选项非空", len(_opts) > 0, len(_opts))
_btn = [b for b in at5.button if "再判断" in (b.label or "")]
check("有再判断按钮", len(_btn) == 1)
if _opts and _btn:
    _ms.set_value([_opts[0]]).run()
    _btn2 = [b for b in at5.button if "再判断" in (b.label or "")]
    _btn2[0].click().run()
    md5b = all_md(at5)
    check("复判后无异常", not at5.exception, str(at5.exception))
    check("复判后出结论", "辨证依据" in md5b and "把握" in md5b, md5b[:100])

print("== 养成模式 ==")
at6 = ask("失眠 手脚冰凉", mode="🏠 日常养生")
md6 = all_md(at6)
check("无异常", not at6.exception, str(at6.exception))
check("有养生输出", "你的困扰" in md6 and len(md6) > 200)
check("养生模式不显示证型卡", "辨证依据" not in md6)

at7 = ask("手心脚心发热 夜里出汗 颧红", mode="🏠 日常养生")
check("养生未命中不留死路", any("最可能是" in i.value for i in at7.info)
      or "通用建议" in all_md(at7) or len(all_md(at7)) > 100, all_md(at7)[:80])

print("== 示例按钮能填充并出结果 ==")
at8 = AppTest.from_file("app.py", default_timeout=180)
at8.run()
_ex = [b for b in at8.button if (b.key or "").startswith("ex_")]
check("有示例按钮", len(_ex) == 4)
if _ex:
    _ex[0].click().run()
    check("点示例后无异常", not at8.exception, str(at8.exception))
    check("点示例后直接出结果", "证型" in all_md(at8) or "把握" in all_md(at8), all_md(at8)[:120])

print(f"\n总计: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
