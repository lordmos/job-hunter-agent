# 课程要求：

## 使用function calling，改造 app.py，参考下方骨架，实现整个流程：`用户输入 JD → 第一次调 LLM（附带 parse_jd 工具定义）→ LLM 返回 tool_call → Agent 执行解析 → 第二次调 LLM（附带结果）→ 返回结构化输出`

```
# 第一步：定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "parse_jd",
            "description": "从职位描述中提取结构化信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_title": {"type": "string", "description": "职位名称"},
                    "company": {"type": "string", "description": "公司名称"},
                    "required_skills": {"type": "array", "items": {"type": "string"}, "description": "必须具备的技能"},
                    "preferred_skills": {"type": "array", "items": {"type": "string"}, "description": "加分项技能"},
                    "experience_years": {"type": "integer", "description": "要求的工作年限"}
                },
                "required": ["job_title", "required_skills"]
            }
        }
    }
]

# 第二步：第一次调 LLM
# 第三步：检测 LLM 是否返回 tool_call
# 第四步：执行工具（这里直接拿参数，不用真正调外部 API）
# 第五步：第二次调 LLM，附带工具结果
```

## 遇到的问题

- 对文档确实不熟悉，注意不要使用responses的文档，而是使用chat completions。DeepSeek用的是后者。
- 使用VSCode Debugger时遇到的问题：需要通过`find_dotenv`进行加载，否则找不到对应的环境变量文件。

```

from dotenv import load_dotenv, find_dotenv
import json

dotenv_path = find_dotenv('.env.local')  # 注意：find_dotenv默认查找'.env'文件，需指定文件名
success = load_dotenv(dotenv_path)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
)


```