from dotenv import dotenv_values, load_dotenv
from openai import OpenAI

load_dotenv()  # reads variables from a .env file and sets them in os.environ
config = dotenv_values(".env.local")

client = OpenAI(
    api_key=config["DEEPSEEK_API_KEY"],
    base_url=config["DEEPSEEK_BASE_URL"],
)

response = client.chat.completions.create(
    model=config["DEEPSEEK_MODEL"],
    messages=[
        {
            "role": "system",
            "content": "你是一个专注于技术岗位的求职教练。规则：1. 只回答求职相关问题，其他话题拒绝回答；2. 每个建议必须给出具体行动步骤；3. 回复不超过 200 字。",
        },
        {
            "role": "user",
            "content": "你能给我讲个故事吗？",
        }
    ],
)

print(response.choices[0].message.content)
