import json

with open("video_ids.json", "r") as f:
    VIDEO_IDS = json.load(f)   # keep original case

TOTAL = len(VIDEO_IDS)


def search_bad_words(query, page=1, limit=50):
    query = query.lower()

    matches = [vid for vid in VIDEO_IDS if query in vid.lower()]

    match_count = len(matches)

    offset = (page - 1) * limit
    results = matches[offset:offset + limit]

    return results, TOTAL, match_count