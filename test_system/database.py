import sqlite3


DB_NAME = "data.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        type TEXT NOT NULL,
        options TEXT,
        correct TEXT NOT NULL,
        points INTEGER NOT NULL DEFAULT 1,
        difficulty TEXT DEFAULT 'medium',
        explanation TEXT DEFAULT '',
        FOREIGN KEY(test_id) REFERENCES tests(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        test_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        duration INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(test_id) REFERENCES tests(id)
    )
    """)

    conn.commit()
    conn.close()