import sqlite3

DB_FILE = "finai.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ✅ Create user profile table
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        age_group TEXT,
        income_range TEXT,
        savings_style TEXT,
        marital_status TEXT,
        financial_style TEXT
    )
    """)

    # ✅ Create chat history table
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        sender TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user_profile(user_id, data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO user_profile 
    (user_id, name, age_group, income_range, savings_style, marital_status, financial_style)
    VALUES (?, ?, ?, ?, ?, ?, ?)""",
    (user_id, data.get("name"), data.get("age_group"), data.get("income_range"),
     data.get("savings_style"), data.get("marital_status"), data.get("financial_style")))
    conn.commit()
    conn.close()

def save_chat_message(user_id, sender, message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO chat_history (user_id, sender, message)
        VALUES (?, ?, ?)
    """, (user_id, sender, message))
    conn.commit()
    conn.close()

def get_chat_history(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT sender, message FROM chat_history WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]
