import pandas as pd
from openai import OpenAI

# Подключение к LM Studio
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Функция для получения эмбеддинга текста
def get_embedding(text, model="second-state/Nomic-embed-text-v1.5-Embedding-GGUF"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

# Чтение Excel файла и обработка товаров и их характеристик
def process_xlsx(file_path, columns_to_embed):
    embeddings = []
    
    try:
        # Чтение данных из Excel файла
        df = pd.read_excel(file_path)
        
        for _, row in df.iterrows():
            try:
                # Объединяем все выбранные характеристики товара в один текст
                combined_text = " ".join([str(row[col]) for col in columns_to_embed])
                embedding = get_embedding(combined_text)
                embeddings.append(embedding)
            except KeyError as e:
                print(f"Ошибка: не найден столбец {e}")
    except Exception as e:
        print(f"Не удалось открыть файл: {e}")
    
    # Преобразуем список эмбеддингов в DataFrame для добавления к исходным данным
    embeddings_df = pd.DataFrame(embeddings)
    
    # Добавляем эмбеддинги в исходный DataFrame
    # Назовем столбцы с эмбеддингами как embedding_1, embedding_2, ..., embedding_n
    for i in range(embeddings_df.shape[1]):
        df[f'embedding_{i+1}'] = embeddings_df[i]
    
    # Сохраняем обновленный DataFrame обратно в Excel
    df.to_excel("updated_" + file_path, index=False)

    return df

# Пример использования
xlsx_file_path = "data.xlsx"  # Укажите путь к вашему Excel файлу
columns_to_embed = ["Name", "Code", "Color", "Brands"]  # Укажите правильные имена столбцов

# Обрабатываем файл и добавляем эмбеддинги
df_with_embeddings = process_xlsx(xlsx_file_path, columns_to_embed)

# Печать первых строк обновленного DataFrame для проверки
print(df_with_embeddings.head())
