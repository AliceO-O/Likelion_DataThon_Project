# 실제 Selenium 수집 로직

import re
import time
from datetime import datetime, timedelta
from urllib.parse import quote

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


KST = pd.Timestamp.now(tz="Asia/Seoul").tz


def setup_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=ko-KR")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def build_cafe_search_url(keyword: str) -> str:
    encoded = quote(keyword)
    return (
        "https://search.naver.com/search.naver?"
        f"cafe_where=&prdtype=0&query={encoded}"
        "&sm=mtb_opt&ssc=tab.cafe.all&st=date&stnm=rel&opt_tab=0&nso=so%3Add%2Cp%3Aall"
    )


def normalize_cafe_url(url: str) -> str:
    if not url:
        return None
    return url.strip()


def contains_keyword(text: str, keyword: str) -> bool:
    if not text:
        return False
    return keyword.lower() in text.lower()


def parse_cafe_date_text(date_text: str, crawl_now_kst: pd.Timestamp):
    """
    날짜 문자열 예:
    - 2026.02.09.
    - 3분 전
    - 1시간 전
    - 23시간 전
    """
    if not date_text:
        return None

    date_text = date_text.strip()

    # 절대 날짜
    m_abs = re.search(r"(\d{4})\.(\d{2})\.(\d{2})\.", date_text)
    if m_abs:
        y, m, d = map(int, m_abs.groups())
        return pd.Timestamp(year=y, month=m, day=d, tz="Asia/Seoul").date()

    # 상대 날짜 - 분
    m_min = re.search(r"(\d+)\s*분 전", date_text)
    if m_min:
        minutes = int(m_min.group(1))
        return (crawl_now_kst - pd.Timedelta(minutes=minutes)).date()

    # 상대 날짜 - 시간
    m_hour = re.search(r"(\d+)\s*시간 전", date_text)
    if m_hour:
        hours = int(m_hour.group(1))
        return (crawl_now_kst - pd.Timedelta(hours=hours)).date()

    return None

def extract_cafe_post_key(url: str):
    """
    네이버 카페 게시글 URL에서 고유 게시글 키 추출
    예:
    https://cafe.naver.com/highendangyang/115?art=...&q=...
    -> highendangyang/115
    """
    if not url:
        return None

    m = re.search(r"https?://(?:m\.)?cafe\.naver\.com/([^/?#]+)/(\d+)", url)
    if m:
        cafe_name, article_id = m.groups()
        return f"{cafe_name}/{article_id}"

    return None

def extract_cards_from_html(html: str, query_keyword: str, crawl_now_kst: pd.Timestamp):
    """
    검색 결과 DOM은 바뀔 수 있어서,
    카드 단위 선택자를 여러 개 시도하고
    텍스트에서 날짜를 정규식으로 찾는 방식으로 간다.
    """
    soup = BeautifulSoup(html, "html.parser")

    candidate_blocks = []
    for selector in ["li.bx", "div.view_wrap", "div.total_wrap", "div.total_area"]:
        candidate_blocks.extend(soup.select(selector))

    rows = []
    seen_local = set()

    for block in candidate_blocks:
        full_text = block.get_text(" ", strip=True)
        full_text = re.sub(r"\s+", " ", full_text)
        full_text = re.sub(r"문서 저장하기", " ", full_text)
        full_text = re.sub(r"Keep에 저장", " ", full_text)
        full_text = re.sub(r"Keep 바로가기", " ", full_text)
        full_text = re.sub(r"\s+", " ", full_text).strip()

        # 날짜 텍스트 추출
        date_match = re.search(
            r"(\d{4}\.\d{2}\.\d{2}\.|(\d+\s*분 전)|(\d+\s*시간 전))",
            full_text
        )
        date_text = date_match.group(0) if date_match else None
        parsed_date = parse_cafe_date_text(date_text, crawl_now_kst)

        if parsed_date is None:
            continue

        # ---------------------------
        # 게시글 링크 후보 찾기
        # ---------------------------
        best_link = None
        best_title = None

        for a in block.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)

            # 문서 저장 / 빈 텍스트 제외
            if not text or text == "문서 저장":
                continue

            # 카페 관련 링크만 보되, 카페 메인 홈처럼 보이는 건 제외
            if "cafe.naver.com" not in href and "m.cafe.naver.com" not in href:
                continue

            # 카페 메인 루트 URL 제외
            # 예: https://cafe.naver.com/winsomecf
            if re.match(r"^https?://(m\.)?cafe\.naver\.com/[^/]+/?$", href):
                continue

            # 너무 짧은 텍스트 제외
            if len(text) < 4:
                continue

            best_link = href
            best_title = text
            break

        if best_link is None:
            continue

        url = normalize_cafe_url(best_link)
        post_key = extract_cafe_post_key(url)

        if not post_key or post_key in seen_local:
            continue

        has_kor = contains_keyword(full_text, "렉스트림")
        has_eng = contains_keyword(full_text, "rextreme")
        has_any = has_kor or has_eng

        rows.append({
            "query_keyword": query_keyword,
            "title": best_title,
            "full_text": full_text,
            "url": url,
            "post_key": post_key,
            "date_text": date_text,
            "parsed_date": str(parsed_date),
            "has_kor": has_kor,
            "has_eng": has_eng,
            "has_any": has_any,
        })
        seen_local.add(post_key )

    return rows

def scroll_until_date_range(driver, query_keyword: str, start_date: str, end_date: str, max_scrolls=200, sleep_sec=1.2):
    """
    무한 스크롤하면서 start_date 이전 결과가 충분히 보이면 중단.
    """
    start_date = pd.Timestamp(start_date).date()
    end_date = pd.Timestamp(end_date).date()

    collected = {}
    no_new_rounds = 0

    crawl_now_kst = pd.Timestamp.now(tz="Asia/Seoul")

    last_height = 0

    for _ in range(max_scrolls):
        html = driver.page_source
        rows = extract_cards_from_html(html, query_keyword, crawl_now_kst)

        before_len = len(collected)
        for row in rows:
            row_date = pd.Timestamp(row["parsed_date"]).date()
            if start_date <= row_date <= end_date:
                if row["post_key"]:
                    collected[row["post_key"]] = row

        after_len = len(collected)

        # 현재 페이지에서 가장 오래된 날짜 확인
        parsed_dates = []
        for row in rows:
            try:
                parsed_dates.append(pd.Timestamp(row["parsed_date"]).date())
            except Exception:
                pass

        oldest_date = min(parsed_dates) if parsed_dates else None

        # 새 데이터 없으면 카운트
        if after_len == before_len:
            no_new_rounds += 1
        else:
            no_new_rounds = 0

        # 종료 조건:
        # 1) 충분히 아래까지 내려가서 oldest_date가 start_date보다 이전
        # 2) 새 데이터도 더 이상 안 늘어남
        if oldest_date is not None and oldest_date < start_date and no_new_rounds >= 2:
            break

        # 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_sec)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_new_rounds += 1
        else:
            last_height = new_height

        if no_new_rounds >= 4:
            break

    return pd.DataFrame(collected.values())


def scrape_naver_cafe_posts(keyword: str, start_date: str, end_date: str, headless=False):
    driver = setup_driver(headless=headless)
    try:
        url = build_cafe_search_url(keyword)
        driver.get(url)
        time.sleep(2)

        raw_df = scroll_until_date_range(
            driver=driver,
            query_keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            max_scrolls=200,
            sleep_sec=1.2
        )

        if raw_df.empty:
            return raw_df

        # 기간 필터 최종 한 번 더
        raw_df["parsed_date"] = pd.to_datetime(raw_df["parsed_date"]).dt.date
        start_d = pd.Timestamp(start_date).date()
        end_d = pd.Timestamp(end_date).date()

        raw_df = raw_df[
            (raw_df["parsed_date"] >= start_d) &
            (raw_df["parsed_date"] <= end_d)
        ].copy()

        return raw_df

    finally:
        driver.quit()


def aggregate_cafe_daily_counts(raw_df: pd.DataFrame, start_date: str, end_date: str, collected_at: str):
    """
    raw_df 컬럼:
    query_keyword, title, full_text, url, post_key, date_text, parsed_date, has_kor, has_eng, has_any
    """
    if raw_df.empty:
        all_dates = pd.date_range(start_date, end_date, freq="D").strftime("%Y-%m-%d")
        keyword_order = ["렉스트림", "REXTREME", "combined_unique"]

        full_grid = pd.MultiIndex.from_product(
            [all_dates, keyword_order],
            names=["target_date", "keyword"]
        ).to_frame(index=False)

        full_grid["platform"] = "naver_cafe"
        full_grid["count"] = 0
        full_grid["collected_at"] = collected_at
        full_grid["status"] = "success"
        full_grid["note"] = ""

        return full_grid[
            ["target_date", "platform", "keyword", "count", "collected_at", "status", "note"]
        ]

    raw_df = raw_df.copy()
    raw_df["target_date"] = pd.to_datetime(raw_df["parsed_date"]).dt.strftime("%Y-%m-%d")

    # 키워드별
    kor_counts = (
        raw_df[raw_df["has_kor"]]
        .groupby("target_date")["post_key"]
        .nunique()
        .reset_index(name="count")
    )
    kor_counts["platform"] = "naver_cafe"
    kor_counts["keyword"] = "렉스트림"

    eng_counts = (
        raw_df[raw_df["has_eng"]]
        .groupby("target_date")["post_key"]
        .nunique()
        .reset_index(name="count")
    )
    eng_counts["platform"] = "naver_cafe"
    eng_counts["keyword"] = "REXTREME"

    combined_counts = (
        raw_df[raw_df["has_any"]]
        .groupby("target_date")["post_key"]
        .nunique()
        .reset_index(name="count")
    )
    combined_counts["platform"] = "naver_cafe"
    combined_counts["keyword"] = "combined_unique"

    final_df = pd.concat([kor_counts, eng_counts, combined_counts], ignore_index=True)

    # 전체 날짜 0 채우기
    all_dates = pd.date_range(start_date, end_date, freq="D").strftime("%Y-%m-%d")
    keyword_order = ["렉스트림", "REXTREME", "combined_unique"]

    full_grid = pd.MultiIndex.from_product(
        [all_dates, keyword_order],
        names=["target_date", "keyword"]
    ).to_frame(index=False)

    full_grid["platform"] = "naver_cafe"
    full_grid["collected_at"] = collected_at
    full_grid["status"] = "success"
    full_grid["note"] = ""

    final_df = full_grid.merge(
        final_df[["target_date", "platform", "keyword", "count"]],
        on=["target_date", "platform", "keyword"],
        how="left"
    )

    final_df["count"] = final_df["count"].fillna(0).astype(int)

    final_df["keyword"] = pd.Categorical(
        final_df["keyword"],
        categories=["렉스트림", "REXTREME", "combined_unique"],
        ordered=True
    )

    final_df = final_df[
        ["target_date", "platform", "keyword", "count", "collected_at", "status", "note"]
    ].sort_values(["target_date", "platform", "keyword"]).reset_index(drop=True)

    return final_df