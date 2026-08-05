import sqlite3
import argparse

DB_NAME = "ratings.db"

def add_match(player_id, control, result, date=None, tournament=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO matches (player_id, control, result, date, tournament)
        VALUES (?, ?, ?, ?, ?)
    ''', (player_id, control, result, date, tournament))
    conn.commit()
    conn.close()
    print(f"Встреча добавлена: игрок {player_id}, контроль {control}, результат {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Добавить личную встречу")
    parser.add_argument("player_id", type=int, help="ФШР ID соперницы")
    parser.add_argument("control", choices=["classic", "rapid", "blitz"], help="Контроль (classic, rapid, blitz)")
    parser.add_argument("result", choices=["win", "draw", "loss"], help="Результат (win - победа дочери, loss - поражение, draw - ничья)")
    parser.add_argument("--date", help="Дата встречи (ГГГГ-ММ-ДД)")
    parser.add_argument("--tournament", help="Название турнира")
    args = parser.parse_args()
    add_match(args.player_id, args.control, args.result, args.date, args.tournament)
