from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json

dotenv_path = find_dotenv('.env.local')  # 注意：find_dotenv默认查找'.env'文件，需指定文件名
print("找到的.env.local路径:", dotenv_path)
success = load_dotenv(dotenv_path)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
)

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


def parse_jd(job_title, required_skills, company, preferred_skills, experience_years):
    # 这里是一个简单的示例实现，实际应用中可以使用更复杂的自然语言处理技术
    print(
        f"解析职位描述: {job_title}, {company}, {required_skills}, {preferred_skills}, {experience_years}")
    return {
        "job_title": job_title,
        "company": company,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "experience_years": experience_years
    }


def handle_tool_call(tool_call_function):
    if tool_call_function.name == "parse_jd":
        args_json = json.loads(tool_call_function.arguments)
        print(f"工具调用参数: {args_json}")
        job_title = args_json.get("job_title", "")
        required_skills = args_json.get("required_skills", [])
        company = args_json.get("company", "")
        preferred_skills = args_json.get("preferred_skills", [])
        experience_years = args_json.get("experience_years", 0)
        return parse_jd(job_title, required_skills, company, preferred_skills, experience_years)
    else:
        raise ValueError("未知工具调用")


def send_message(messages):
    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        tools=tools,
        messages=messages,
    )
    response_message = response.choices[0].message
    messages.append(response_message)  # 将模型的回复添加到消息列表中
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            tool_result = handle_tool_call(tool_call.function)
            # 将工具调用结果作为系统消息添加到消息列表中
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)  # 将工具结果转换为字符串形式
            })
        return send_message(messages)  # 继续对话，工具调用后不需要用户输入
    else:
        return messages


def main():
    messages = [
        {
            "role": "system",
            "content": "你是一个专注于技术岗位的求职教练。规则：1. 只回答求职相关问题，其他话题拒绝回答；2. 每个建议必须给出具体行动步骤；3. 回复不超过 200 字。",
        },
    ]
    messages.append({
        "role": "user",
        "content": "请你分析一下这个JD：\n\n职位描述：我们正在寻找一位经验丰富的软件工程师，负责开发和维护我们的核心产品。要求至少3年的相关工作经验，熟悉Python和Django框架，能够设计和实现REST API。加分项包括Docker和Kubernetes的使用经验。"
    })
    response_message = send_message(messages)
    print(response_message[-1].content)  # 打印模型的最终回复


main()
