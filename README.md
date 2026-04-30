# Youtube ID Search Project

Youtube video IDs are made of random 11 character sequences. That means that out of 1 million video IDs, the probability of a 3 or 4 letter word showing up is near 1. I've collected 1 million video IDs to test the results. This tool compares observed frequency vs theoretical probability.

## Features
- FastAPI backend
- Vue frontend
- 1M video ID dataset
- JSON-based runtime search
- Statistical comparison of observed vs expected frequency

## Data Pipeline
1. collect_ids.py -> gathers Youtube IDs using API 
2. exporter.py -> exports SQLite data to JSON
3. video_ids.json -> runtime dataset used by app

## Run locally
pip install -r requirements.txt
uvicorn main:app --reload