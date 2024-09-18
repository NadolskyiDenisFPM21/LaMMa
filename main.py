# Example: reuse your existing OpenAI setup
from openai import OpenAI

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

messages=[
  ]



question = input('Введіть питання:\n')

messages.append({"role": "user", "content": question})


completion = client.chat.completions.create(
  model="LM Studio Community/Meta-Llama-3-8B-Instruct-GGUF",
  messages=messages,
  temperature=0.7,
)


print(completion.choices[0].message)