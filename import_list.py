import sqlite3
import openpyxl
from datetime import date
from config import XLSX_FILE, MIN_CLASSIC, MIN_RAPID, MIN_BLITZ

DB_NAME = "ratings.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            fide_id INTEGER,
            region_code INTEGER,
            name TEXT,
            birth_year INTEGER,
            rank TEXT,
            classic_fshr INTEGER,
            classic_fide INTEGER,
            rapid_fshr INTEGER,
            rapid_fide INTEGER,
            blitz_fshr INTEGER,
            blitz_fide INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ratings_snapshots (
            player_id INTEGER,
            date TEXT,
            classic_fshr INTEGER,
            classic_fide INTEGER,
            rapid_fshr INTEGER,
            rapid_fide INTEGER,
            blitz_fshr INTEGER,
            blitz_fide INTEGER,
            PRIMARY KEY (player_id, date)
        )
    ''')
    conn.commit()
    return conn

def import_from_xlsx():
    wb = openpyxl.load_workbook(XLSX_FILE)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        print("Файл пуст")
        return

    headers = rows[0]
    print(f"Заголовки: {headers}")
    # Ожидаемый порядок столбцов (из вашего примера)
    # Код ФШР, Код ФИДЕ, Регион, ФИО, Год рождения, Разряд, ФШР клс, ФИДЕ клс, ФШР быс, ФИДЕ быс, ФШР блиц, ФИДЕ блиц

    conn = init_db()
    c = conn.cursor()
    today = date.today().isoformat()

    skipped = 0
    imported = 0
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        # Извлекаем значения, заменяя None на пустую строку или 0
        fshr_id = int(row[0])
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

        # Фильтр по минимальным рейтингам
        if (classic_fshr < MIN_CLASSIC and
            rapid_fshr < MIN_RAPID and
            blitz_fshr < MIN_BLITZ):
            skipped += 1
            continue

        # Вставляем или обновляем игрока
        c.execute('''
            INSERT OR REPLACE INTO players
            (id, fide_id, region_code, name, birth_year, rank,
             classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fshr_id, fide_id, region, name, birth, rank,
              classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide))
        imported += 1

        # Создаём первый снапшот (только если есть хотя бы один ненулевой рейтинг)
        if any([classic_fshr, rapid_fshr, blitz_fshr, classic_fide, rapid_fide, blitz_fide]):
            c.execute('''
                INSERT OR REPLACE INTO ratings_snapshots
                (player_id, date, classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fshr_id, today, classic_fshr, classic_fide, rapid_fshr, rapid_fide, blitz_fshr, blitz_fide))

    conn.commit()
    conn.close()
    print(f"Импортировано: {imported} игроков, пропущено по фильтру: {skipped}")

if __name__ == "__main__":
    import_from_xlsx()
