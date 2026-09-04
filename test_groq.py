from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("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"))

completion = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {
            "role": "user",
            "content": "Dis juste: Groq fonctionne !"
        }
    ],
    temperature=0.6,
    max_tokens=100,
    stream=True,
)

print("Réponse : ", end="")
for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
print()