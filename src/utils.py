# 날짜 범위 처리

from datetime import date, timedelta

def daterange(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)