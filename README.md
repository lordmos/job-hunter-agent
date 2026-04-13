# JobHunter Agent — 项目启动指南

> 用 AI Agent 帮自己找到 AI Agent 工程师的工作。

---

## 项目背景

你是一个 React/Node 全栈工程师，目标是在 6 周内转型为 AI Agent 工程师。这个项目是你的转型载体——边造边学，最终这个项目本身就是你简历上的核心项目。

**面试叙事**："我造了一个 AI Agent 帮自己找到了 AI Agent 工程师的工作。"

---

## 已完成

- [x] 旧方案诊断（失败原因：让 AI 当教授写教材，而不是当教练带你练）
- [x] 新 AGENT.md（教练模式 + 挑战协议 + 知识来源引用规范）
- [x] 项目选题：JobHunter Agent（求职 Agent）
- [x] 技术栈确定：Next.js + Python FastAPI + DeepSeek API
- [x] MVP 范围定义

---

## 三阶段路线

| 阶段 | 时间 | 目标 | 核心产出 |
|------|------|------|---------|
| **第一阶段** | 第 1-2 周 | MVP 能跑 | Agent 主循环 + JD 解析 + 技能匹配 + 对话交互 |
| **第二阶段** | 第 3-4 周 | 功能完整 | RAG + Planning + LangChain/LangGraph + 多 Agent |
| **第三阶段** | 第 5-6 周 | 可投递 | 项目打磨 + 简历优化 + 模拟面试 |

---

## MVP 功能定义（第一阶段）

| 功能 | 学到的 Agent 技能 | 实现方式 |
|------|-------------------|---------|
| JD 解析器 | **Tool Use** | 用户粘贴 JD 文本 → LLM 调用解析函数 → 结构化输出（技术栈、经验、职责） |
| 技能匹配 | **Prompt Engineering** | LLM 对比 JD 要求 vs 用户技能档案 → 匹配度 + 差距分析 |
| 简历定制建议 | **LLM 结构化输出** | 基于匹配结果，生成简历调整建议 |
| 对话交互 | **Memory（短期）** | 多轮对话记住上下文 |

**MVP 排除项**：爬虫、完整简历生成、多 Agent 协作、向量数据库/RAG

---

## 目标技术架构

```
┌─────────────────────────────────┐
│       Next.js 前端（React）      │
│  - 对话界面（聊天 UI）           │
│  - JD 输入面板                   │
│  - 匹配结果展示                  │
└──────────────┬──────────────────┘
               │ HTTP / WebSocket
┌──────────────▼──────────────────┐
│     Python FastAPI 后端          │
│  - /api/chat  → Agent 主循环    │
│  - /api/parse-jd → JD 解析工具  │
│  - /api/match → 技能匹配工具    │
│  - LLM Client (DeepSeek API)    │
│  - Tool Registry（工具注册表）   │
│  - Memory Manager（对话历史）    │
└─────────────────────────────────┘
```

---

## 待完成：项目搭建步骤

### 1. 初始化 Git

```bash
cd ~/Documents/Git/fire/job-hunter-agent
git init
```

### 2. 搭建 Python 后端

```bash
mkdir -p backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn openai python-dotenv
pip freeze > requirements.txt
```

创建 `.env`：
```
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3. 搭建 Next.js 前端

```bash
cd ~/Documents/Git/fire/job-hunter-agent
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir
```

### 4. 创建 .gitignore

```
# Python
backend/.venv/
__pycache__/
*.pyc
.env

# Node
frontend/node_modules/
frontend/.next/

# IDE
.DS_Store
.vscode/
```

---

## 与 AI 教练的协作方式

新的 AGENT.md 已就绪（本目录下）。核心改动：

1. **AI 是教练不是教授** — 不凭空编教材，引导你用官方文档和开源项目学习
2. **挑战协议** — AI 必须主动质疑你的理解，不能什么都说对
3. **知识来源三级制** — L1 官方文档 > L2 开源项目 > L3 技术文章，每个概念附来源
4. **项目驱动** — 先遇到问题再学解法，不按理论主题分章节
5. **不确定时必须声明** — AI 说"我不确定"比瞎编强

**开始新对话时**，告诉 AI 教练："读 AGENT.md，我们从第一阶段 MVP 开始。"

---

## 知识来源速查

在学习过程中，优先查阅以下资源：

| 主题 | 权威来源 |
|------|---------|
| LLM API 调用 | [OpenAI API Reference](https://platform.openai.com/docs/api-reference) / [DeepSeek API 文档](https://platform.deepseek.com/api-docs) |
| Function Calling / Tool Use | [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling) / [Anthropic Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) |
| Prompt Engineering | [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) |
| Agent 设计模式 | [Anthropic: Building Effective Agents](https://docs.anthropic.com/en/docs/build-with-claude/agent) |
| LangChain / LangGraph | [LangChain 官方文档](https://python.langchain.com/docs/) / [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/) |
| RAG | [OpenAI Cookbook - RAG](https://cookbook.openai.com/) |
| FastAPI | [FastAPI 官方文档](https://fastapi.tiangolo.com/) |
| Vercel AI SDK | [Vercel AI SDK 文档](https://sdk.vercel.ai/docs) |

---

## 旧方案的教训（避免重蹈覆辙）

| 错误 | 教训 |
|------|------|
| 让 AI 凭空写教材 | 知识必须来自权威来源，AI 只做解释和引导 |
| 背 API 参数 | 能查文档的东西不需要记，理解原理即可 |
| 10 Phase 线性理论课 | 项目驱动，先跑起来再理解 |
| AI 不质疑你 | 挑战协议：AI 必须主动找你方案的问题 |
| 你替 AI 做质量把关 | AI 必须附来源，你验证来源而不是验证 AI |
| 课程反复重设计 | 不设计课程了，直接写代码 |
