# 과거 날짜 구간 한 번에 수집(네이버 블로그&뉴스, 유튜브)

import os
import sys
from datetime import date, timedelta

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config import KEYWORDS, CSV_PATH
from src.orchestrator import collect_one_day
from src.save_csv import append_to_csv
from src.utils import daterange

def main():
    start_date = date.today() - timedelta(days=25)
    end_date = date.today() - timedelta(days=1)

    all_rows = []
    for target_date in daterange(start_date, end_date):
        rows = collect_one_day(target_date, KEYWORDS)
        all_rows.extend(rows)

    append_to_csv(all_rows, CSV_PATH)
    print("백필 완료")

if __name__ == "__main__":
    main()