# 네이버 날짜별 카운트 로직

from datetime import datetime
from email.utils import parsedate_to_datetime

from src.config import NAVER_DISPLAY_PER_PAGE, NAVER_MAX_START
from src.naver_api import fetch_naver_items


def parse_blog_date(item):
    value = item.get("postdate")
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except Exception:
        return None


def parse_news_date(item):
    value = item.get("pubDate")
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).date()
    except Exception:
        return None


def get_naver_item_date(service_name: str, item):
    if service_name == "blog":
        return parse_blog_date(item)
    elif service_name == "news":
        return parse_news_date(item)
    return None


def contains_keyword(text: str, keyword: str) -> bool:
    if not text:
        return False
    return keyword.lower() in text.lower()


def is_valid_naver_match(item: dict, keyword: str) -> bool:
    """
    제목(title) 또는 설명(description)에 keyword가 실제 포함되는지 확인
    """
    title = item.get("title", "")
    description = item.get("description", "")

    return contains_keyword(title, keyword) or contains_keyword(description, keyword)


def get_naver_unique_key(service_name: str, item: dict):
    """
    네이버 뉴스/블로그 결과에서 dedupe용 고유 키 추출
    - news: originallink 우선, 없으면 link
    - blog: link
    """
    if service_name == "news":
        return item.get("originallink") or item.get("link")
    elif service_name == "blog":
        return item.get("link")
    return None


def count_naver_by_date(service_name: str, keyword: str, target_date):
    """
    특정 키워드 기준 날짜별 count
    """
    total_count = 0

    for start in range(1, NAVER_MAX_START + 1, NAVER_DISPLAY_PER_PAGE):
        data = fetch_naver_items(service_name, keyword, start=start, display=NAVER_DISPLAY_PER_PAGE)
        items = data.get("items", [])

        if not items:
            break

        stop_search = False

        for item in items:
            item_date = get_naver_item_date(service_name, item)

            if item_date is None:
                continue

            if item_date == target_date:
                if is_valid_naver_match(item, keyword):
                    total_count += 1

            elif item_date < target_date:
                stop_search = True
                break

        if stop_search:
            break

    return total_count


def count_naver_unique_by_date(service_name: str, keywords: list[str], target_date):
    """
    여러 키워드 결과를 합친 뒤, URL 기준으로 중복 제거하여 고유 URL 수를 센다.
    - blog: link 기준
    - news: originallink 우선, 없으면 link 기준
    """
    unique_keys = set()

    for keyword in keywords:
        for start in range(1, NAVER_MAX_START + 1, NAVER_DISPLAY_PER_PAGE):
            data = fetch_naver_items(service_name, keyword, start=start, display=NAVER_DISPLAY_PER_PAGE)
            items = data.get("items", [])

            if not items:
                break

            stop_search = False

            for item in items:
                item_date = get_naver_item_date(service_name, item)

                if item_date is None:
                    continue

                if item_date == target_date:
                    if is_valid_naver_match(item, keyword):
                        unique_key = get_naver_unique_key(service_name, item)
                        if unique_key:
                            unique_keys.add(unique_key)

                elif item_date < target_date:
                    stop_search = True
                    break

            if stop_search:
                break

    return len(unique_keys)