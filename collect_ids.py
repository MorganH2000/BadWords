import sqlite3
import requests
import time
import os

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY environmental variable")
DB_PATH = "video_ids.db"

TARGET_TOTAL = 1_000_000

BASE_URL = "https://www.googleapis.com/youtube/v3"

# -------------------------
# Database Setup
# -------------------------
def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY
        )
    """)

    conn.commit()
    return conn


def get_count(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos")
    return cursor.fetchone()[0]


def insert_ids(conn, ids):
    cursor = conn.cursor()
    for vid in ids:
        cursor.execute(
            "INSERT OR IGNORE INTO videos VALUES (?)",
            (vid,)
        )
    conn.commit()


# -------------------------
# API Calls
# -------------------------
SEARCH_TERMS = [
    "a", "e", "i", "o", "u", "the", "game", "music", "news",
    
    "halo", "call of duty", "minecraft", "pokemon", "zelda", "mario", "fortnite",
    
    "guitar", "piano", "cooking", "fitness", "makeup", "lego",
    
    "science", "history", "space", "cars", "travel", "food"]

def search_channels(page_token=None):
    import random

    params = {
        "part": "snippet",
        "type": "channel",
        "q": random.choice(SEARCH_TERMS),
        "maxResults": 50,
        "key": API_KEY
    }

    if page_token:
        params["pageToken"] = page_token

    r = requests.get(f"{BASE_URL}/search", params=params)
    data = r.json()

    print("Channels returned:", len(data.get("items", [])))  # debug

    return data



def get_uploads_playlist(channel_id):
    """
    Costs 1 quota unit.
    """
    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": API_KEY
    }

    r = requests.get(f"{BASE_URL}/channels", params=params)
    data = r.json()

    items = data.get("items", [])
    if not items:
        return None

    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_playlist_videos(playlist_id, page_token=None):
    """
    Costs 1 quota unit per page.
    Returns up to 50 videos.
    """
    params = {
        "part": "contentDetails",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": API_KEY
    }

    if page_token:
        params["pageToken"] = page_token

    r = requests.get(f"{BASE_URL}/playlistItems", params=params)
    return r.json()


# -------------------------
# Main Logic
# -------------------------
def main():
    conn = setup_db()

    total = get_count(conn)
    print(f"Currently stored: {total}")

    if total >= TARGET_TOTAL:
        print("Target already reached.")
        return

    next_channel_page = None

    # Limit search pages per run to stay safe under quota
    for _ in range(5):   # 5 search calls = 500 quota units
        channel_data = search_channels(next_channel_page)

        for item in channel_data.get("items", []):
            channel_id = item["id"]["channelId"]

            uploads_playlist = get_uploads_playlist(channel_id)
            if not uploads_playlist:
                continue

            next_video_page = None

            while True:
                if get_count(conn) >= TARGET_TOTAL:
                    print("Target reached!")
                    conn.close()
                    return

                video_data = get_playlist_videos(
                    uploads_playlist,
                    next_video_page
                )

                ids = [
                    v["contentDetails"]["videoId"]
                    for v in video_data.get("items", [])
                ]

                insert_ids(conn, ids)

                print("Total:", get_count(conn))

                next_video_page = video_data.get("nextPageToken")
                if not next_video_page:
                    break

                time.sleep(0.1)  # gentle rate limit

        next_channel_page = channel_data.get("nextPageToken")
        if not next_channel_page:
            break

        time.sleep(0.2)

    conn.close()
    print("Finished this run. Run again tomorrow if needed.")


if __name__ == "__main__":
    main()

