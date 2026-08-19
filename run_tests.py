# -*- coding: utf-8 -*-
"""
run_tests.py — 项目标准测试入口
用法: python run_tests.py   （跑全部测试套件）
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.join(HERE, "tests")
TEST_FILES = ["test_knowledge.py", "test_rag.py", "test_wellness.py", "test_data_lib.py", "test_rag_semantic.py", "test_constitution.py"]

def main():
    fails = 0
    for t in TEST_FILES:
        print(f"\n===== {t} =====")
        r = subprocess.run([sys.executable, os.path.join(TESTS_DIR, t)])
        fails += r.returncode
    print("\n" + ("=" * 40))
    if fails:
        print(f"❌ {fails} 个测试套件失败")
        return 1
    print("✅ 全部测试套件通过")
    return 0

if __name__ == "__main__":
    sys.exit(main())
