import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import requests
import re

# Функция для получения эмбеддинга текста с использованием Ollama
def get_embedding(text, model="mxbai-embed-large"):
    text = text.replace("\n", " ")
    response = requests.post('http://localhost:11434/api/embeddings', 
                             json={
                                 "model": model,
                                 "prompt": text
                             })
    if response.status_code == 200:
        return response.json()['embedding']
    else:
        raise Exception("Failed to get embedding from Ollama")

def preprocess_text(text):
    # Удаляем специальные символы и приводим к нижнему регистру
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_best_partial_ratio(query, text):
    # Разбиваем текст на слова и находим лучшее частичное совпадение
    words = text.split()
    return max(fuzz.partial_ratio(query, word) for word in words)

def weighted_fuzzy_score(query, text):
    query = preprocess_text(query)
    text = preprocess_text(text)
    
    partial_ratio = fuzz.partial_ratio(query, text)/100

    return partial_ratio

def find_similar_products(user_query, product_embeddings, products_info):
    # Получаем эмбеддинг для пользовательского запроса
    user_embedding = get_embedding(user_query)
    
    # Преобразуем эмбеддинги в массив numpy для удобства расчетов
    product_embeddings = np.array(product_embeddings)
    
    # Рассчитываем косинусное сходство между запросом пользователя и эмбеддингами товаров
    similarities = cosine_similarity([user_embedding], product_embeddings)[0]
    
    # Применяем улучшенный нечеткий поиск к названиям товаров
    fuzzy_results = []
    for idx, sim in enumerate(similarities):
        product_name = products_info.iloc[idx]['Name']
        fuzzy_score = weighted_fuzzy_score(user_query, product_name)
        combined_score = (sim + fuzzy_score)/2  # Комбинированный скор
        fuzzy_results.append((idx, sim, fuzzy_score, combined_score))
    
    # Вычисляем среднее значение комбинированного скора
    max_combined_score = np.max([result[3] for result in fuzzy_results])
    
    # Выбираем результаты выше среднего
    above_average_results = [
        result for result in fuzzy_results if result[3] > max_combined_score*.95
    ]
    
    # Сортируем результаты по комбинированному скору
    top_results = sorted(
        above_average_results,
        key=lambda x: x[3],  # Сортировка по комбинированному скору
        reverse=True
    )
    
    # Возвращаем информацию о наиболее релевантных товарах
    similar_products = [
        (products_info.iloc[idx], combined)
        for idx, sim, fuzzy, combined in top_results
    ]
    
    return similar_products

# Чтение Excel файла с данными о товарах и эмбеддингами
def load_data(file_path):
    # Читаем Excel файл
    df = pd.read_excel(file_path)
    
    # Предполагаем, что эмбеддинги хранятся в отдельных столбцах, например, 'embedding_1', 'embedding_2', ..., 'embedding_n'
    embedding_columns = [col for col in df.columns if col.startswith('embedding')]
    
    # Извлекаем эмбеддинги как массив
    product_embeddings = df[embedding_columns].values
    
    # Информация о товарах
    products_info = df.drop(columns=embedding_columns)  # Удаляем столбцы с эмбеддингами для получения чистой информации о товарах
    
    return products_info, product_embeddings

# Пример использования
xlsx_file_path = "updated_data.xlsx"  # Укажите путь к вашему Excel файлу

# Загрузка данных
products_info, product_embeddings = load_data(xlsx_file_path)

def generate_data(query):
    similar_products = find_similar_products(query, product_embeddings, products_info)
    data = ''
    # Генерация ответа
    for product, similarity in similar_products:
        data += f"Товар: {product['Name']} Код: {product['Code']} Колір: {product['Color']} Ціна: {product['Price']} {product['Currency']}\t{similarity}\n"

    return data

# # Запрос пользователя
# user_query = "Механизм вж 96 мм"
# similar_products = generate_data(user_query)
# print(similar_products)