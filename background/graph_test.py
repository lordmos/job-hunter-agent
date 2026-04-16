from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    messages: list
    context: dict

# 执行节点:


def node_call_llm(state: State):
    # 不需要处理输入输出，直接调用LLM，返回结果，如果需要tool_calls，LLM会在输出里带上tool_calls字段，后续路由会根据这个字段判断下一步走哪个节点
    print("Calling LLM :", state)
    return state


def node_execute_tools(state: State):
    print("Function called with state:", state)
    ctx = state['context']
    # 这里需要在执行工具调用后，更新一下这两个缓存数据，因为工具调用的时候，这两个数据在业务上就失效了
    ctx.pop('match_skills_result', None)
    ctx.pop('generate_resume_advice_result', None)
    return state


def node_match_skills(state: State):
    print("Matching skills with state:", state)
    return state


def node_generate_resume_advice(state: State):
    print("Generating resume advice with state:", state)
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

app = graph.compile()

result = app.invoke({"messages": ["hi"]})

print(result)
