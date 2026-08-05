import sqlite3
import argparse
from collections import defaultdict
from config import DAUGHTER_ID

DB_NAME = "ratings.db"

def get_latest_snapshots(tag=None, birth_year=None, sort_by="classic_fshr"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

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

def get_all_matches(player_ids):
    """Возвращает словарь {player_id: [result, ...]} для переданных id."""
    if not player_ids:
        return {}
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    placeholders = ','.join(['?']*len(player_ids))
    c.execute(f'SELECT player_id, result FROM matches WHERE player_id IN ({placeholders}) ORDER BY date', player_ids)
    d = defaultdict(list)
    for pid, res in c.fetchall():
        d[pid].append(res)
    conn.close()
    return d

def print_table(rows, sort_by, top=None, show_fide=False):
    if not rows:
        print("Нет данных по заданным фильтрам.")
        return

    if top:
        rows = rows[:top]

    # Собираем все id для запроса встреч
    all_ids = [row[0] for row in rows]
    matches_dict = get_all_matches(all_ids)

    result_icon = {'win': '🟢', 'draw': '🟡', 'loss': '🔴'}

    if sort_by.startswith("classic"):
        main_idx = 5
        fide_idx = 8
    elif sort_by.startswith("rapid"):
        main_idx = 6
        fide_idx = 9
    else:
        main_idx = 7
        fide_idx = 10

    # Заголовок (ширина колонки "Встр" до 5 символов)
    header = f"{'Место':<5} {'ID':<8} {'Имя':<30} {'Год':<6} {'Рег':<6} {'Рейт':>6} {'Встр':<5}"
    if show_fide:
        header += f" {'ФИДЕ':>8}"
    print(header)
    print("-" * len(header))

    for i, row in enumerate(rows, start=1):
        fshr_id, name, birth, region, tags = row[0], row[1], row[2], row[3], row[4]
        main_rating = row[main_idx]
        fide_rating = row[fide_idx] if show_fide else None

        # Иконки встреч
        match_results = matches_dict.get(fshr_id, [])
        icons = ''.join(result_icon.get(r, '?') for r in match_results)

        prefix = "🔹 " if fshr_id == DAUGHTER_ID else "  "
        line = f"{prefix}{i:<3} {fshr_id:<8} {name:<30} {birth:<6} {region:<6} {main_rating:>6} {icons:<5}"
        if show_fide:
            line += f" {fide_rating:>8}"
        print(line)

    # Место дочери
    daughter_row = next((r for r in rows if r[0] == DAUGHTER_ID), None)
    if daughter_row:
        position = rows.index(daughter_row) + 1
        print(f"\n🔹 Алёна Никитина находится на {position}-м месте из {len(rows)} участниц.")
    else:
        print("\nАлёна Никитина не найдена в выборке.")

    # Сводка всех встреч
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*), result FROM matches GROUP BY result')
    stats = {row[1]: row[0] for row in c.fetchall()}
    conn.close()
    if stats:
        print("\nЛичные встречи (всего):")
        print(f"  Побед: {stats.get('win', 0)}, Ничьих: {stats.get('draw', 0)}, Поражений: {stats.get('loss', 0)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Просмотр рейтингов ФШР")
    parser.add_argument("--tag", default=None, help="Фильтр по тегу")
    parser.add_argument("--birth", default=None, help="Год рождения или диапазон")
    parser.add_argument("--sort", default="classic_fshr", choices=["classic_fshr", "rapid_fshr", "blitz_fshr"],
                        help="По какому рейтингу сортировать")
    parser.add_argument("--top", type=int, default=None, help="Показать только N лучших")
    parser.add_argument("--fide", action="store_true", help="Показывать также рейтинг ФИДЕ")
    args = parser.parse_args()

    rows = get_latest_snapshots(tag=args.tag, birth_year=args.birth, sort_by=args.sort)
    print_table(rows, sort_by=args.sort, top=args.top, show_fide=args.fide)
