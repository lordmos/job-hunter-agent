# Phase 06 — 流式输出 + FastAPI 架构设计

## 今日完成
- 理解 SSE vs WebSocket 的选择
- 实现流式 token 打印
- 实现流式 tool call 碎片收集
- 理解 yield / 生成器 / 协程原理
- 设计 FastAPI 服务架构

---

## SSE vs WebSocket

| | SSE | WebSocket |
|---|---|---|
| 方向 | 单向（服务→客户端） | 双向 |
| 断线重连 | 浏览器自动处理（Last-Event-ID） | 需要自己写 |
| LLM 流式输出 | **完美匹配** | 杀鸡用牛刀 |

**结论：** LLM 流式回复用 SSE，WebSocket 留给需要服务端主动推送的场景。

---

## SSE 断线重连机制

服务端每条消息带 `id`：
```
id: 42
data: token内容
```

断线后浏览器自动重连，带请求头 `Last-Event-ID: 42`，服务端从 42 之后补发。

**流状态机：** `pending | streaming | completed | error`  
重连后先查状态，再决定是回放 token 还是直接拉完整消息。

---

## 流式响应的 chunk 结构

```
chunk 1:  delta={role:"assistant", content:""}   finish_reason=None   ← 开头
chunk 2:  delta={content:"你好"}                 finish_reason=None   ← 内容
...
chunk N:  delta={content:""}                     finish_reason="stop" ← 结束
```

finish_reason 取值：
- `"stop"` — 正常结束
- `"tool_calls"` — LLM 决定调用工具
- `"length"` — 被 max_tokens 截断（危险）

---

## 流式 Tool Call 碎片收集

tool call 的 arguments 是分片传输的 JSON 字符串，需要手动拼接：

```python
tool_calls_buffer = {}  # {index: {id, name, arguments}}

for chunk in response:
    delta = chunk.choices[0].delta
    if delta.tool_calls:
        for tc in delta.tool_calls:
            idx = tc.index  # 用 index 做 key（id 只在第一个 chunk 出现）
            if idx not in tool_calls_buffer:
                tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
            if tc.id:
                tool_calls_buffer[idx]["id"] = tc.id
            if tc.function.name:
                tool_calls_buffer[idx]["name"] = tc.function.name
            if tc.function.arguments:
                tool_calls_buffer[idx]["arguments"] += tc.function.arguments  # 拼接！

    if chunk.choices[0].finish_reason == "tool_calls":
        for idx, tc in tool_calls_buffer.items():
            args = json.loads(tc["arguments"])  # 全部到齐才能解析
            print(f"工具调用完成：{tc['name']}，参数：{args}")
```

**为什么用 index 不用 id：** id 只在第一个 chunk 出现，后续为空字符串。index 每个 chunk 都有。

---

## stream=True 与 json_object 的关系

- 技术上不冲突，可以同时使用
- 实践上 json_object 流式没意义：JSON 在最后一个 `}` 前不完整，无法解析
- **结论：** match_skills / generate_resume_advice 用非流式等完整 JSON；对话引导文字用流式

---

## choices 为什么是数组

对应 API 参数 `n`（默认1），可以让 LLM 同时生成多个回答。实际工程里永远用 `choices[0]`，`n>1` 成本翻倍。

---

## yield / 生成器 / 协程

**生成器：** 含 `yield` 的函数，调用返回生成器对象，不立即执行。
每次 `next()` 执行到下一个 `yield`，暂停，保存栈帧（局部变量 + 执行位置）。
函数结束时抛 `StopIteration`，`for` 循环自动捕获停止。

**协程：** 可以主动让出 CPU 的函数（`async/await`）。
`await` = "我在等，让别人先用 CPU"。
FastAPI 基于协程，一个进程可以同时处理几千个 SSE 连接。

---

## FastAPI 架构：递归 → while 循环 + yield

**当前 app.py 的问题：** `send_message` 递归调用，必须等最内层完成才返回，无法在中间 yield token。

**重构方案：**

```python
async def run_agent(messages, context):
    while True:
        tool_calls_buffer = {}
        async for chunk in await call_llm_stream(messages):
            if chunk.content:
                yield chunk.content          # 实时推给客户端
            if chunk.tool_calls:
                collect_fragments(tool_calls_buffer, chunk)

        if not tool_calls_buffer:
            break  # 没有工具调用，结束

        # 执行工具，更新 context 和 messages
        for tc in tool_calls_buffer.values():
            result = execute_tool(tc)
            messages.append(tool_result_message(tc, result))
            context[tc.name] = result

        if context['parse_jd'] and context['parse_profile']:
            messages.append(match_skills_prompt(...))
        # while 继续 → 下一轮 LLM
```

**关键变化：** 递归 → while True；return → yield；同步 → async

---

## 下一步

- 新建 `background/server.py`
- 定义 `ChatRequest` Pydantic 模型（服务端无状态，客户端持有 messages + context）
- 实现 `/chat` SSE 接口
