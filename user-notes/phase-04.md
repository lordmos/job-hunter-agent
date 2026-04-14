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

### 什么是 Agent？

**当前做的是"带工具的 LLM 应用"，不是真正的 Agent。**

| | 带工具的 LLM 应用（当前） | Agent（目标） |
|---|---|---|
| 流程编排 | 代码写死：解析JD → 匹配 → 建议 | LLM 自己决定下一步 |
| 工具调用时机 | 程序员决定 | LLM 决定 |
| 循环控制 | 代码控制几轮 | LLM 决定何时停止 |

真正的 Agent 需要一个**通知/驱动机制**——把任务交给 LLM，LLM 自主规划步骤、决定工具调用顺序、判断任务完成。这就是第二阶段用 LangGraph 要解决的事。

面试时要能说清楚这个区别。
