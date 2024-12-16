import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import json


# Глобальная переменная для хранения данных о книгах
library_data = []

# Доступные жанры
AVAILABLE_GENRES = [
    "Adventure",
    "Children's Literature",
    "Classic Literature",
    "Fantasy",
    "Mystery",
    "Non-Fiction",
    "Romance",
    "Science Fiction",
]


# Загрузка данных из файла
def parse_json_to_dataframe(filepath):
    global library_data
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    library_data = pd.json_normalize(raw_data)


# Получение предпочтений пользователя
def extract_user_inputs():
    selected_genres = [genre for genre, var in genre_vars.items() if var.get()]
    author_list = [a.strip() for a in author_input.get().split(",") if a.strip()]
    search_terms = [k.strip() for k in keyword_input.get().split(",") if k.strip()]
    year = year_input.get()
    year = int(year) if year else None
    return {
        "genres": selected_genres,
        "authors": author_list,
        "terms": search_terms,
        "year_limit": year,
        "filters": {
            "only_genres": only_genres_var.get(),
            "after_year": after_year_var.get(),
        },
        "sort_by": sort_option.get()
    }


# Преобразование имени автора
def simplify_author_name(full_name):
    if not full_name or not full_name.strip():
        return ""
    return full_name.strip().split()[-1].lower()


# Подсчёт релевантности для книги
def compute_match_score(book_row, preferences):
    score = 0

    # Проверка жанра
    if book_row["genre"] in preferences["genres"]:
        score += 3

    # Проверка авторов
    book_authors = [simplify_author_name(a) for a in book_row.get("author", [])]
    for user_author in preferences["authors"]:
        user_author_normalized = simplify_author_name(user_author)
        if any(user_author_normalized in author for author in book_authors):
            score += 5

    # Проверка ключевых слов
    if any(term.lower() in book_row["description"].lower() for term in preferences["terms"]):
        score += 2

    # Учет года с допуском ±10 лет
    if preferences["year_limit"]:
        book_year = book_row["first_publish_year"]
        if book_year and abs(book_year - preferences["year_limit"]) <= 10:
            score += 4

    return score


# Фильтрация и сортировка книг
def filter_books(preferences):
    filtered_data = library_data.copy()

    # Фильтрация по году, если включен соответствующий чекбокс
    if preferences["filters"]["after_year"] and preferences["year_limit"]:
        filtered_data = filtered_data[filtered_data["first_publish_year"] > preferences["year_limit"]]

    # Фильтрация по жанрам
    if preferences["filters"]["only_genres"] and preferences["genres"]:
        filtered_data = filtered_data[filtered_data["genre"].isin(preferences["genres"])]

    # Вычисление рейтинга
    filtered_data["score"] = filtered_data.apply(lambda row: compute_match_score(row, preferences), axis=1)

    # Фильтрация книг с минимальным рейтингом
    filtered_data = filtered_data[filtered_data["score"] > 2]

    # Сортировка
    if preferences["sort_by"] == "Рейтинг":
        filtered_data = filtered_data.sort_values(by="score", ascending=False)
    elif preferences["sort_by"] == "Алфавит":
        filtered_data = filtered_data.sort_values(by="title", ascending=True)
    elif preferences["sort_by"] == "Год публикации":
        filtered_data = filtered_data.sort_values(by="first_publish_year", ascending=True)

    return filtered_data


# Отображение списка подходящих книг
def show_results(filtered_data):
    result_display.delete(1.0, tk.END)

    if filtered_data.empty:
        messagebox.showinfo("Результаты", "Не найдено подходящих книг.")
        return

    for idx, book in filtered_data.iterrows():
        details = f"Рейтинг: {book['score']} - Название: {book['title']}\n"
        details += f"Автор(ы): {', '.join(book['author'])}\n"
        details += f"Жанр: {book['genre']}, Год: {book['first_publish_year']}\n"
        details += f"Описание: {book['description'][:300]}...\n"
        details += "-" * 40 + "\n\n"
        result_display.insert(tk.END, details)


# Сохранение результата в файл
def save_results_to_file(filtered_data):
    if filtered_data.empty:
        messagebox.showwarning("Ошибка", "Нет данных для сохранения.")
        return

    output_data = filtered_data[
        ["title", "author", "genre", "first_publish_year", "description", "score"]].to_dict(orient="records")
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    messagebox.showinfo("Успех", "Данные успешно сохранены в output.json")


# Обработка кнопки рекомендаций
def handle_recommendation():
    preferences = extract_user_inputs()
    results = filter_books(preferences)
    show_results(results)


# Обработка кнопки сохранения
def handle_saving():
    preferences = extract_user_inputs()
    results = filter_books(preferences)
    save_results_to_file(results)


# Основная программа
def launch_application():
    filepath = "books.json"
    parse_json_to_dataframe(filepath)

    app_window = tk.Tk()
    app_window.title("Книжный помощник")

    tk.Label(app_window, text="Выберите жанры:").pack(padx=10, pady=5)

    global genre_vars
    genre_vars = {}
    for genre in AVAILABLE_GENRES:
        var = tk.BooleanVar()
        tk.Checkbutton(app_window, text=genre, variable=var).pack(anchor="w")
        genre_vars[genre] = var

    tk.Label(app_window, text="Авторы:").pack(padx=10, pady=5)
    global author_input
    author_input = tk.Entry(app_window, width=50)
    author_input.pack(padx=10, pady=5)

    tk.Label(app_window, text="Ключевые слова:").pack(padx=10, pady=5)
    global keyword_input
    keyword_input = tk.Entry(app_window, width=50)
    keyword_input.pack(padx=10, pady=5)

    tk.Label(app_window, text="Год публикации:").pack(padx=10, pady=5)
    global year_input
    year_input = tk.Entry(app_window, width=50)
    year_input.pack(padx=10, pady=5)

    # Чекбоксы для фильтрации
    global only_genres_var, after_year_var
    only_genres_var = tk.BooleanVar()
    after_year_var = tk.BooleanVar()

    tk.Checkbutton(app_window, text="Только указанные жанры", variable=only_genres_var).pack(padx=10, pady=5)
    tk.Checkbutton(app_window, text="Только книги после указанного года", variable=after_year_var).pack(padx=10, pady=5)

    # Сортировка
    global sort_option
    sort_option = tk.StringVar(value="Рейтинг")
    tk.Label(app_window, text="Сортировка:").pack(padx=10, pady=5)
    sort_menu = ttk.Combobox(app_window, textvariable=sort_option, values=["Рейтинг", "Алфавит", "Год публикации"])
    sort_menu.pack(padx=10, pady=5)

    recommend_btn = tk.Button(app_window, text="Показать книги", command=handle_recommendation)
    recommend_btn.pack(padx=10, pady=20)

    save_btn = tk.Button(app_window, text="Сохранить в файл", command=handle_saving)
    save_btn.pack(padx=10, pady=5)

    text_frame = tk.Frame(app_window)
    text_frame.pack(padx=10, pady=5)

    global result_display
    result_display = tk.Text(text_frame, height=20, width=80)
    result_display.pack(side="left", fill="both", expand=True)

    scroll_bar = tk.Scrollbar(text_frame, orient="vertical", command=result_display.yview)
    scroll_bar.pack(side="right", fill="y")
    result_display.config(yscrollcommand=scroll_bar.set)

    app_window.mainloop()


if __name__ == "__main__":
    launch_application()
