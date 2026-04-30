import sqlite3
import json

DB_PATH = "video_ids.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT video_id FROM videos")
rows = cursor.fetchall()

video_ids = [r[0] for r in rows]

with open("video_ids.json", "w") as f:
    json.dump(video_ids, f)

print("Exported", len(video_ids), "IDs")