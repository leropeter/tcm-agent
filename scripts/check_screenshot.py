# -*- coding: utf-8 -*-
"""检查截图是否真的是我们的页面：命中主题色像素占比"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from PIL import Image
from collections import Counter

TARGETS = {
    "宣纸底 #faf8f3": (250, 248, 243),
    "渐变底 #f3efe4": (243, 239, 228),
    "品牌绿 #1f5c3a": (31, 92, 58),
    "赭金 #b08d3f": (176, 141, 63),
    "侧边栏 #f5f1e6": (245, 241, 230),
}


def near(c, t, tol=10):
    return all(abs(a - b) <= tol for a, b in zip(c, t))


for path in (r"E:\tcm-agent\ui_preview_1.png", r"E:\tcm-agent\ui_preview_2.png"):
    im = Image.open(path).convert("RGB")
    px = list(im.getdata())
    total = len(px)
    print(f"\n{path}  {im.size}  共 {total:,} 像素")
    cnt = Counter(px)
    for name, t in TARGETS.items():
        n = sum(v for c, v in cnt.items() if near(c, t, 12))
        print(f"  {name:22} {n:>9,}  {n/total*100:5.2f}%")
    top = cnt.most_common(5)
    print("  最常见颜色:", [(c, f"{v/total*100:.1f}%") for c, v in top])
