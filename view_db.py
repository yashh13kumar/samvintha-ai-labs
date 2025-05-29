import sqlite3

conn = sqlite3.connect("finai.db")
c = conn.cursor()

print("---- Users ----")
for row in c.execute("SELECT * FROM user_profile"):
    print(row)

print("---- Chat History ----")
for row in c.execute("SELECT * FROM chat_history"):
    print(row)

conn.close()
