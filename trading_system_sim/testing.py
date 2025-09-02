import sqlite3
from common.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM fills")
print(cursor.fetchone())
cursor.execute("SELECT * FROM fills LIMIT 5")
print(cursor.fetchall())
conn.close()
