import sqlite3
import argparse
import openpyxl

DB_NAME = "ratings.db"

def import_snapshot_xlsx(filename, date_str, control):
    wb = openpyxl.load_workbook(filename)
    ws = wb.active
    # Данные начинаются с 3-й строки (1-я — "Стартовый список", 2-я — заголовки столбцов)
    rows = list(ws.iter_rows(min_row=3, values_only=True))
    if not rows:
        print("Файл пуст или не содержит данных после заголовков")
        return

    entries = []
    for row in rows:
        if not row or len(row) < 5:
            continue
        # ID (ИН) в колонке D (индекс 3), рейтинг в колонке E (индекс 4)
        player_id = row[3]
        rating = row[4]
        try:
            player_id = int(player_id)
            rating = int(rating)
        except (ValueError, TypeError):
            continue
        entries.append((player_id, rating))

    if not entries:
        print("Не найдено записей в файле.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Определяем, какую колонку заполнять
    col = f'{control}_fshr'

    for player_id, rating in entries:
        c.execute(f'''
            INSERT INTO ratings_snapshots (player_id, date, {col})
            VALUES (?, ?, ?)
            ON CONFLICT(player_id, date) DO UPDATE SET {col}=excluded.{col}
        ''', (player_id, date_str, rating))

    conn.commit()
    conn.close()
    print(f"Импортировано {len(entries)} записей для {control} на {date_str}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Импорт стартовых рейтингов из XLSX")
    parser.add_argument("filename", help="Путь к XLSX-файлу")
    parser.add_argument("date", help="Дата турнира YYYY-MM-DD")
    parser.add_argument("control", choices=["classic","rapid","blitz"], help="Контроль")
    args = parser.parse_args()
    import_snapshot_xlsx(args.filename, args.date, args.control)
