import os

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"]) as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    duplicates = db.execute("SELECT title FROM tasks GROUP BY title HAVING count(*) > 1").fetchall()
    if duplicates:
        raise SystemExit("В tasks есть повторяющиеся названия - уберите и повторите миграцию: " + ", ".join(row[0] for row in duplicates))
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS tasks_title_key ON tasks (title)")
