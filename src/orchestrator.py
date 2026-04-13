# 전체 플랫폼을 돌리는 총괄

from datetime import datetime

from src.collector_naver_blog_news import count_naver_by_date, count_naver_unique_by_date
from src.collector_youtube import count_youtube_by_date, count_youtube_unique_by_date


def collect_one_day(target_date, keywords):
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []

    # 1) 키워드별 집계
    for keyword in keywords:
        for platform in ["naver_blog", "naver_news", "youtube"]:
            try:
                if platform == "naver_blog":
                    count = count_naver_by_date("blog", keyword, target_date)
                elif platform == "naver_news":
                    count = count_naver_by_date("news", keyword, target_date)
                elif platform == "youtube":
                    count = count_youtube_by_date(keyword, target_date)

                rows.append({
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "platform": platform,
                    "keyword": keyword,
                    "count": count,
                    "collected_at": collected_at,
                    "status": "success",
                    "note": ""
                })

            except Exception as e:
                rows.append({
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "platform": platform,
                    "keyword": keyword,
                    "count": None,
                    "collected_at": collected_at,
                    "status": "fail",
                    "note": str(e)
                })

    # 2) 네이버 블로그 중복 제거 통합
    try:
        unique_blog_count = count_naver_unique_by_date("blog", keywords, target_date)

        rows.append({
            "target_date": target_date.strftime("%Y-%m-%d"),
            "platform": "naver_blog",
            "keyword": "combined_unique",
            "count": unique_blog_count,
            "collected_at": collected_at,
            "status": "success",
            "note": ""
        })

    except Exception as e:
        rows.append({
            "target_date": target_date.strftime("%Y-%m-%d"),
            "platform": "naver_blog",
            "keyword": "combined_unique",
            "count": None,
            "collected_at": collected_at,
            "status": "fail",
            "note": str(e)
        })

    # 3) 네이버 뉴스 중복 제거 통합
    try:
        unique_news_count = count_naver_unique_by_date("news", keywords, target_date)

        rows.append({
            "target_date": target_date.strftime("%Y-%m-%d"),
            "platform": "naver_news",
            "keyword": "combined_unique",
            "count": unique_news_count,
            "collected_at": collected_at,
            "status": "success",
            "note": ""
        })

    except Exception as e:
        rows.append({
            "target_date": target_date.strftime("%Y-%m-%d"),
            "platform": "naver_news",
            "keyword": "combined_unique",
            "count": None,
            "collected_at": collected_at,
            "status": "fail",
            "note": str(e)
        })

    # 4) 유튜브 중복 제거 통합
    try:
        unique_youtube_count = count_youtube_unique_by_date(keywords, target_date)

        rows.append({
            "target_date": target_date.strftime("%Y-%m-%d"),
            "platform": "youtube",
            "keyword": "combined_unique",
            "count": unique_youtube_count,
            "collected_at": collected_at,
            "status": "success",
            "note": ""
        })

    except Exception as e:
        rows.append({
            "target_date": target_date.strftime("%Y-%m-%d"),
            "platform": "youtube",
            "keyword": "combined_unique",
            "count": None,
            "collected_at": collected_at,
            "status": "fail",
            "note": str(e)
        })

    return rows