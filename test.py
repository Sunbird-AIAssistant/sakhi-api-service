from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
# client.api_key = "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"

stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Say this is a test"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")