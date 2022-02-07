import asyncio
from collections import namedtuple
from datetime import date, timedelta
import logging

import httpx

from .errors import ErrorBadRequestMPStats, ErrorAuthenticationMPStats

HEADERS_AUTH = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,\
application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "ru-RU,ru;q=0.9",
    "content_lenght": "73",
    "content-type": "application/x-www-form-urlencoded",
    "dnt": "1",
    "origin": "https://mpstats.io",
    "pragma": "no-cache",
    "referer": "https://mpstats.io/login",
    # "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"
}

HEADERS_JSON = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "ru-RU,ru;q=0.9",
    "content-type": "application/json",
    "dnt": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0",
    # "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 \
    # Safari/537.36"
}
WORD_ROW = namedtuple("words", "word, count, total")
SALES_IN_DAY = namedtuple("sales", "day, balance, sales, price")


def _authorization(client: httpx.Client, login: str, password: str) -> bool:
    """Авторизация на сайте mpstats.io"""
    authorize = client.post(
        url="https://mpstats.io/login",
        data={"act": "login", "email": login, "password": password},
        timeout=60
    )
    if authorize.text:
        logging.error(f"Ошибка авторизации. Статус код авторизации - {authorize.status_code}")
        with open("auth.html", "w") as file:
            file.write(authorize.text)
        raise ErrorAuthenticationMPStats
    return True


def _request_keywords_by_search_queries_from_mpstats(client: httpx.Client, queries: str) -> dict | None:
    request = client.post(
        url="https://mpstats.io/api/seo/keywords/expanding",
        headers=HEADERS_JSON,
        json={"query": queries, "searchFullWord": False, "similar": False, "stopWords": [], "type": "keyword"},
        timeout=60
    )
    try:
        result = request.json()["result"]
        if not result:
            raise KeyError
    except (TypeError, KeyError):
        logging.error(f"Ошибка сбора данных из MPStats - {request.text}. Код ошибки - {request.status_code}")
        raise ErrorBadRequestMPStats
    return result


def _parse_categories(categories):
    result = ""
    for category in categories["categories"].keys():
        result += category.strip() + "\n\n"
    return result


def _request_categories_by_scu_from_mpstats(client: httpx.Client, scu: int, begin_date: str, end_date: str) -> dict:
    request = client.get(
        url=f"https://mpstats.io/api/wb/get/item/{scu}/by_category",
        headers=HEADERS_JSON,
        params={"d1": begin_date, "d2": end_date},
        timeout=60
    )
    return request.json()


def _request_info_by_scu(client: httpx.Client, scu: int, begin_date: str, end_date: str):
    request = client.get(
        url=f"https://mpstats.io/api/wb/get/item/{scu}/by_keywords",
        headers=HEADERS_JSON,
        params={"d1": begin_date, "d2": end_date},
        timeout=60
    )
    return request.json()


def _get_list_queries(queries: str):
    queries_list = list(filter(bool, queries.split("\n")))
    clear_queries = list(map(str.strip, queries_list))
    return clear_queries


def _parse_info_by_scu(product_info: dict) -> tuple[list[WORD_ROW], list[SALES_IN_DAY]]:
    words = []
    for word, info in product_info["words"].items():
        words.append(WORD_ROW(word=word, count=info["count"], total=info["total"]))
    sorted_words = sorted(words, key=lambda value: value.count, reverse=True)
    days = []
    for cnt in range(len(product_info["days"]) - 1, len(product_info["days"]) - 11, -1):
        days.append(SALES_IN_DAY(
            day=product_info["days"][cnt],
            balance=product_info["balance"][cnt],
            sales=product_info["sales"][cnt],
            price=product_info["final_price"][cnt]
        ))
    return sorted_words, days


async def get_keywords_by_search_query(queries: str, login, password) -> list | None:
    suggest_queries = _get_list_queries(queries)
    with httpx.Client(headers=HEADERS_AUTH, proxies="http://160.116.216.196:8000") as client:
        authorize = _authorization(client, login, password)
        if not authorize:
            return
        try:
            response = _request_keywords_by_search_queries_from_mpstats(client, ",".join(suggest_queries))
        except ErrorBadRequestMPStats:
            return
        return response


async def get_info_by_scu(scu: int, login, password) -> tuple | None:
    with httpx.Client(headers=HEADERS_AUTH, proxies="http://160.116.216.196:8000") as client:
        try:
            _authorization(client, login, password)
        except ErrorAuthenticationMPStats:
            return
        begin_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        raw_categories = _request_categories_by_scu_from_mpstats(client, scu, begin_date, end_date)
        try:
            categories = _parse_categories(raw_categories)
        except KeyError:
            return
        product_info = _request_info_by_scu(client, scu, begin_date, end_date)
        words, sales = _parse_info_by_scu(product_info)
        return categories, words, sales



# asyncio.run(get_info_by_scu(124231, "kolpackir@yandex.ru", "potok522222"))