# JobHunter Agent — 教练进度记录

## 当前阶段
第一阶段（第 1-2 周）— MVP 能跑

## 学员背景
- 全栈工程师，主要写 JS/TS（React/Node）
- Python 基本没写过
- 已有 DeepSeek API Key

## 已完成
- [x] 环境确认：Python 3.14 + pip 26（macOS）
- [x] 项目结构：`background/` 目录，含 app.py、requirements.txt、.env.local
- [x] 依赖安装：openai、fastapi、python-dotenv
- [x] 首次 API 调通：DeepSeek Chat Completions API 成功返回
- [x] 学习 messages 角色：system / user / assistant
- [x] 实验 system prompt：理解了 prompt 需要明确规则和边界，不是"客气聊天"

## 待修复
- [x] `.gitignroe` 拼写错误 → 已修复为 `.gitignore`

## 下一步
- 进入 JD 解析器功能（Tool Use / Function Calling）
- 学员需阅读 OpenAI Function Calling 文档
- 在 app.py 中定义 parse_jd 函数签名并跑通

## MVP 功能清单
1. JD 解析器（Tool Use）
2. 技能匹配（Prompt Engineering）
3. 简历定制建议（结构化输出）
4. 对话交互（短期 Memory）
