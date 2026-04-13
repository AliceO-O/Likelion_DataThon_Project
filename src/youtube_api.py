# 유튜브 API 호출만 담당

import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3/search"

def fetch_youtube_items(query: str, published_after: str, published_before: str, page_token: str = None, max_results: int = 50):
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다.")

    params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "publishedAfter": published_after,
        "publishedBefore": published_before,
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }

    if page_token:
        params["pageToken"] = page_token

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()