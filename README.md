# 🌿 TCM Agent — 中医药辨证调养助手

> 输入你的身体感受（症状），基于中医辨证理论给出**可能的证型** + **调养建议**（饮食/茶饮/穴位/生活作息）+ 配图。
> 开源项目，MIT 许可证，可自由下载使用。

**⚠️ 重要声明**：本项目仅用于**中医知识学习与养生参考**，不构成医疗诊断，**不替代专业医师诊疗**。身体不适请及时就医。

---

## ✨ 核心功能

- ✅ **症状 → 中医辨证**：基于八纲辨证（阴阳·表里·寒热·虚实）+ 脏腑辨证，输出可能的证型（如"肝郁气滞""脾气虚"）
- ✅ **31 个常见证型**：覆盖外感、肺系、心系、肝系、脾系、肾系、气血津液
- ✅ **调养建议生成**：针对证型给出饮食、茶饮、穴位、生活作息建议
- ✅ **Web 界面**：浏览器打开就能用，无需命令行
- ✅ **可解释**：每个结论都标注辨证依据与命中症状，不是黑盒
- ✅ **离线可用**：纯规则引擎，无需 API key，下载即用

## 🚀 快速开始

### 环境准备
- Python 3.10+（本机：`L:\Python312\python.exe`）

### 安装
```bash
git clone https://github.com/你的用户名/tcm-agent.git
cd tcm-agent
pip install -r requirements.txt
```

### 方式一：Web 界面（推荐）
```bash
pip install streamlit
streamlit run app.py
```
浏览器自动打开 → 输入症状 → 点"开始辨证"。

### 方式二：命令行
```bash
python examples/demo.py --symptom "头痛 怕冷 流清涕"
```

### 运行测试
```bash
python tests/test_knowledge.py
```

### 基本使用（命令行输出示例）
```
🌡️  可能证型：风寒束表（风寒感冒）
📋  辨证依据：恶寒 + 无汗 + 流清涕 + 舌淡苔薄白
🍵  建议茶饮：生姜红糖水
💆  穴位调理：风池穴、大椎穴
💤  生活建议：注意保暖，避风寒，喝热水
```

## 📁 项目结构
```
tcm-agent/
├── app.py              # 🌐 Web 界面（Streamlit）
├── README.md
├── LICENSE             # MIT
├── .gitignore
├── requirements.txt
├── src/
│   ├── agent.py        # 辨证主逻辑（症状→证型→调养）
│   └── knowledge.py    # 中医知识库（31 证型，症状-证型-调养规则表）
├── tests/
│   └── test_knowledge.py  # 知识库自检（证型判定/无匹配/边界）
├── data/
│   └── sample/         # 示例数据
├── examples/
│   └── demo.py         # 命令行演示
├── docs/
└── assets/             # 配图（后续放真实穴位/药材图）
```

## 🧠 技术架构
- **辨证引擎**：纯 Python 规则 + 加权知识库（可解释、可扩展、离线）
- **Web 界面**：Streamlit
- **未来增强**：RAG（接入已下载的 21 本中医经典做检索）、可选 LLM 润色

## 🤝 贡献指南
欢迎提交 Issue 和 Pull Request！尤其是补充更多"症状→证型"知识条目。

## 📄 许可证
[MIT License](./LICENSE)

## 📮 反馈
通过 GitHub Issue 反馈问题或建议。
