# -*- coding: utf-8 -*-
"""用 dulwich（纯 Python git）在没装 git 的机器上做提交。"""
import sys

from dulwich import porcelain
from dulwich.repo import Repo

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = r"E:\tcm-agent"
repo = Repo(REPO)

st = porcelain.status(repo)
print("== staged ==")
for k, v in st.staged.items():
    print(f"  {k}: {v[:5]}{' ...' if len(v) > 5 else ''} ({len(v)})")
print("== unstaged ==")
print(f"  {list(st.unstaged)[:10]} ({len(st.unstaged)})")
print("== untracked ==")
print(f"  {list(st.untracked)[:20]} ({len(st.untracked)})")

head = repo.head()
print("HEAD:", head.decode() if head else None)
print("branch:", repo.refs.read_ref(b"HEAD"))
