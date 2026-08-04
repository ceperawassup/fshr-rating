import sqlite3
import openpyxl
from datetime import date, datetime
import argparse

DB_NAME = "ratings.db"

def update_ratings(xlsx_file, snapshot_date, add_new=False):
    wb = openpyxl.load_workbook(xlsx_file)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        print("Файл пуст")
        return

    headers = rows[0]
    print(f"Заголовки: {headers}")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = snapshot_date or date.today().isoformat()

    updated = 0
    new_players = 0
    skipped = 0
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        fshr_id = int(row[0])
        # Проверяем существование игрока
        c.execute("SELECT id FROM players WHERE id = ?", (fshr_id,))
        exists = c.fetchone() is not None

        # Извлекаем рейтинги (индексы как в import_list.py)
        fide_id = int(row[1]) if row[1] else 0
        region = int(row[2]) if row[2] else 0
        name = row[3].strip() if row[3] else ""
        birth = int(row[4]) if row[4] else 0
        rank = str(row[5]).strip() if row[5] else ""
        classic_fshr = int(row[6]) if row[6] else 0
        classic_fide = int(row[7]) if row[7] else 0
        rapid_fshr = int(row[8]) if row[8] else 0
        rapid_fide = int(row[9]) if row[9] else 0
        blitz_fshr = int(row[10]) if row[10] else 0
        blitz_fide = int(row[11]) if row[11] else 0

        if exists:
            # Добавляем снапшот
            c.execute('''
                INSERT OR REPLACE INTO ratings_snapshots
                (player_id, date, classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fshr_id, today, classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide))
            updated += 1
        else:
            if add_new:
                # Добавляем нового игрока
                c.execute('''
                    INSERT OR REPLACE INTO players
                    (id, fide_id, region_code, name, birth_year, rank,
                     classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fshr_id, fide_id, region, name, birth, rank,
                      classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide))
                # И сразу первый снапшот
                c.execute('''
                    INSERT OR REPLACE INTO ratings_snapshots
                    (player_id, date, classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fshr_id, today, classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide))
                new_players += 1
                updated += 1
            else:
                skipped += 1

    conn.commit()
    conn.close()
    print(f"Готово: обновлено снапшотов: {updated}")
    if new_players > 0:
        print(f"  из них новых игроков: {new_players}")
    if skipped > 0:
        print(f"  пропущено неизвестных ID: {skipped}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Обновление рейтингов из XLSX")
    parser.add_argument("xlsx_file", help="Путь к XLSX-файлу")
    parser.add_argument("--date", default=None, help="Дата снимка в формате YYYY-MM-DD (по умолчанию сегодня)")
    parser.add_argument("--add-new", action="store_true", help="Добавлять новых игроков, если их нет в базе")
    args = parser.parse_args()
    update_ratings(args.xlsx_file, args.date, args.add_new)
