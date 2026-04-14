# 课程要求
## 对话交互（短期 Memory）

目标是把现在的脚本改成真正的多轮对话——用户可以连续输入，Agent 记住上下文。

核心就是一个循环：

```

while True:
    user_input = input("你: ")
    if user_input.lower() in ["exit", "quit", "退出"]:
        break
    # 追加到 messages，调 LLM，打印回复


```

设计建议：main() 改成一个 while True 循环，messages 在循环外初始化（持续累积上下文），每轮用户输入后调 send_message，打印最终回复。