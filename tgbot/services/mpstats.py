import asyncio
import json
from collections import namedtuple
from dataclasses import dataclass
from datetime import date, timedelta
import logging
from pathlib import Path

import httpx
from pydantic import BaseModel, ValidationError

from .errors import ErrorBadRequestMPStats, ErrorAuthenticationMPStats
# from tgbot.services.errors import ErrorBadRequestMPStats, ErrorAuthenticationMPStats
from ..models.models import Proxy
# from tgbot.models.models import Proxy


HEADERS_JSON = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
}
WordRow = namedtuple("WordRow", "word, word_forms, count, total")
RequestRow = namedtuple("RequestRow", "request, count")
SALES_IN_DAY = namedtuple("sales", "day, balance, sales, price")


@dataclass
class ScuInfo:
    name: str = None
    price: int = None
    amount_sales: int = None
    total_sales: int = None


class Sales(BaseModel):
    price: int
    discount: int
    final_price: int
    sales: int


# def _request_keywords_by_search_queries_from_mpstats(client: httpx.Client, queries: str) -> dict | None:
#     request = client.post(
#         url="https://mpstats.io/api/seo/keywords/expanding",
#         json={"query": queries, "searchFullWord": False, "similar": False, "stopWords": [], "type": "keyword"},
#         timeout=60
#     )
#     try:
#         result = request.json()["result"]
#         if not result:
#             raise KeyError
#     except (TypeError, KeyError):
#         logging.error(f"Ошибка сбора данных из MPStats - {request.text}. Код ошибки - {request.status_code}")
#         raise ErrorBadRequestMPStats
#     return result


# def _parse_categories(categories):
#     result = ""
#     for category in categories["categories"].keys():
#         result += category.strip() + "\n\n"
#     return result


# async def _request_categories_by_scu_from_mpstats(client: httpx.AsyncClient, scu: int, begin_date: str, end_date: str) -> dict:
#     request = await client.get(
#         url=f"https://mpstats.io/api/wb/get/item/{scu}/by_category",
#         params={"d1": begin_date, "d2": end_date},
#         timeout=60
#     )
#     return request.json()





# def _get_list_queries(queries: str):
#     queries_list = list(filter(bool, queries.split("\n")))
#     clear_queries = list(map(str.strip, queries_list))
#     return clear_queries




# def get_keywords_by_search_query(queries: str, token: str, proxy: Proxy) -> list | None:
#     headers = HEADERS_JSON.copy()
#     headers["X-Mpstats-TOKEN"] = token
#     proxy = {"http://": f"http://{proxy.username}:{proxy.password}@{proxy.ip_address}:{proxy.port}"}
#     suggest_queries = _get_list_queries(queries)
#     with httpx.Client(headers=headers, proxies=proxy) as client:
#         try:
#             response = _request_keywords_by_search_queries_from_mpstats(client, ",".join(suggest_queries))
#         except ErrorBadRequestMPStats:
#             return
#         return response


class InfoByQuery:
    def __init__(self, query: str, token: str, proxy: Proxy = None):
        self.result: list[WordRow] | None = None
        self._query = ",".join(query.split("\n"))
        self._token = token
        self._begin_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        self._end_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self._proxy = {"http://": f"http://{proxy.username}:{proxy.password}@{proxy.ip_address}:{proxy.port}"} \
            if proxy else None

    async def start_process(self):
        headers = HEADERS_JSON.copy()
        headers["X-Mpstats-TOKEN"] = self._token
        async with httpx.AsyncClient(headers=headers, proxies=self._proxy, timeout=60) as client:
            by_query = await self._get_words(client, "keyword")
            by_word = await self._get_words(client, "word")
            words = by_query if len(by_query) > len(by_word) else by_word
            self.result = self._parse_words(words)

    async def _get_words(self, client: httpx.AsyncClient, type_request: str) -> list:
        response = await client.post(
            url="https://mpstats.io/api/seo/keywords/expanding",
            json={
                "d1": self._begin_date,
                "d2": self._end_date,
                "mp": 0,
                "query": self._query,
                "searchFullWord": "false",
                "similar": "false",
                "stopWords": [],
                "type": type_request
            }
        )
        return response.json()["result"]

    @staticmethod
    def _parse_words(data) -> list[WordRow]:
        words = []
        for row in data:
            words.append(WordRow(word=row["word"], word_forms=", ".join(row["words"]), count=row["count"],
                                 total=row["keys_count_sum"]))
        sorted_words = sorted(words, key=lambda value: value.total, reverse=True)
        return sorted_words


class InfoByScu:
    def __init__(self, scu: int, token: str, proxy: Proxy = None):
        self.image: Path
        self.categories: str
        self.words: list[WordRow]
        self.requests: list[RequestRow]
        self.scu_info = ScuInfo()
        self._scu = scu
        self._token = token
        self._proxy = {"http://": f"http://{proxy.username}:{proxy.password}@{proxy.ip_address}:{proxy.port}"} \
            if proxy else None
        self._begin_date_for_30_days = (date.today() - timedelta(days=31)).strftime("%Y-%m-%d")
        self._begin_date_for_60_days = (date.today() - timedelta(days=61)).strftime("%Y-%m-%d")
        self._end_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")

    async def get_info_by_scu(self):
        headers = HEADERS_JSON.copy()
        headers["X-Mpstats-TOKEN"] = self._token
        async with httpx.AsyncClient(headers=headers, proxies=self._proxy) as client:
            await self._get_sales_info_by_scu(client)
            await self._download_image(client)
            await self._get_categories(client)
            await self._request_info_for_files_by_scu(client)

    async def _download_image(self, client):
        response = await client.get(
            url=f"https://img1.wbstatic.net/c246x328/new/{self._scu // 10000 * 10000}/{self._scu}-1.jpg"
        )
        self.image = Path() / f"{self._scu}.jpg"
        self.image.write_bytes(response.content)

    async def _get_categories(self, client: httpx.AsyncClient):
        response = await client.get(
            url=f"https://mpstats.io/api/wb/get/item/{self._scu}/by_category",
            params={"d1": self._begin_date_for_30_days, "d2": self._end_date}
        )
        categories = response.json()["categories"].keys()
        self.categories = "\n".join(categories)

    async def _get_sales_info_by_scu(self, client: httpx.AsyncClient):
        raw_sales_data = await client.get(
            url=f"https://mpstats.io/api/wb/get/item/{self._scu}/sales",
            params={"d1": self._begin_date_for_60_days, "d2": self._end_date}
        )
        try:
            sales = [Sales.parse_obj(day) for day in raw_sales_data.json()]
        except (json.JSONDecodeError, ValidationError):
            raise ErrorBadRequestMPStats
        self.scu_info.price, self.scu_info.amount_sales, self.scu_info.total_sales = \
            self._parse_sales_info_by_scu(sales)

    @staticmethod
    def _parse_sales_info_by_scu(sales: list[Sales]) -> tuple[int, int, int]:
        amount_sales = 0
        sum_price_sales = 0
        for day in sales:
            amount_sales += day.sales
            sum_price_sales += day.final_price * day.sales
        return sales[0].final_price, amount_sales, sum_price_sales

    async def _request_info_for_files_by_scu(self, client: httpx.AsyncClient):
        request = await client.post(
            url="https://mpstats.io/api/seo/keywords/expanding",
            json={"d1": self._begin_date_for_30_days, "d2": self._end_date, "mp": 0, "query": self._scu,
                  "searchFullWord": "false", "similar": "false", "stopWords": "[]", "type": "sku"},
            timeout=60
        )
        self.scu_info.name, self.words, self.requests = self._parse_info_for_files_by_scu(request.json())

    @staticmethod
    def _parse_info_for_files_by_scu(product_info: dict) -> tuple[str, list[WordRow], list[RequestRow]]:
        words = []
        for row in product_info["result"]:
            words.append(WordRow(word=row["word"], word_forms=", ".join(row["words"]), count=row["count"],
                                 total=row["keys_count_sum"]))
        sorted_words = sorted(words, key=lambda value: value.total, reverse=True)
        requests = []
        for request in product_info["words"]:
            requests.append(RequestRow(
                request=request["word"],
                count=request["count"]
            ))
        return product_info["path"][0]["name"], sorted_words, requests


