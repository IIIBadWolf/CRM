import pandas as pd
import re
from rapidfuzz import fuzz
import pdfplumber


# =============== 1. Чтение Excel или PDF =====================
def read_supplier_file(path):
    """
    Определяет тип файла и возвращает DataFrame поставщика.
    PDF → конвертируется в таблицу автоматически.
    """
    path = str(path).lower()

    if path.endswith(".pdf"):
        return read_pdf_as_df(path)

    if path.endswith(".xls") or path.endswith(".xlsx"):
        return pd.read_excel(path)

    raise ValueError("Неподдерживаемый формат файла")


# =============== PDF обработка ======================
def read_pdf_as_df(path):
    tables = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                table = page.extract_table()
                if table:
                    tables.append(pd.DataFrame(table))
            except:
                pass

    if not tables:
        raise ValueError("PDF не содержит табличных данных")

    df = pd.concat(tables, ignore_index=True)

    # первая строка — заголовок
    df.columns = df.iloc[0]
    df = df[1:]

    return df


# =============== 2. Удаление строк с итогами ======================
def remove_totals_rows(df):
    """
    Убираем строки:
    - где только суммы
    - где отсутствует наименование
    - где встречаются слова ИТОГО, ВСЕГО, TOTAL
    """

    if df.empty:
        return df

    cols = list(df.columns)

    # Основная колонка для проверки — первая
    name_col = cols[0]

    cleaned = df[
        df[name_col].notna() &
        df[name_col].astype(str).str.strip().ne("") &
        ~df[name_col].astype(str).str.upper().str.contains("ИТОГО|ВСЕГО|TOTAL")
    ]

    return cleaned


# =============== 3. Очистка данных ==============================
def clean_supplier_df(df):
    """
    Приводим данные поставщика к нормальному виду:
    - удаляем пустые строки
    - убираем повторяющиеся заголовки
    - очищаем пробелы
    """

    df = df.dropna(how="all")
    df = df.drop_duplicates()

    # убираем строки, где название похоже на заголовки
    header_words = ["наим", "кол", "цена", "ед", "сум"]
    first_col = df.columns[0]

    def row_is_header(val):
        if not isinstance(val, str):
            return False
        val = val.lower()
        return any(w in val for w in header_words)

    df = df[~df[first_col].apply(row_is_header)]

    # чистим названия
    df[first_col] = df[first_col].astype(str).apply(lambda x: x.strip())

    return df


# =============== 4. Автоматическое сопоставление колонок ==================
def map_columns_by_keywords(df):
    """
    Определяем логические колонки по тексту:
        name → наименование
        qty  → количество
        price → цена
        sum → сумма
    """

    keywords = {
        "name": ["наим", "товар", "продукт"],
        "qty": ["кол", "кол-во", "шт"],
        "price": ["цена", "руб", "закуп"],
        "sum": ["сум", "итог"]
    }

    columns = list(df.columns)
    mapping = {c: None for c in columns}

    for col in columns:
        cname = str(col).lower()

        for logical, words in keywords.items():
            if any(w in cname for w in words):
                mapping[col] = logical

    return mapping
