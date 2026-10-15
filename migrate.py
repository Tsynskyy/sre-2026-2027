import os

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"]) as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL UNIQUE,
            status VARCHAR(10) NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'done'))
        )
    """)
