# 과거 날짜 구간 한 번에 수집(네이버 카페)

import os
import sys
from datetime import datetime, date, timedelta

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.collector_naver_cafe import scrape_naver_cafe_posts, aggregate_cafe_daily_counts


def main():
    start_date = date(2025, 12, 15)
    end_date = date.today() - timedelta(days=1)
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1) 키워드별 raw 수집
    kor_df = scrape_naver_cafe_posts("렉스트림", start_date, end_date, headless=False)
    eng_df = scrape_naver_cafe_posts("REXTREME", start_date, end_date, headless=False)

    raw_df = None
    if not kor_df.empty and not eng_df.empty:
        raw_df = pd.concat([kor_df, eng_df], ignore_index=True)
    elif not kor_df.empty:
        raw_df = kor_df.copy()
    elif not eng_df.empty:
        raw_df = eng_df.copy()
    else:
        raw_df = pd.DataFrame()

    # raw 저장
    raw_path = os.path.join(project_root, "data", "Crawling_data", "naver_cafe_raw_data.csv")
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    # 2) 날짜별 집계
    final_df = aggregate_cafe_daily_counts(
        raw_df=raw_df,
        start_date=start_date,
        end_date=end_date,
        collected_at=collected_at
    )

    final_path = os.path.join(project_root, "data", "Crawling_data", "naver_cafe_daily_counts.csv")
    final_df.to_csv(final_path, index=False, encoding="utf-8-sig")

    print("네이버 카페 raw 저장 완료:", raw_path)
    print("네이버 카페 일별 집계 저장 완료:", final_path)


if __name__ == "__main__":
    import pandas as pd
    main()