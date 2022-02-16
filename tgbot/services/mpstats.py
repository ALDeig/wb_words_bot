import asyncio
from collections import namedtuple
from datetime import date, timedelta
import logging

import httpx

from .errors import ErrorBadRequestMPStats, ErrorAuthenticationMPStats
# from tgbot.services.errors import ErrorBadRequestMPStats, ErrorAuthenticationMPStats
from ..models.models import Proxy


HEADERS_JSON = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
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
        params={"d1": begin_date, "d2": end_date},
        timeout=60
    )
    return request.json()


def _request_info_by_scu(client: httpx.Client, scu: int, begin_date: str, end_date: str):
    request = client.get(
        url=f"https://mpstats.io/api/wb/get/item/{scu}/by_keywords",
        # headers=HEADERS_JSON,
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


def get_keywords_by_search_query(queries: str, token: str, proxy: Proxy) -> list | None:
    headers = HEADERS_JSON.copy()
    headers["X-Mpstats-TOKEN"] = token
    proxy = {"http://": f"http://{proxy.username}:{proxy.password}@{proxy.ip_address}:{proxy.port}"}
    suggest_queries = _get_list_queries(queries)
    with httpx.Client(headers=headers, proxies=proxy) as client:
        try:
            response = _request_keywords_by_search_queries_from_mpstats(client, ",".join(suggest_queries))
        except ErrorBadRequestMPStats:
            return
        return response


def get_info_by_scu(scu: int, token: str, proxy: Proxy) -> tuple | None:
    headers = HEADERS_JSON.copy()
    headers["X-Mpstats-TOKEN"] = token
    proxy = {"http://": f"http://{proxy.username}:{proxy.password}@{proxy.ip_address}:{proxy.port}"}
    with httpx.Client(headers=headers, proxies=proxy) as client:
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
