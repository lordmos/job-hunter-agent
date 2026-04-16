# Phase 08 — LangGraph 图编排设计

## 本阶段目标
把 server.py 里手写的 while 循环状态机重构为 LangGraph StateGraph，让业务逻辑和执行控制分离。

## 核心概念

### StateGraph(State) 是什么
- 创建一个图，`State` 是图流转的共享上下文（共享内存）
- 每个节点：**读** state 决定做什么，**返回 dict** 由 LangGraph merge 回 state
- 条件函数只能**读** state，不能写，写只能在节点里做

### 三个核心 API
```python
graph.add_node("name", fn)               # 注册节点
graph.add_edge("a", "b")                 # 固定边
graph.add_conditional_edges("a", fn)     # 条件边，fn(state) 返回下一节点名
```

## 图结构设计

```
START → node_call_llm
node_call_llm → [有 tool_calls?] → node_execute_tools
               [stop]            → END

node_execute_tools → [parse_jd + parse_profile 都有?] → node_match_skills
                    [没齐]                             → node_call_llm

node_match_skills → node_generate_resume_advice (直连)
node_generate_resume_advice → END
```

### State 设计
```python
class State(TypedDict):
    messages: list   # 对话历史，节点之间传递
    context: dict    # parse_jd / parse_profile / match_result / advice_result
```
不需要 `need_resume_advice` flag，用 context 里 key 是否存在来推导状态。

## 踩坑记录

### 1. 条件函数不能写 state
```python
# ❌ 错误：条件函数里改 state
def route_after_tools(state):
    state['context']['x'] = ""
    return "next_node"

# ✅ 正确：写 state 只能在节点函数里
def node_execute_tools(state):
    state['context'].pop('match_result', None)
    return state
```

### 2. 空字符串 ≠ 不存在
```python
ctx['key'] = ""        # ❌ 'key' in ctx 仍然为 True
ctx.pop('key', None)   # ✅ 真正删除 key
```

### 3. node_call_llm_json 反模式
早期设计了一个"判断现在是 match 还是 advice 阶段"的节点，本质上是把业务逻辑又塞回了一个大节点。
**正确做法**：每个节点自己完整负责（构建 prompt → 调 LLM → 解析结果 → 写 context）。

### 4. 节点职责划分原则
- `node_call_llm` → 流式对话，yield SSE 给前端
- `node_match_skills` → 非流式，拿完整 JSON，写 `context['match_result']`
- `node_generate_resume_advice` → 非流式，拿完整 JSON，写 `context['advice_result']`

两类调用方式本来就不同，不要强行合并到一个节点。

### 5. 多轮会话更新 JD/profile 时的状态清理
```python
def node_execute_tools(state):
    ctx = state['context']
    if tool_name == 'parse_jd':
        ctx['parse_jd'] = result
        ctx.pop('match_result', None)      # 旧 match 作废
        ctx.pop('advice_result', None)     # 旧建议作废
```
状态机自然重新触发 match → advice 流程，不需要额外控制。

## SSE 与 LangGraph 集成方案

- 节点不 yield，图来 yield
- `graph.astream_events()` 自动捕获图内所有事件
- FastAPI `/chat` 消费 `astream_events` 里的流式 chunk

```python
async for event in graph.astream_events(state, version="v2"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        yield f"data: {chunk.content}\n\n"
```

## 当前状态
- [x] LangGraph hello world 跑通
- [x] 条件边跑通
- [x] 图骨架设计完成（graph_test.py）
- [ ] node_call_llm 接入真实 DeepSeek LLM
- [ ] node_execute_tools 实现工具调用
- [ ] node_match_skills / node_generate_resume_advice 实现
- [ ] 接入 astream_events + FastAPI SSE
 