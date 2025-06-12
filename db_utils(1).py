import sqlite3
import imaplib
import email
from email.header import decode_header

DB_FILE = "finai.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        age_group TEXT,
        income_range TEXT,
        savings_style TEXT,
        marital_status TEXT,
        financial_style TEXT,
        password TEXT
    )
    """)
    
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
    (user_id, name, age_group, income_range, savings_style, marital_status, financial_style, password)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    (user_id, data.get("name"), data.get("age_group"), data.get("income_range"),
     data.get("savings_style"), data.get("marital_status"), data.get("financial_style"),
     data.get("password")))
    conn.commit()
    conn.close()

def verify_password(user_id, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM user_profile WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == password

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

# --- Optional: Fetch Recent Emails (IMAP) ---
def fetch_recent_emails(email_user, app_password, n=5):
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(email_user, app_password)
        imap.select("inbox")

        status, messages = imap.search(None, "ALL")
        mail_ids = messages[0].split()[-n:]

        fetched = []
        for mail_id in reversed(mail_ids):
            _, msg_data = imap.fetch(mail_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    subject = subject.decode() if isinstance(subject, bytes) else subject
                    from_ = msg.get("From")
                    fetched.append(f"From: {from_}\nSubject: {subject}")
        imap.logout()
        return fetched
    except Exception as e:
        return [f"Failed to fetch emails: {str(e)}"]

# --- Placeholder: Fetch SMS (Android or Emulator) ---
def fetch_sms_data():
    # Placeholder for Android SMS access via Java/Kivy/ADB
    return [
        "SMS from Bank: ₹500 debited on 2 June.",
        "Promo SMS: 20% off on groceries at BigBazaar!"
    ]

# --- SECURITY NOTES ---
# ✅ Never store Gmail passwords directly
# ✅ Use App Passwords when using Gmail IMAP access
# ✅ For SMS access, ensure user consent and device permissions
