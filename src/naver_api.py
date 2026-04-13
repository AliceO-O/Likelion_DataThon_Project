# 네이버 API 호출만 담당

import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

BASE_URL = "https://openapi.naver.com/v1/search"

HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET,
}

def fetch_naver_items(service: str, query: str, start: int = 1, display: int = 100) -> dict:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("네이버 API 키가 설정되지 않았습니다.")

    url = f"{BASE_URL}/{service}.json"
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": "date",
    }

    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()
    return response.json()