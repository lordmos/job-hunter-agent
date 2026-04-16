# Phase 07 — FastAPI SSE 服务化

## 今日完成
- 搭建 FastAPI 服务骨架（`server.py`）
- 设计 Pydantic 数据模型（`models/chat_request.py`）
- 实现流式 `run_agent`：while 循环 + yield + tool call 碎片收集
- 跑通完整三阶段流程：parse → match_skills → resume_advice
- 理解服务端无状态 + 客户端持有 context 的架构

---

## 踩过的坑（重要）

### 1. 相对导入 vs 绝对导入
`from .models.chat_request import ...` 相对导入只在 Python package 里有效。
必须从**项目根目录**启动，且目录有 `__init__.py`：
```bash
# 错误：在 background/ 里跑
python server.py  → ImportError

# 正确：从根目录跑
uvicorn background.server:app --reload --port 8000
```
`background/` 和 `background/models/` 都需要 `__init__.py`。

### 2. 虚拟环境没激活
每次新开终端都要：
```bash
source background/.venv/bin/activate
```
否则用系统 Python，找不到 openai/fastapi 等包。

### 3. Pydantic 类定义顺序
Python 从上到下读，被依赖的类必须先定义：
```python
# 错误：ChatRequest 用了 ChatMessage，但 ChatMessage 在后面
class ChatRequest(BaseModel):
    messages: list[ChatMessage]  # NameError！

class ChatMessage(BaseModel): ...

# 正确：依赖的先定义
class ChatMessage(BaseModel): ...
class ChatRequest(BaseModel):
    messages: list[ChatMessage]
```

### 4. Optional 没有默认值
```python
parse_jd: Optional[ParseJDResult]         # ❌ 仍然必填
parse_jd: Optional[ParseJDResult] = None  # ✅ 真正可选
```

### 5. list[ChatMessage] vs list[dict] 混用
`run_agent` 接收 `list[dict]`，但内部 append 了 `ChatMessage` 对象。
**原则：** 选一种类型，统一到底。在入口一次性 `model_dump()` 转成 dict，全程用 dict。

### 6. message_cache 在 while 循环内初始化
```python
while True:
    message_cache = list(messages)  # ❌ 每轮都重置，上一轮 tool 结果全丢
```
`message_cache` 必须在循环**外**初始化，循环内只 append。

### 7. assistant 消息必须在 tool 消息之前
OpenAI 要求消息顺序：
```
[user]
[assistant: {tool_calls: [...]}]  ← 记录 LLM 的决策，必须有
[tool: {tool_call_id: "xxx"}]     ← 才能出现 tool 结果
```
遗漏 assistant 那条，下一轮 LLM 报错。

### 8. 未初始化变量导致 UnboundLocalError
```python
if finish_reason == "stop":
    if need_resume_advice:  # ❌ 如果从未进入 tool_calls 分支，变量未定义
```
标志位必须在函数开头初始化：`need_resume_advice = False`

### 9. assistant 流式回复没有收集进 message_cache
流式模式下只 yield 出去但没拼接保存，下一轮用 `message_cache[-1]` 是错的。
```python
assistant_content = ""
for chunk in response:
    if delta.content:
        assistant_content += delta.content  # 拼接
        yield ...
if finish_reason == "stop":
    message_cache.append({"role": "assistant", "content": assistant_content})
```

### 10. json.loads 碎片化 JSON
LLM 输出 JSON 时可能带 markdown 代码块（```json...```），直接 `json.loads` 报错。
流式场景下直接传字符串给下一个 prompt 更安全，不要中间解析。

### 11. context 恢复逻辑无效
从 `working_messages` 扫描 `tool_name` 字段永远找不到（messages 里没这个字段）。
正确做法是从 `request.context` 读取：
```python
context = {}
if request.context:
    if request.context.parse_jd:
        context['parse_jd'] = request.context.parse_jd.model_dump()
    if request.context.parse_profile:
        context['parse_profile'] = request.context.parse_profile.model_dump()
```

### 12. system prompt 必须由服务端注入
客户端传来的 system 消息必须过滤，否则任何人可以篡改 prompt：
```python
working_messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
] + [m.model_dump(exclude_none=True) for m in request.messages if m.role != "system"]
```

---

## 架构设计要点

### 服务端无状态 + 客户端持有 context
- 客户端每次请求带完整 `messages` 历史 + `context`（已解析的 JD/profile）
- 服务端不存任何会话状态，请求结束即释放
- 优点：横向扩展简单；缺点：客户端可以篡改历史
- 生产级做法：session_id + 数据库，服务端管理状态

### run_agent 的 while 循环结构
```
while True:
    流式调 LLM → yield content token（实时推送）、收集 tool_call 碎片

    finish_reason == "tool_calls"
        → 追加 assistant 消息（含 tool_calls）
        → 执行工具，追加 tool 结果消息
        → 更新 context
        → 注入下一步 prompt（match_skills）
        → while 继续

    finish_reason == "stop"
        → 追加 assistant 消息（完整 content）
        → 如果 need_resume_advice → 注入 resume_advice，continue
        → 否则 return
```

### 业务逻辑混在 run_agent 里（待改进）
当前 `run_agent` 混杂了业务逻辑（JobHunter 专有）和通用 Agent 机制。
本质是一个状态机：`idle → matching → advising → done`
LangGraph 阶段会用节点/边的方式重构，分离业务流转与执行框架。

---

## 下一步
- `langgraph-agent`：用 LangGraph 实现真正的 ReAct loop，重构业务状态机
- `rag-pipeline`：引入向量数据库
- `frontend-nextjs`：Next.js 前端对接 SSE
