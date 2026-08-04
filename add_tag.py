import sqlite3
import argparse

DB_NAME = "ratings.db"

def add_tag(tag, ids_file):
    # Читаем ID из файла
    with open(ids_file) as f:
        ids = [line.strip() for line in f if line.strip()]
    if not ids:
        print("Файл пуст")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for pid in ids:
        # Проверяем, существует ли игрок
        c.execute("SELECT tags FROM players WHERE id = ?", (pid,))
        row = c.fetchone()
        if row is None:
            print(f"ID {pid} не найден в базе, пропускаем")
            continue
        current_tags = row[0] if row[0] else ""
        if tag in current_tags.split(","):
            print(f"ID {pid} уже имеет тег {tag}")
            continue
        new_tags = f"{current_tags},{tag}" if current_tags else tag
        c.execute("UPDATE players SET tags = ? WHERE id = ?", (new_tags, pid))
    conn.commit()
    conn.close()
    print(f"Тег '{tag}' добавлен {len(ids)} игрокам из файла '{ids_file}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tag", help="Название тега, например russia_classical")
    parser.add_argument("ids_file", help="Файл со списком ID (по одному на строку)")
    args = parser.parse_args()
    add_tag(args.tag, args.ids_file)
