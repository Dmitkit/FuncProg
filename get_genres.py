import json

def extract_genres_from_json(filepath):
    # Читаем JSON-файл
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Извлекаем жанры
    genres = {book["genre"] for book in data if "genre" in book}
    
    # Преобразуем множество в отсортированный список
    return sorted(genres)


# Основная программа
if __name__ == "__main__":
    filepath = "books.json"  # Замените на путь к вашему JSON-файлу
    genres = extract_genres_from_json(filepath)
    
    print("Список жанров:")
    for genre in genres:
        print(f"- {genre}")
