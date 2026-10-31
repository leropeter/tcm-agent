# -*- coding: utf-8 -*-
"""dulwich 提交：暂存所有变更并 commit（不 push）。"""
import os
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

paths = [p.decode() if isinstance(p, bytes) else p
         for p in list(st.unstaged) + list(st.untracked)]
paths = [p for p in paths if os.path.exists(os.path.join(REPO, p))]
print(f"待加入 {len(paths)} 个路径")

porcelain.add(repo, paths=paths)

st2 = porcelain.status(repo)
staged = st2.staged
print(f"已暂存: add={len(staged.get('add', []))} modify={len(staged.get('modify', []))} "
      f"delete={len(staged.get('delete', []))}")

bad = [p for p in staged.get('add', []) if b'__pycache__' in p or b'.pyc' in p]
print(f"误入 pycache: {len(bad)}")
if bad:
    repo.stage([p for p in staged.get('add', []) if p not in set(bad)])
    print("已剔除")

MSG = """feat: 口语归一化 + 分诊追问 + 61 方 + 250 医案 + 口语评测集

- src/normalize.py  口语→标准术语归一化（226 条映射），口语回归 0/16 → 16/16
- src/triage.py     笼统输入的分诊层（10 个症状域），证据不足时不硬给证型
- src/probe.py      关键词驱动追问（23 词 × 49 问 × 308 选项），答完当场复判
- src/advice.py     7 维差异化建议（因时/因人/线索/对症/兼证/禁忌/红旗）
- src/cases.py      250 例真实医案检索（TCMEval-SDT）
- src/formulas.py   61 首经典方，41 证型全覆盖，只给组成不给剂量
- src/agent.py      置信度三档 + 同源最长匹配 + 命中原词追溯
- eval/             100 条口语评测集 + 跑分脚本（Top1 72%，过度诊断 0/8）
- docs/EVALUATION.md 三层评测口径、过拟合风险、为什么临床只有 8%
- README 重写       30 秒启动 + 真实数字 + 明确的「它不能做什么」
- tests             10 个套件 / 276 项全绿
"""

author = b"leropeter <leropeter@users.noreply.github.com>"
sha = porcelain.commit(repo, message=MSG.encode("utf-8"), author=author, committer=author)
print("新提交:", sha.decode())

head = repo.head().decode()
print("HEAD:", head)
