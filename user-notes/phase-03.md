# 课程要求
## 设计技能匹配的 prompt
在 app.py 里写一个 match_skills 函数，接收 parsed_jd（上一步解析出的结构化 JD）和 profile（从 profile.json 读取），调一次 LLM，输出：

1. 匹配的技能（你有且 JD 要求的）
2. 差距（JD 要求但你没有的）
3. 匹配度总结（一句话）

```
def match_skills(parsed_jd, profile):
    prompt = f"""
你是一个技术招聘专家。对比以下候选人档案和职位要求，给出技能匹配分析。

候选人档案：
{json.dumps(profile, ensure_ascii=False)}

职位要求：
{json.dumps(parsed_jd, ensure_ascii=False)}

输出格式（JSON）：
{
  "matched_skills": [...],
  "skill_gaps": [...],
  "summary": "一句话总结"
}
"""
```

注意：这次不用 Function Calling，直接在 user message 里要求 LLM 返回 JSON——这是 Prompt Engineering 控制输出格式的基本手段。

## 笔记

message 中在后面追加system类型消息后，会清除掉最原始的system prompt。

## 挑战
**提问：** LLM 怎么知道 Node.js 经验可以对应 "REST API设计与实现"？ 你的 profile.json 里只写了 "Node.js"，JD 里只写了 "REST API"，这个映射是谁做的？对你来说意味着什么？

**回答：** LLM 在预训练时读过海量代码、文档、技术文章，知道"用 Node.js 写后端" 和 "REST API 开发" 是高度相关的概念。它在做语义推理，不是字符串匹配。这对你意味着一件重要的事：LLM 的推理能力就是你的工具。你不需要自己写规则说"Node.js → 可以做 REST API"，LLM 帮你做了。但这也是风险——它可能做出错误的语义映射，而你发现不了。生产场景下这个风险怎么控制？先记住这个问题，第二阶段讲 RAG 和 Evaluation 时会回来。


