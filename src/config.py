# 공통 설정

import os

KEYWORDS = ["렉스트림", "REXTREME"]

PLATFORMS = ["naver_blog", "naver_news", "youtube"]

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CSV_PATH = os.path.join(BASE_DIR, "data", "Crawling_data", "daily_counts.csv")

NAVER_DISPLAY_PER_PAGE = 100
NAVER_MAX_START = 1000

YOUTUBE_MAX_RESULTS = 50