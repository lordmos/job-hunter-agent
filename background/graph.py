from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json

# 注意：find_dotenv默认查找'.env'文件，需指定文件名
dotenv_path = find_dotenv(os.path.join(
    os.path.dirname(__file__), '.env.local'))
load_dotenv(dotenv_path)
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


def handle_tool_call(tool_call: dict):
    print("工具调用：", tool_call['function']['name'])
    if tool_call['function']['name'] == "parse_jd":
        args_json = json.loads(tool_call['function']['arguments'])
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
    elif tool_call['function']['name'] == "parse_profile":
        args_json = json.loads(tool_call['function']['arguments'])
        user_skills = args_json.get("user_skills", [])
        return {
            "user_skills": user_skills
        }
    else:
        raise ValueError("未知工具调用")


class State(TypedDict):
    messages: list
    context: dict

# 执行节点:


def node_call_llm(state: State):
    # 不需要处理输入输出，直接调用LLM，返回结果，如果需要tool_calls，LLM会在输出里带上tool_calls字段，后续路由会根据这个字段判断下一步走哪个节点

    current_role = ''
    current_content = ''
    tool_calls_buffer = {}
    message_cache = state['messages']

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
            # yield f"data: {json.dumps({'role': delta.role})}\n\n"
            current_role = delta.role
            current_content = ''
        if delta.content:
            current_content += delta.content
            # yield f"data: {json.dumps({'content': delta.content})}\n\n"
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
            tool_calls_buffer.clear()

        if choice.finish_reason == "stop":
            message_cache.append({
                "role": current_role,
                "content": current_content
            })
    state['messages'] = message_cache
    return state


def node_execute_tools(state: State):
    print("Function called with state:", state)
    ctx = state['context']
    # 这里需要在执行工具调用后，更新一下这两个缓存数据，因为工具调用的时候，这两个数据在业务上就失效了
    ctx.pop('match_result', None)
    ctx.pop('advice_result', None)
    message_cache = state['messages']
    last_message = state['messages'][-1] if state['messages'] else {}

    for tc in last_message.get('tool_calls', []):
        result = handle_tool_call(tc)
        message_cache.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": json.dumps(result)
        })
        state['context'][tc["function"]["name"]] = result
    state['messages'] = message_cache
    return state


def node_match_skills(state: State):
    ctx = state['context']
    prompt = f"""你是一个技术招聘专家。对比候选人档案和职位要求，给出技能匹配分析。
候选人档案：{json.dumps(ctx['parse_profile'], ensure_ascii=False)}
职位要求：{json.dumps(ctx['parse_jd'], ensure_ascii=False)}
输出格式（纯JSON，不要markdown）：
{{"matched_skills": [...], "skill_gaps": [...], "summary": "一句话总结"}}"""

    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)
    ctx['match_result'] = result
    state['context'] = ctx
    return state


def node_generate_resume_advice(state: State):
    ctx = state['context']
    prompt = f"""根据技能匹配分析，给出简历优化建议。
匹配分析：{json.dumps(ctx['match_result'], ensure_ascii=False)}
输出格式（纯JSON，不要markdown）：
{{"highlights": [...], "suggestions": [...], "keywords": [...], "summary": "一句话总结"}}"""

    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)
    ctx['advice_result'] = result
    state['context'] = ctx
    return state

# 执行路由


def route_after_llm(state: State):
    ctx = state['context']
    last_message = state['messages'][-1] if state['messages'] else {}
    if 'tool_calls' in last_message:
        return "node_execute_tools"
    # if 'role' in last_message and last_message['role'] == 'user':
    #     return "node_call_llm"
    return END


def route_after_tools(state: State):
    ctx = state['context']
    if 'parse_jd' in ctx and 'parse_profile' in ctx:
        return "node_match_skills"
    return "node_call_llm"


def build_graph():
    graph = StateGraph(State)
    # Add nodes and edges to the graph
    graph.add_node("node_call_llm", node_call_llm)
    graph.add_node("node_execute_tools", node_execute_tools)
    graph.add_node("node_match_skills", node_match_skills)
    graph.add_node("node_generate_resume_advice", node_generate_resume_advice)

    # Set the entry point of the graph
    graph.set_entry_point("node_call_llm")

    # Add edges between nodes
    graph.add_conditional_edges("node_call_llm", route_after_llm)
    graph.add_conditional_edges("node_execute_tools", route_after_tools)
    graph.add_edge("node_match_skills", "node_generate_resume_advice")
    graph.add_edge("node_generate_resume_advice", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({
        "messages": [
            {"role": "system", "content": "你是一个专注于技术岗位的求职教练。"},
            {"role": "user", "content": "职位：Python后端工程师，要求3年经验，熟悉FastAPI、PostgreSQL、Redis。我的技能：Node.js、TypeScript、Angular、基础SQL"},
        ],
        "context": {}
    })
    print("context keys:", list(result["context"].keys()))
    print("advice_result:", result["context"].get("advice_result"))
