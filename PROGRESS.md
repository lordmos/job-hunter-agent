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
- [x] `.gitignore` 修复
- [x] JD 解析器：用 Function Calling 实现，流程完整跑通
- [x] 技能匹配：用 Prompt Engineering 实现，输出干净 JSON，匹配结果准确

## 注意事项（踩过的坑）
- OpenAI 有两套 API：Responses API（新）和 Chat Completions API（旧/通用）。DeepSeek 只兼容后者，搜文档时认准 `chat.completions`
- VSCode Debugger 下需用 `find_dotenv('.env.local')` 显式加载环境变量
- `for tool_calls` 循环里不要提前 `return`，否则多工具调用时后续工具会被跳过
- `messages` 不能是全局变量，做成 FastAPI 服务时会多用户污染（待重构）
- 技能匹配 prompt 应用 `user` 消息，不是 `system`；`system` 只在对话开始时设置一次
- `open()` 要用 `with` 语句，避免文件句柄泄漏

## 下一步
- **简历定制建议**：接收技能匹配结果，输出 `highlights`/`suggestions`/`keywords`
- 用 DeepSeek JSON Mode（`response_format`）保证返回合法 JSON，而非靠 prompt 约束

## MVP 功能清单
1. [x] JD 解析器（Tool Use / Function Calling）
2. [ ] 技能匹配（Prompt Engineering）
3. [ ] 简历定制建议（结构化输出）
4. [ ] 对话交互（短期 Memory）
