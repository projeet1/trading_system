# import sqlite3
# from common.config import DB_PATH

# conn = sqlite3.connect(DB_PATH)
# cursor = conn.cursor()
# cursor.execute("SELECT COUNT(*) FROM fills")
# print(cursor.fetchone())
# cursor.execute("SELECT * FROM fills LIMIT 5")
# print(cursor.fetchall())
# conn.close()

#!/usr/bin/env python3
"""Simple script to clear the trading simulation database."""

import os
from common.config import DB_PATH

def clear_database():
    """Delete the entire database file to start fresh."""
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"✅ Database cleared: {DB_PATH}")
            print("🚀 Ready for fresh simulation!")
        else:
            print("ℹ️  Database file doesn't exist - already clean!")
    except Exception as e:
        print(f"❌ Error clearing database: {e}")

if __name__ == "__main__":
    print(f"🗑️  Clearing simulation database: {DB_PATH}")
    clear_database()
