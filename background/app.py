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

profile_path = 'profile.json'

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
    },
    {
        "type": "function",
        "function": {
            "name": "parse_profile",
            "description": "从候选人档案中提取结构化信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_skills": {"type": "array", "items": {"type": "string"}, "description": "必须具备的技能"},
                },
                "required": ["user_skills"]
            }
        }
    },
]


def handle_tool_call(tool_call_function):
    print("工具调用：", tool_call_function.name)
    if tool_call_function.name == "parse_jd":
        args_json = json.loads(tool_call_function.arguments)
        job_title = args_json.get("job_title", "")
        required_skills = args_json.get("required_skills", [])
        company = args_json.get("company", "")
        preferred_skills = args_json.get("preferred_skills", [])
        experience_years = args_json.get("experience_years", 0)
        return {
            "job_title": job_title,
            "company": company,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "experience_years": experience_years
        }
    elif tool_call_function.name == "parse_profile":
        args_json = json.loads(tool_call_function.arguments)
        user_skills = args_json.get("user_skills", [])
        return {
            "user_skills": user_skills
        }
    else:
        raise ValueError("未知工具调用")


def match_skills(parsed_jd, profile):
    prompt = f"""你是一个技术招聘专家。对比以下候选人档案和职位要求，给出技能匹配分析。
        候选人档案：{json.dumps(profile, ensure_ascii=False)}
        职位要求：{json.dumps(parsed_jd, ensure_ascii=False)}
        输出格式（JSON）：
        {{
                "matched_skills": [...], "skill_gaps": [...], "summary": "一句话总结"
        }}
        """
    return prompt


def generate_resume_advice(match_skills_result):
    prompt = f"""你是一个求职顾问。根据以下技能匹配分析结果，给出简历优化建议。
        技能匹配分析结果：{match_skills_result}
        输出格式（JSON）：
        {{
            "matched_skills": ["已经匹配的技能"],
            "skill_gaps": ["技能差距"],
            "highlights": ["应该在简历里重点突出的经验"],
            "suggestions": ["具体的修改建议，每条针对一个差距"],
            "keywords": ["应该加进简历的关键词"],
            "summary": "一句话总结"
        }}
        """
    return prompt


def send_message(messages, context, json_mode=False):
    format = 'text'
    if json_mode:
        format = 'json_object'
    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        tools=tools,
        messages=messages,
        response_format={
            'type': format
        }
    )
    response_message = response.choices[0].message
    messages.append(response_message)  # 将模型的回复添加到消息列表中
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            tool_result = handle_tool_call(tool_call.function)
            if tool_call.function.name in ['parse_jd', 'parse_profile']:
                context[tool_call.function.name] = tool_result
            # 将工具调用结果作为系统消息添加到消息列表中
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)  # 将工具结果转换为字符串形式
            })
        if context['parse_jd'] and context['parse_profile']:
            messages.append({
                "role": "user",
                "content": match_skills(
                    context['parse_jd'], context['parse_profile'])
            })
            messages = send_message(
                messages, context, json_mode=True)
            match_result = messages[-1].content  # 获取技能匹配分析结果
            messages.append({
                "role": "user",
                "content": generate_resume_advice(match_result)
            })
            return send_message(messages, context, json_mode=True)
        return send_message(messages, context)
    return messages


def main():
    context = {'parse_jd': None, 'parse_profile': None}
    messages = [
        {
            "role": "system",
            "content": """你是一个专注于技术岗位的求职教练。
                1. 你需要引导用户提供职位描述。
                2. 你需要引导用户提供自己的候选人档案（技能列表）。
                3. 如果用户提供了职位描述和候选人档案，你需要分析职位描述中的技能要求和候选人档案的匹配情况。
                4. 如果用户需要简历优化，给出简历优化建议。
                5. 用户可以多次输入职位描述，你需要针对新提供的职位描述进行分析和建议。
                **重要约束:** 你只能回答求职相关问题，其他话题拒绝回答。
            """
        },
        {
            "role": "user",
            "content": "请帮我分析职位描述和你的技能匹配情况，并给出简历优化建议。"
        }
    ]
    messages = send_message(messages, context)
    while True:
        user_input = input(
            "我有什么可以帮你的吗？（输入'exit'或者'quit'或者'退出'退出）：")
        if user_input.lower() in ['exit', 'quit', '退出']:
            break
        user_message = {
            "role": "user",
            "content": user_input
        }
        messages.append(user_message)
        messages = send_message(messages, context)
        print("模型回复：", messages[-1].content)


main()
