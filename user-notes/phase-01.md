# 课程要求

## 第一步：搭项目骨架 + 调通 DeepSeek API。你的方向是这样的：

1. 初始化 Python 项目 — 用 uv 或 pip + venv 管理依赖
2. 装两个包 — fastapi 和 openai（DeepSeek 兼容 OpenAI SDK，这是它的设计，见 DeepSeek API 文档）
3. 写一个最小脚本 — 用 OpenAI SDK 调 DeepSeek，发一句话拿到回复

## 笔记

1. 命令行创建虚拟环境

```bash

mkdir background
cd background
# 初始化虚拟环境
python -m venv .venv
# 使虚拟环境生效
source ./.venv/bin/activate

```

2. 安装 fastapi、openai、python-dotenv

```bash

pip3 install fastapi openai python-dotenv

```

- 对应的的文档链接：
  - [FastAPI](https://fastapi.tiangolo.com/)
  - [OpenAI](https://platform.openai.com/docs/)
  - [python-dotenv](https://pypi.org/project/python-dotenv/)
  - [DeepSeek API](https://platform.deepseek.com/docs/)

## 给导师的提问

- **提问：** 我有一个问题，openai现在支持js和python库，为何你推荐用python？

- **回答：** 好问题。直说原因：
  - AI Agent 生态是 Python 主导的。 LangChain、LangGraph、LlamaIndex、CrewAI——主流 Agent 框架都是 Python 优先。JS 版本有，但功能滞后、社区小、文档少。你到第二阶段要用 LangGraph 做多 Agent 编排，JS 版会卡住你。
  - 求职市场的现实。 你搜 "AI Agent Engineer" 的 JD，90%+ 要求 Python。你用 JS 写后端，面试时会被问"为什么不用 Python"，而答案只能是"我不会"——这不是你想要的叙事。
  - 你已经会 JS 了，不需要再证明。 简历上多一门 Python + FastAPI 是增量价值。用 JS 写只是在舒适区里重复。
  - AGENT.md 里写的也很直接："Python FastAPI — AI 生态主力语言"。

## 关于 Messages

Chat Completions API 的 messages 数组有三个核心 role：

| role | 干什么 | 举例|
|---|---|---|
|system|给 LLM 设定身份和规则，LLM 会全程遵守|"你是一个求职教练，只回答求职相关问题"|
|user|用户说的话|"帮我分析这个 JD"|
|assistant|LLM 之前回复的内容|（上一轮 LLM 的回答）|

这就是你 MVP 里"对话交互"功能的核心原理。

## System Prompt 实验

- 模糊的 prompt（"请你扮演""请你尽量详细""谢谢"）→ 对 LLM 没有约束力
- 有约束力的 prompt 需要**明确规则和边界**，例如：拒绝无关话题、要求行动步骤、限制字数
- 好的 prompt 是给 LLM 画边界，不是跟它聊天

## 下一步：JD 解析器（Tool Use / Function Calling）

核心问题：让 LLM 返回结构化数据而非自由文本。

| 方案 | 原理 | 适用场景 |
|------|------|---------|
| Tool Use / Function Calling | 定义函数签名，LLM 决定调用并返回符合签名的参数 | LLM 需要"做动作" |
| Structured Output | 直接要求 LLM 按 JSON Schema 返回 | 纯粹需要格式化输出 |

JD 解析器用 Function Calling——因为后面要让 Agent 自己决定"什么时候该解析 JD"。

**参考文档：**
- [OpenAI Function Calling 文档](https://platform.openai.com/docs/guides/function-calling)（DeepSeek 兼容此格式）

**任务：** 在 app.py 定义 `parse_jd` 函数签名，字段：`job_title`、`company`、`required_skills`、`preferred_skills`、`experience_years`，传一段真实 JD 跑通。
