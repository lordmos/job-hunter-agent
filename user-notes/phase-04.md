# 课程要求
## 简历定制建议

写一个 generate_resume_advice 函数，接收 match_result（上一步的 JSON），调 LLM，输出：

```
{
  "highlights": ["应该在简历里重点突出的经验"],
  "suggestions": ["具体的修改建议，每条针对一个差距"],
  "keywords": ["应该加进简历的关键词"]
}

```
这次要求你用 DeepSeek 的 JSON Mode——直接让 API 保证返回合法 JSON，不靠 prompt 里说"只返回JSON"。

查一下 DeepSeek 怎么开启 JSON Mode：DeepSeek API 文档，搜 response_format。

## 笔记

### JSON Mode

调用方显式传参控制是否开启，而不是在 send_message 内部猜测：

```python
def send_message(messages, json_mode=False):
    response_format = {"type": "json_object"} if json_mode else {"type": "text"}
```

规则：后续代码要做 `json.loads()` 的地方，调用时传 `json_mode=True`。

**DeepSeek 的强制要求（踩坑）：** 使用 `response_format=json_object` 时，prompt 中必须包含 "json" 关键词，否则 API 直接报错。这和 GPT-4 不同——GPT-4 不报错只是自由发挥字段。所以两个都需要：`response_format` 保证语法，prompt 里的 schema 描述保证字段结构。

### 对话交互（短期 Memory）

- LLM 无状态，每次调用都是全新请求
- 多轮对话 = 把历史消息全部带着重新发（messages 数组持续累积）
- `messages` 必须在循环外初始化，不能是全局变量（多用户污染问题）
- 会话状态（如 context）应作为局部变量传参，不用全局变量

### 工具调用时机是 LLM 决定的

实验验证：用户分两条消息提供技能和 JD，LLM 在只收到技能时没有立刻调 `parse_profile`，等到 JD 也出现后才一起调两个工具。这个行为没有写任何规则，是 LLM 自主判断"什么时候调工具最合理"。这是 Agent 行为的核心体现。

### 什么是 Agent？

**当前做的是"带工具的 LLM 应用"，不是真正的 Agent。**

| | 带工具的 LLM 应用（当前） | Agent（目标） |
|---|---|---|
| 流程编排 | 代码写死：解析JD → 匹配 → 建议 | LLM 自己决定下一步 |
| 工具调用时机 | 程序员决定 | LLM 决定 |
| 循环控制 | 代码控制几轮 | LLM 决定何时停止 |

真正的 Agent 需要一个**通知/驱动机制（ReAct loop）**——把任务交给 LLM，LLM 自主规划步骤、决定工具调用顺序、判断任务完成。这就是第二阶段用 LangGraph 要解决的事。

面试时要能说清楚这个区别。
