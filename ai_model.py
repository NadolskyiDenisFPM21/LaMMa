from openai import OpenAI

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")


history = [
    {"role": "system", "content": "Отвечай на русском языке"}
]



def get_completion(query):
    history.append({"role": "user", "content": query})
    completion = client.chat.completions.create(
        model="LM Studio Community/Meta-Llama-3-8B-Instruct-GGUF",
        messages=history,
        temperature=0.,
        stream=True,
    )

    new_message = {"role": "assistant", "content": ""}
    
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            new_message["content"] += chunk.choices[0].delta.content

    history.append(new_message)
    return new_message



# if __name__ == "__main__":
#     data = '''Товар: Mottura Art. 54797TBDR56 Замок 4-риг з засувкою і допом замком під євроциліндр (без накладок), Код: 20764, Цена: 104.2
# Товар: Mottura Art. 54797TBSR56 Замок 4-риг із засувкою, і допом замком під євроциліндр (без накладок), Код: 20765, Цена: 104.2
# Товар: Замок для дверей Mottura Art. 84971S8B0B 4 - ригеля з засувкою, під циліндр, під тяги лівий, Код: 64575, Цена: 79.3
# Товар: Замок для дверей Mottura Art. 84971D8B0B 4 - ригеля з засувкою, під циліндр, під тяги правий, Код: 64462, Цена: 79.3
# Товар: Mottura Art. 40751420053 Замок 1-риг. малий (без накладок), Код: 50326, Цена: 43.55
# Товар: Mottura Art.  3D787L80005CS Замок 4-риг з засувом і доп. замком під євроциліндр лівий складний ключ, Код: 58685, Цена: 432.95
# Товар: Mottura Art. 3D787R80005CS Замок 4-риг з засувом і доп. замком під євроциліндр правий складаний ключ, Код: 58684, Цена: 432.95
# Товар: Mottura Art. 52771DM2856 (TSBM) Замок 4-риг з засув, під тяги (без накладок), Код: 20767, Цена: 70.0
# Товар: Mottura Art. 3D771L80005CS Замок 4-риг з засувом під тяги лівий складаний ключ, Код: 58683, Цена: 369.8
# Товар: Mottura Art. 85971D28T Замок 4-риг з зас., Під циліндр, під тяги, Код: 10291, Цена: 66.9'''
#     print(get_completion("Замки без накладок", data))