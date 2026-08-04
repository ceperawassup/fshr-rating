import sqlite3
import argparse
from config import DAUGHTER_ID

DB_NAME = "ratings.db"

def get_latest_snapshots(tag=None, birth_year=None, sort_by="classic_fshr"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Базовый запрос: последний снапшот для каждого игрока
    query = '''
        SELECT p.id, p.name, p.birth_year, p.region_code, p.tags,
               s.classic_fshr, s.rapid_fshr, s.blitz_fshr,
               s.classic_fide, s.rapid_fide, s.blitz_fide
        FROM players p
        JOIN ratings_snapshots s ON p.id = s.player_id
        WHERE s.date = (SELECT MAX(date) FROM ratings_snapshots WHERE player_id = p.id)
    '''
    conditions = []
    params = []

    if tag:
        # Поддержка нескольких тегов через запятую
        tags = [t.strip() for t in tag.split(",")]
        tag_conditions = []
        for t in tags:
            tag_conditions.append("p.tags LIKE ?")
            params.append(f"%{t}%")
        conditions.append("(" + " OR ".join(tag_conditions) + ")")

    if birth_year:
        if "-" in birth_year:
            start, end = birth_year.split("-")
            conditions.append("p.birth_year BETWEEN ? AND ?")
            params.append(int(start))
            params.append(int(end))
        else:
            conditions.append("p.birth_year = ?")
            params.append(int(birth_year))

    if conditions:
        query += " AND " + " AND ".join(conditions)

    # Сортировка — теперь явно указываем s.column
    sort_map = {
        "classic_fshr": "s.classic_fshr",
        "rapid_fshr": "s.rapid_fshr",
        "blitz_fshr": "s.blitz_fshr",
        "classic_fide": "s.classic_fide",
        "rapid_fide": "s.rapid_fide",
        "blitz_fide": "s.blitz_fide",
    }
    sort_column = sort_map.get(sort_by, "s.classic_fshr")
    query += f" ORDER BY {sort_column} DESC"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def print_table(rows, sort_by, top=None, show_fide=False):
    if not rows:
        print("Нет данных по заданным фильтрам.")
        return

    if top:
        rows = rows[:top]

    # Индексы колонок в возвращаемом кортеже:
    # 0-id, 1-name, 2-birth, 3-region, 4-tags,
    # 5-classic_fshr, 6-rapid_fshr, 7-blitz_fshr,
    # 8-classic_fide, 9-rapid_fide, 10-blitz_fide
    if sort_by.startswith("classic"):
        main_idx = 5
        fide_idx = 8
    elif sort_by.startswith("rapid"):
        main_idx = 6
        fide_idx = 9
    else:  # blitz
        main_idx = 7
        fide_idx = 10

    header = f"{'Место':<5} {'ФШР ID':<8} {'Имя':<30} {'Год':<6} {'Рег':<6} {'Рейтинг':>8}"
    if show_fide:
        header += f" {'ФИДЕ':>8}"
    print(header)
    print("-" * len(header))

    for i, row in enumerate(rows, start=1):
        fshr_id, name, birth, region, tags = row[0], row[1], row[2], row[3], row[4]
        main_rating = row[main_idx]
        fide_rating = row[fide_idx] if show_fide else None

        is_daughter = (fshr_id == DAUGHTER_ID)
        prefix = "🔹 " if is_daughter else "  "
        line = f"{prefix}{i:<3} {fshr_id:<8} {name:<30} {birth:<6} {region:<6} {main_rating:>8}"
        if show_fide:
            line += f" {fide_rating:>8}"
        print(line)

    # Поиск дочери в списке
    daughter_row = next((r for r in rows if r[0] == DAUGHTER_ID), None)
    if daughter_row:
        position = rows.index(daughter_row) + 1
        print(f"\n🔹 Алёна Никитина находится на {position}-м месте из {len(rows)} участниц.")
    else:
        print("\nАлёна Никитина не найдена в выборке (возможно, не участвовала или нет данных).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Просмотр рейтингов ФШР")
    parser.add_argument("--tag", default=None, help="Фильтр по тегу, например szfo_classical или несколько через запятую")
    parser.add_argument("--birth", default=None, help="Год рождения или диапазон, например 2015 или 2015-2016")
    parser.add_argument("--sort", default="classic_fshr", choices=["classic_fshr", "rapid_fshr", "blitz_fshr"],
                        help="По какому рейтингу сортировать")
    parser.add_argument("--top", type=int, default=None, help="Показать только N лучших")
    parser.add_argument("--fide", action="store_true", help="Показывать также рейтинг ФИДЕ")
    args = parser.parse_args()

    rows = get_latest_snapshots(tag=args.tag, birth_year=args.birth, sort_by=args.sort)
    print_table(rows, sort_by=args.sort, top=args.top, show_fide=args.fide)
