from typing import Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from .models.chat_request import ChatRequest, ChatMessage, ParseContext, ParseJDResult, ParseProfileResult

from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json

app = FastAPI()
# 注意：find_dotenv默认查找'.env'文件，需指定文件名
dotenv_path = find_dotenv(os.path.join(
    os.path.dirname(__file__), '.env.local'))
load_dotenv(dotenv_path)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
)

SYSTEM_PROMPT = """
你是一个专注于技术岗位的求职教练。
1. 你需要引导用户提供职位描述。
2. 你需要引导用户提供自己的候选人档案（技能列表）。
3. 如果用户提供了职位描述和候选人档案，你需要分析职位描述中的技能要求和候选人档案的匹配情况。
4. 如果用户需要简历优化，给出简历优化建议。
5. 用户可以多次输入职位描述，你需要针对新提供的职位描述进行分析和建议。
**重要约束:** 你只能回答求职相关问题，其他话题拒绝回答。
"""

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


def handle_tool_call(tool_call_function):
    print("工具调用：", tool_call_function['name'])
    if tool_call_function['name'] == "parse_jd":
        args_json = json.loads(tool_call_function['arguments'])
        job_title = args_json.get("job_title", "")
        required_skills = args_json.get("required_skills", [])
        company = args_json.get("company", "")
        preferred_skills = args_json.get("preferred_skills", [])
        experience_years = args_json.get("experience_years", 0)
        return ParseJDResult(
            job_title=job_title,
            company=company,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=experience_years
        )
    elif tool_call_function['name'] == "parse_profile":
        args_json = json.loads(tool_call_function['arguments'])
        user_skills = args_json.get("user_skills", [])
        return ParseProfileResult(user_skills=user_skills)
    else:
        raise ValueError("未知工具调用")


async def run_agent(messages: list[dict], context: dict):
    message_cache = list(messages)
    need_resume_advice = False
    current_role = ''
    current_content = ''
    while True:
        tool_calls_buffer = {}
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL"),
            tools=tools,
            messages=message_cache,
            stream=True,
        )

        for chunk in response:
            choice = chunk.choices[0]
            delta = choice.delta
            if delta.role:
                yield f"data: {json.dumps({'role': delta.role})}\n\n"
                current_role = delta.role
                current_content = ''
            if delta.content:
                current_content += delta.content
                yield f"data: {json.dumps({'content': delta.content})}\n\n"
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index  # 哪个 tool call（支持并行调用）
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls_buffer[idx]["id"] = tc.id
                    if tc.function.name:
                        tool_calls_buffer[idx]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls_buffer[idx]["arguments"] += tc.function.arguments

            if choice.finish_reason == "tool_calls":
                message_cache.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]}
                    } for tc in tool_calls_buffer.values()]
                })
                for idx, tc in tool_calls_buffer.items():
                    result = handle_tool_call(tc)
                    context[tc["name"]] = result.model_dump()
                    yield f"data: {json.dumps({
                        'tool_call_id': tc['id'],
                        'result': result.model_dump(),
                        'tool_name': tc['name']
                    })}\n\n"
                    message_cache.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(
                            result.model_dump())  # 将工具结果转换为字符串形式
                    })
                tool_calls_buffer.clear()
                if 'parse_jd' in context and 'parse_profile' in context:
                    jd_info = context['parse_jd']
                    profile_info = context['parse_profile']
                    # 简单的匹配分析逻辑
                    message_cache.append({
                        "role": "user",
                        "content": match_skills(jd_info, profile_info)
                    })
                    need_resume_advice = True

            if choice.finish_reason == "stop":
                message_cache.append({
                    "role": current_role,
                    "content": current_content
                })
                if need_resume_advice:
                    match_skills_result = message_cache[-1]['content']
                    message_cache.append({
                        "role": "user",
                        "content": generate_resume_advice(match_skills_result)
                    })
                    need_resume_advice = False
                else:
                    return


@app.post("/chat")
async def chat(request: ChatRequest):
    working_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + [m.model_dump(exclude_none=True) for m in request.messages if m.role != "system"]
    context = {}
    for m in working_messages:
        if 'tool_name' in m and 'result' in m:
            context[m['tool_name']] = json.loads(m['result'])
            break
    return StreamingResponse(
        run_agent(working_messages, context),
        media_type="text/event-stream"
    )
