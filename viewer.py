import sqlite3
import argparse
from collections import defaultdict
from config import DAUGHTER_ID, TOURNAMENT_DATES

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

def get_start_snapshot(player_id, date_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT classic_fshr, rapid_fshr, blitz_fshr
        FROM ratings_snapshots
        WHERE player_id = ? AND date <= ?
        ORDER BY date DESC LIMIT 1
    ''', (player_id, date_str))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0, 0)

def get_all_matches(player_ids):
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

def print_table(rows, sort_by, top=None, show_fide=False, delta_tag=None):
    if not rows:
        print("Нет данных по заданным фильтрам.")
        return

    if top:
        rows = rows[:top]

    all_ids = [row[0] for row in rows]
    matches_dict = get_all_matches(all_ids)

    # Определяем индекс рейтинга в строке (5-classic, 6-rapid, 7-blitz)
    if sort_by.startswith("classic"):
        main_idx = 5
    elif sort_by.startswith("rapid"):
        main_idx = 6
    else:
        main_idx = 7

    # Если задан delta_tag, получаем дату турнира
    tournament_date = None
    if delta_tag and delta_tag in TOURNAMENT_DATES:
        tournament_date = TOURNAMENT_DATES[delta_tag]

    result_icon = {'win': '🟢', 'draw': '🟡', 'loss': '🔴'}

    # ANSI-цвета для дельты
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

    header = f"{'Место':<5} {'ID':<8} {'Имя':<30} {'Год':<6} {'Рег':<6} {'Рейт':>6} {'Δ':>4} {'Встр':<5}"
    if show_fide:
        header += f" {'ФИДЕ':>8}"
    print(header)
    print("-" * len(header))

    for i, row in enumerate(rows, start=1):
        fshr_id, name, birth, region, tags = row[0], row[1], row[2], row[3], row[4]
        current_rating = row[main_idx]
        fide_rating = row[8] if show_fide else None

        # Дельта с цветом
        delta_str = " · "
        if tournament_date:
            start_ratings = get_start_snapshot(fshr_id, tournament_date)
            start_rating = start_ratings[main_idx - 5]  # 0-classic,1-rapid,2-blitz
            if start_rating:
                diff = current_rating - start_rating
                if diff > 0:
                    delta_str = f"{GREEN}{diff:+4d}{RESET}"
                elif diff < 0:
                    delta_str = f"{RED}{diff:+4d}{RESET}"
                else:
                    delta_str = f"  0 "
            else:
                delta_str = "  n/a"

        # Иконки встреч
        match_results = matches_dict.get(fshr_id, [])
        icons = ''.join(result_icon.get(r, '?') for r in match_results)

        prefix = "🔹 " if fshr_id == DAUGHTER_ID else "  "
        line = f"{prefix}{i:<3} {fshr_id:<8} {name:<30} {birth:<6} {region:<6} {current_rating:>6} {delta_str:>4} {icons:<5}"
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

    # Сводка встреч
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
    parser.add_argument("--delta-tag", default=None, help="Тег турнира для отображения прироста (например, rf_26_blitz)")
    args = parser.parse_args()

    rows = get_latest_snapshots(tag=args.tag, birth_year=args.birth, sort_by=args.sort)
    print_table(rows, sort_by=args.sort, top=args.top, show_fide=args.fide, delta_tag=args.delta_tag)
