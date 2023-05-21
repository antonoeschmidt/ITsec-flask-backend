import sqlite3

DATABASE = 'database.db'

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

username = "hej"
cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
result = cursor.fetchone()
conn.close()

print(result)