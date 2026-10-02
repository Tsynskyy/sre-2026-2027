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
