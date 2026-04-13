# 유튜브 날짜별 카운트 로직

from datetime import datetime, time, timedelta, timezone

from src.config import YOUTUBE_MAX_RESULTS
from src.youtube_api import fetch_youtube_items

KST = timezone(timedelta(hours=9))


def make_utc_range_for_kst_day(target_date):
    start_kst = datetime.combine(target_date, time.min, tzinfo=KST)
    end_kst = datetime.combine(target_date + timedelta(days=1), time.min, tzinfo=KST)

    return (
        start_kst.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        end_kst.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def contains_keyword(text: str, keyword: str) -> bool:
    """
    대소문자 무시하고 keyword가 text에 포함되는지 검사
    """
    if not text:
        return False
    return keyword.lower() in text.lower()


def is_valid_youtube_match(item: dict, keyword: str) -> bool:
    """
    유튜브 검색 결과 item 중에서
    제목(title) 또는 설명(description)에 keyword가 실제 포함되는지 검사
    """
    snippet = item.get("snippet", {})
    title = snippet.get("title", "")
    description = snippet.get("description", "")

    return contains_keyword(title, keyword) or contains_keyword(description, keyword)


def count_youtube_by_date(keyword: str, target_date):
    """
    특정 날짜(target_date)에 업로드된 유튜브 영상 중
    제목/설명에 keyword가 실제 포함된 영상 수를 센다.
    """
    published_after, published_before = make_utc_range_for_kst_day(target_date)

    total_count = 0
    page_token = None

    while True:
        data = fetch_youtube_items(
            query=keyword,
            published_after=published_after,
            published_before=published_before,
            page_token=page_token,
            max_results=YOUTUBE_MAX_RESULTS
        )

        items = data.get("items", [])

        for item in items:
            if is_valid_youtube_match(item, keyword):
                total_count += 1

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return total_count


def count_youtube_unique_by_date(keywords: list[str], target_date):
    """
    여러 키워드 결과를 합친 뒤 videoId 기준으로 중복 제거하여 실제 고유 영상 수를 센다.
    """
    published_after, published_before = make_utc_range_for_kst_day(target_date)

    unique_video_ids = set()

    for keyword in keywords:
        page_token = None

        while True:
            data = fetch_youtube_items(
                query=keyword,
                published_after=published_after,
                published_before=published_before,
                page_token=page_token,
                max_results=YOUTUBE_MAX_RESULTS
            )

            items = data.get("items", [])

            for item in items:
                if is_valid_youtube_match(item, keyword):
                    video_id = item.get("id", {}).get("videoId")
                    if video_id:
                        unique_video_ids.add(video_id)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return len(unique_video_ids)