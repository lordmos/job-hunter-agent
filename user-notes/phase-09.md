# Phase 09 — LangGraph 接入 LLM 全流程

## 本阶段目标
在 graph.py 骨架基础上，把所有节点接入真实 DeepSeek LLM，验证完整流程跑通。

---

## 遇到的问题与解决

### 1. handle_tool_call 参数类型不匹配
**问题：** server.py 里 `handle_tool_call` 接收的是 Pydantic 对象（用 `.name` 属性访问），graph.py 里工具调用存的是 dict，用 `.name` 会 AttributeError。

**解决：** graph.py 里统一用 dict，改成 `tc["function"]["name"]` 访问：
```python
def handle_tool_call(tool_call: dict):
    name = tool_call['function']['name']
    args = json.loads(tool_call['function']['arguments'])
```

### 2. result.model_dump() 报错
**问题：** 原来 `handle_tool_call` 返回 Pydantic 对象，写 tool message 时用 `json.dumps(result.model_dump())`。改成返回 dict 之后，`dict` 没有 `.model_dump()` 方法。

**解决：** 直接 `json.dumps(result)` 即可。

**顺带理清楚了三种类型的转换：**
| 类型 | 转换 |
|------|------|
| dict → JSON字符串 | `json.dumps(d)` |
| JSON字符串 → dict | `json.loads(s)` |
| Pydantic → dict | `obj.model_dump()` |
| dict → Pydantic | `Model(**d)` |

### 3. response_format 参数名写错
**问题：** 写成了 `format={"type": "json_object"}`，这不是 OpenAI SDK 的参数名，会被忽略，LLM 可能输出带 markdown 的内容导致 json.loads 失败。

**解决：** 改为 `response_format={"type": "json_object"}`。

### 4. context key 命名不一致
**问题：** `node_match_skills` 写入 `ctx['match_skills_result']`，但 `node_generate_resume_advice` 读 `ctx['match_result']`，KeyError。

**解决：** 统一命名，全部用 `match_result` 和 `advice_result`。

**教训：** key 名一定要在最开始确定好，最好写注释说明每个 key 的含义。

### 5. FastAPI app 误放入 graph.py
**问题：** 从 server.py 复制代码时，把 `app = FastAPI()` 一起带过来了。graph.py 是纯图逻辑，不应该有 FastAPI 实例。

**解决：** 删掉。职责分离：graph.py 只管图，server.py 只管 HTTP 接口。

---

## 架构设计讨论

### 为什么不需要 node_call_llm_json
早期想法：做一个专门解析 LLM JSON 输出的节点，在里面判断当前是 match 阶段还是 advice 阶段。

**问题：** 这又把业务判断逻辑塞回了一个大节点，和原来 server.py 的 while 循环没有本质区别。

**正确做法：** 每个节点自己完整负责。`node_match_skills` 自己构建 prompt、调 LLM、解析结果。节点=一件完整的事。

### 流式 vs 非流式的分工
| 节点 | 调用方式 | 原因 |
|------|---------|------|
| node_call_llm | stream=True | 对话内容需要实时展示给用户 |
| node_match_skills | stream=False | 结构化 JSON，需要完整结果才能解析 |
| node_generate_resume_advice | stream=False | 同上 |

### Supervisor 模式（未来扩展）
当有多个业务图时，可以在 /chat 前加一个 Supervisor 图，根据用户意图路由到不同子图：
```
用户输入 → supervisor → job_hunter_graph / resume_graph / interview_graph
```
目前只有一个图，直接调用即可。

---

## 完整验证

输入一条包含 JD + 个人技能的消息，图自动走完全流程：

```
call_llm
  → tool_calls: parse_jd
execute_tools → (parse_jd 写入 context)
call_llm
  → tool_calls: parse_profile
execute_tools → (parse_profile 写入 context，jd+profile 齐了)
node_match_skills → (match_result 写入 context)
node_generate_resume_advice → (advice_result 写入 context)
END
```

最终 context keys: `['parse_jd', 'parse_profile', 'match_result', 'advice_result']`

---

## 下一步
将 graph.py 改为 async，接入 `graph.astream_events()`，与 FastAPI SSE 对接：
1. `AsyncOpenAI` 替换 `OpenAI`
2. 节点函数改为 `async def`
3. FastAPI `/chat` 用 `astream_events` 消费事件，yield SSE
